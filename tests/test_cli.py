import unittest
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from pyfc.cli import main, _assign_date_arguments, _adapt_api_matches_data, parser


class TestAssignDateArguments(unittest.TestCase):
    def setUp(self):
        self.todays_date = datetime(2026, 4, 3)

    def test_invalid_date_from_format(self):
        args = parser.parse_args(["--date-from", "not-a-date"])
        with self.assertRaises(SystemExit):
            _assign_date_arguments(args, self.todays_date)

    def test_invalid_date_to_format(self):
        args = parser.parse_args(["--date-to", "2026-13-45"])
        with self.assertRaises(SystemExit):
            _assign_date_arguments(args, self.todays_date)

    def test_date_from_after_date_to(self):
        args = parser.parse_args(
            ["--date-from", "2026-04-10", "--date-to", "2026-04-01"]
        )
        with self.assertRaises(SystemExit):
            _assign_date_arguments(args, self.todays_date)

    def test_defaults_to_today(self):
        args = parser.parse_args([])
        date_from, date_to = _assign_date_arguments(args, self.todays_date)
        self.assertEqual(date_from, self.todays_date)
        self.assertEqual(date_to, self.todays_date + timedelta(hours=24))

    def test_valid_custom_dates(self):
        args = parser.parse_args(
            ["--date-from", "2026-04-01", "--date-to", "2026-04-05"]
        )
        date_from, date_to = _assign_date_arguments(args, self.todays_date)
        self.assertEqual(date_from, datetime(2026, 4, 1))
        self.assertEqual(date_to, datetime(2026, 4, 5))


class TestAdaptApiMatchesData(unittest.TestCase):
    def test_adapts_single_match(self):
        api_data = {
            "matches": [
                {
                    "utcDate": "2026-04-03T15:00:00Z",
                    "homeTeam": {"name": "Arsenal"},
                    "awayTeam": {"name": "Chelsea"},
                    "competition": {"name": "Premier League"},
                    "area": {"name": "England"},
                }
            ]
        }
        result = _adapt_api_matches_data(api_data)
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["matches"][0]["home_team"], "Arsenal")
        self.assertEqual(result["matches"][0]["away_team"], "Chelsea")
        self.assertEqual(result["matches"][0]["competition"], "Premier League")
        self.assertEqual(result["matches"][0]["area"], "England")
        self.assertEqual(result["matches"][0]["utc_date"], "2026-04-03T15:00:00Z")

    def test_adapts_empty_matches(self):
        result = _adapt_api_matches_data({"matches": []})
        self.assertEqual(result, {"matches": []})


class TestMainApiFetchBranch(unittest.TestCase):
    @patch("pyfc.cli.display_matches_in_range")
    @patch("pyfc.cli.get_matches")
    @patch("pyfc.cli.init_or_sync_cache")
    @patch("pyfc.cli.get_pyfc_cache_path", return_value=":memory:")
    @patch("pyfc.cli.get_football_data_api_key", return_value="test-key")
    def test_api_branch_when_dates_far_from_today(
        self, mock_key, mock_cache_path, mock_sync, mock_get_matches, mock_display
    ):
        mock_get_matches.return_value = {
            "matches": [
                {
                    "utcDate": "2026-05-01T18:00:00Z",
                    "homeTeam": {"name": "Liverpool"},
                    "awayTeam": {"name": "Man City"},
                    "competition": {"name": "Premier League"},
                    "area": {"name": "England"},
                }
            ]
        }

        main(["--date-from", "2026-05-01", "--date-to", "2026-05-10"])

        mock_get_matches.assert_called_once()
        mock_display.assert_called_once()
        called_data = mock_display.call_args[0][0]
        self.assertEqual(called_data["matches"][0]["home_team"], "Liverpool")


class TestMain(unittest.TestCase):
    @patch("pyfc.cli.display_matches_in_range")
    @patch("pyfc.cli.init_or_sync_cache")
    @patch("pyfc.cli.get_pyfc_cache_path")
    @patch("pyfc.cli.get_football_data_api_key", return_value="test-key")
    def test_full_flow(self, mock_key, mock_cache_path, mock_sync, mock_display):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript("""
            CREATE TABLE areas (area_id INTEGER PRIMARY KEY, name TEXT NOT NULL, code TEXT);
            CREATE TABLE competitions (competition_id INTEGER PRIMARY KEY, area_id INTEGER, name TEXT NOT NULL, code TEXT, type TEXT);
            CREATE TABLE seasons (season_id INTEGER PRIMARY KEY, competition_id INTEGER, start_date DATE, end_date DATE, current_matchday INTEGER, winner TEXT);
            CREATE TABLE teams (team_id INTEGER PRIMARY KEY, name TEXT NOT NULL, short_name TEXT, tla TEXT);
            CREATE TABLE matches (match_id INTEGER PRIMARY KEY, area_id INTEGER, competition_id INTEGER, season_id INTEGER, home_team_id INTEGER, away_team_id INTEGER, utc_date TIMESTAMP NOT NULL, status TEXT, matchday INTEGER, stage TEXT, group_name TEXT, last_updated TIMESTAMP);
            CREATE TABLE scores (match_id INTEGER PRIMARY KEY, winner TEXT, duration TEXT, full_time_home INTEGER, full_time_away INTEGER, half_time_home INTEGER, half_time_away INTEGER);
        """)
        conn.execute("INSERT INTO areas VALUES (1, 'England', 'ENG')")
        conn.execute(
            "INSERT INTO competitions VALUES (10, 1, 'Premier League', 'PL', 'LEAGUE')"
        )
        conn.execute("INSERT INTO teams VALUES (50, 'Arsenal', 'Arsenal', 'ARS')")
        conn.execute("INSERT INTO teams VALUES (51, 'Chelsea', 'Chelsea', 'CHE')")
        conn.execute(
            "INSERT INTO seasons VALUES (200, 10, '2025-08-01', '2026-05-31', 30, NULL)"
        )
        today_str = datetime.now().strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO matches VALUES (100, 1, 10, 200, 50, 51, ?, 'SCHEDULED', 30, 'REGULAR_SEASON', NULL, NULL)",
            (f"{today_str}T15:00:00Z",),
        )
        conn.commit()

        mock_cache_path.return_value = ":memory:"

        with patch("pyfc.cli.sqlite3.connect") as mock_connect:
            mock_connect.return_value.__enter__ = MagicMock(return_value=conn)
            mock_connect.return_value.__exit__ = MagicMock(return_value=False)

            main([])

        mock_sync.assert_called_once()
        mock_display.assert_called_once()
        called_data = mock_display.call_args[0][0]
        self.assertIn("matches", called_data)
        self.assertEqual(len(called_data["matches"]), 1)
        self.assertEqual(called_data["matches"][0]["home_team"], "Arsenal")

        conn.close()


if __name__ == "__main__":
    unittest.main()
