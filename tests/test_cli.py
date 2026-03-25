import unittest
import sqlite3
import runpy
from datetime import datetime
from unittest.mock import patch, MagicMock

from pyfc.cli import main


class TestMain(unittest.TestCase):
    @patch("pyfc.cli.display_todays_matches")
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

            main()

        mock_sync.assert_called_once()
        mock_display.assert_called_once()
        called_data = mock_display.call_args[0][0]
        self.assertIn("matches", called_data)
        self.assertEqual(len(called_data["matches"]), 1)
        self.assertEqual(called_data["matches"][0]["home_team"], "Arsenal")

        conn.close()

    @patch("pyfc.cli.display_todays_matches")
    @patch("pyfc.cli.init_or_sync_cache")
    @patch("pyfc.cli.get_pyfc_cache_path", return_value=":memory:")
    @patch("pyfc.cli.get_football_data_api_key", return_value=None)
    def test_main_module_entry_point(
        self, mock_key, mock_cache, mock_sync, mock_display
    ):
        with patch("pyfc.cli.sys.exit") as mock_exit:
            runpy.run_module("pyfc.cli", run_name="__main__", alter_sys=False)
            mock_exit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
