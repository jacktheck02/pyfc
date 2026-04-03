from io import StringIO
import unittest
from datetime import datetime, timezone
import contextlib
import pyfc.display

DATE_FROM = datetime(2026, 3, 20, tzinfo=timezone.utc)
DATE_TO = datetime(2026, 3, 21, tzinfo=timezone.utc)


class TestUtcToLocalTime(unittest.TestCase):
    def test_returns_aware_datetime(self):
        result = pyfc.display._utc_to_local_time("2026-03-20T14:00:00Z")

        self.assertIsInstance(result, datetime)
        self.assertIsNotNone(result.tzinfo)

    def test_correct_utc_value(self):
        result = pyfc.display._utc_to_local_time("2026-03-20T14:00:00Z")
        expected_utc = datetime(2026, 3, 20, 14, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(result, expected_utc.astimezone())


class TestDisplayTodaysMatches(unittest.TestCase):
    def test_empty_matches_list(self):
        out = StringIO()
        with contextlib.redirect_stdout(out):
            pyfc.display.display_matches_in_range({"matches": []}, DATE_FROM, DATE_TO)

        self.assertIn("No matches from", out.getvalue())

    def test_no_matches_key(self):
        out = StringIO()
        with contextlib.redirect_stdout(out):
            pyfc.display.display_matches_in_range({}, DATE_FROM, DATE_TO)

        self.assertIn("No matches from", out.getvalue())

    def test_matches_key_not_a_list(self):
        out = StringIO()
        with contextlib.redirect_stdout(out):
            pyfc.display.display_matches_in_range({"matches": "bad"}, DATE_FROM, DATE_TO)

        self.assertIn("No matches from", out.getvalue())

    def test_displays_matches_grouped_by_league(self):
        matches_data = {
            "matches": [
                {
                    "competition": "Premier League",
                    "area": "England",
                    "home_team": "Arsenal",
                    "away_team": "Chelsea",
                    "utc_date": "2026-03-20T15:00:00Z",
                },
                {
                    "competition": "Premier League",
                    "area": "England",
                    "home_team": "Liverpool",
                    "away_team": "Man City",
                    "utc_date": "2026-03-20T17:30:00Z",
                },
                {
                    "competition": "La Liga",
                    "area": "Spain",
                    "home_team": "Barcelona",
                    "away_team": "Real Madrid",
                    "utc_date": "2026-03-20T20:00:00Z",
                },
            ]
        }
        out = StringIO()
        with contextlib.redirect_stdout(out):
            pyfc.display.display_matches_in_range(matches_data, DATE_FROM, DATE_TO)

        output = out.getvalue()
        self.assertIn("Matches on", output)
        self.assertIn("Premier League", output)
        self.assertIn("England", output)
        self.assertIn("Arsenal vs Chelsea", output)
        self.assertIn("Liverpool vs Man City", output)
        self.assertIn("La Liga", output)
        self.assertIn("Spain", output)
        self.assertIn("Barcelona vs Real Madrid", output)


if __name__ == "__main__":
    unittest.main()
