from io import StringIO
import unittest
from datetime import datetime, timezone
import contextlib
import pyfc.display

DATE_FROM = datetime(2026, 3, 20, tzinfo=timezone.utc)
DATE_TO = datetime(2026, 3, 21, tzinfo=timezone.utc)


class TestOrdinal(unittest.TestCase):
    def test_first(self):
        self.assertEqual(pyfc.display._ordinal(1), "1st")

    def test_second(self):
        self.assertEqual(pyfc.display._ordinal(2), "2nd")

    def test_third(self):
        self.assertEqual(pyfc.display._ordinal(3), "3rd")

    def test_fourth(self):
        self.assertEqual(pyfc.display._ordinal(4), "4th")

    def test_eleventh(self):
        self.assertEqual(pyfc.display._ordinal(11), "11th")

    def test_twelfth(self):
        self.assertEqual(pyfc.display._ordinal(12), "12th")

    def test_thirteenth(self):
        self.assertEqual(pyfc.display._ordinal(13), "13th")

    def test_twenty_first(self):
        self.assertEqual(pyfc.display._ordinal(21), "21st")

    def test_twenty_second(self):
        self.assertEqual(pyfc.display._ordinal(22), "22nd")

    def test_twenty_third(self):
        self.assertEqual(pyfc.display._ordinal(23), "23rd")

    def test_thirty_first(self):
        self.assertEqual(pyfc.display._ordinal(31), "31st")

    def test_one_hundred_eleventh(self):
        self.assertEqual(pyfc.display._ordinal(111), "111th")

    def test_one_hundred_twelfth(self):
        self.assertEqual(pyfc.display._ordinal(112), "112th")


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
            pyfc.display.display_matches_in_range(
                {"matches": "bad"}, DATE_FROM, DATE_TO
            )

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

    def test_displays_matches_across_multiple_dates(self):
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
                    "competition": "La Liga",
                    "area": "Spain",
                    "home_team": "Barcelona",
                    "away_team": "Real Madrid",
                    "utc_date": "2026-03-21T20:00:00Z",
                },
            ]
        }
        date_from = datetime(2026, 3, 20, tzinfo=timezone.utc)
        date_to = datetime(2026, 3, 22, tzinfo=timezone.utc)

        out = StringIO()
        with contextlib.redirect_stdout(out):
            pyfc.display.display_matches_in_range(matches_data, date_from, date_to)

        output = out.getvalue()
        self.assertIn("Arsenal vs Chelsea", output)
        self.assertIn("Barcelona vs Real Madrid", output)
        # Should have two separate date headers
        self.assertEqual(output.count("Matches on"), 2)


if __name__ == "__main__":
    unittest.main()
