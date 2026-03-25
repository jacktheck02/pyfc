import unittest
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch

from pyfc.cache import insert_matches_into_cache, init_or_sync_cache
from pyfc.schemas import CREATE_MATCHES_TABLES
from conftest import SAMPLE_MATCH


def _create_tables(conn):
    """Helper to create cache tables using init_or_sync_cache's schema."""
    conn.executescript(CREATE_MATCHES_TABLES)
    conn.commit()


class TestInsertMatchesIntoCache(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        _create_tables(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_insert_single_match(self):
        matches_data = {"matches": [SAMPLE_MATCH]}
        today = datetime(2026, 3, 20)

        insert_matches_into_cache(self.conn, matches_data, today)

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM areas WHERE area_id = 1")
        self.assertIsNotNone(cursor.fetchone())

        cursor.execute("SELECT * FROM competitions WHERE competition_id = 10")
        self.assertIsNotNone(cursor.fetchone())

        cursor.execute("SELECT * FROM seasons WHERE season_id = 200")
        self.assertIsNotNone(cursor.fetchone())

        cursor.execute("SELECT * FROM teams")
        self.assertEqual(len(cursor.fetchall()), 2)

        cursor.execute("SELECT * FROM matches WHERE match_id = 100")
        self.assertIsNotNone(cursor.fetchone())

        cursor.execute("SELECT * FROM scores WHERE match_id = 100")
        self.assertIsNotNone(cursor.fetchone())

        cursor.execute("SELECT * FROM referees WHERE referee_id = 300")
        self.assertIsNotNone(cursor.fetchone())

        cursor.execute("SELECT * FROM match_referees WHERE match_id = 100 AND referee_id = 300")
        self.assertIsNotNone(cursor.fetchone())

        cursor.execute("SELECT value FROM cache_meta WHERE key = 'last_full_sync'")
        row = cursor.fetchone()
        self.assertEqual(row[0], "2026-03-20")

    def test_insert_empty_matches(self):
        matches_data = {"matches": []}
        today = datetime(2026, 3, 20)

        insert_matches_into_cache(self.conn, matches_data, today)

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM matches")
        self.assertEqual(len(cursor.fetchall()), 0)

    def test_insert_match_without_referees(self):
        match = {**SAMPLE_MATCH, "referees": []}
        matches_data = {"matches": [match]}
        today = datetime(2026, 3, 20)

        insert_matches_into_cache(self.conn, matches_data, today)

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM referees")
        self.assertEqual(len(cursor.fetchall()), 0)

    def test_insert_match_missing_referees_key(self):
        match = dict(SAMPLE_MATCH)
        del match["referees"]
        matches_data = {"matches": [match]}
        today = datetime(2026, 3, 20)

        insert_matches_into_cache(self.conn, matches_data, today)

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM matches WHERE match_id = 100")
        self.assertIsNotNone(cursor.fetchone())


class TestInitOrSyncCache(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        self.conn.close()

    @patch("pyfc.cache.get_matches")
    def test_first_sync_no_previous_data(self, mock_get_matches):
        """No last_full_sync => time_delta is huge => full purge + sync."""
        mock_get_matches.return_value = {"matches": [SAMPLE_MATCH]}
        today = datetime(2026, 3, 20)

        init_or_sync_cache(self.conn, today, "api-key")

        mock_get_matches.assert_called_once()
        args = mock_get_matches.call_args
        self.assertEqual(args.args[0], "api-key")
        # date_from = today - 5 days, date_to = today + 5 days
        self.assertEqual(args.kwargs.get("date_from") or args.args[1], today - timedelta(days=5))
        self.assertEqual(args.kwargs.get("date_to") or args.args[2], today + timedelta(days=5))

    @patch("pyfc.cache.get_matches")
    def test_sync_within_ten_days(self, mock_get_matches):
        """Last sync 2 days ago => incremental sync (no full purge)."""
        mock_get_matches.return_value = {"matches": []}
        today = datetime(2026, 3, 20)
        last_sync = today - timedelta(days=2)

        # First init the cache
        init_or_sync_cache(self.conn, today, "api-key")
        mock_get_matches.reset_mock()

        # Set last_full_sync to 2 days ago
        self.conn.execute(
            "INSERT OR REPLACE INTO cache_meta (key, value, updated_at) VALUES ('last_full_sync', ?, ?)",
            (last_sync.strftime("%Y-%m-%d"), datetime.now().isoformat()),
        )
        self.conn.commit()

        mock_get_matches.return_value = {"matches": []}

        init_or_sync_cache(self.conn, today, "api-key")

        mock_get_matches.assert_called_once()
        args = mock_get_matches.call_args
        self.assertEqual(
            args.kwargs.get("date_from") or args.args[1],
            today - timedelta(days=5),
        )

    @patch("pyfc.cache.get_matches")
    def test_sync_skipped_when_recent(self, mock_get_matches):
        """Last sync is today => no API call."""
        mock_get_matches.return_value = {"matches": []}
        today = datetime(2026, 3, 20)

        # First init
        init_or_sync_cache(self.conn, today, "api-key")
        mock_get_matches.reset_mock()

        # Set last_full_sync to today
        self.conn.execute(
            "INSERT OR REPLACE INTO cache_meta (key, value, updated_at) VALUES ('last_full_sync', ?, ?)",
            (today.strftime("%Y-%m-%d"), datetime.now().isoformat()),
        )
        self.conn.commit()

        init_or_sync_cache(self.conn, today, "api-key")

        mock_get_matches.assert_not_called()

    @patch("pyfc.cache.get_matches")
    def test_full_purge_when_over_ten_days(self, mock_get_matches):
        """Last sync 11 days ago => full purge path."""
        mock_get_matches.return_value = {"matches": [SAMPLE_MATCH]}
        today = datetime(2026, 3, 20)

        # First init
        init_or_sync_cache(self.conn, today, "api-key")
        mock_get_matches.reset_mock()

        last_sync = today - timedelta(days=11)
        self.conn.execute(
            "INSERT OR REPLACE INTO cache_meta (key, value, updated_at) VALUES ('last_full_sync', ?, ?)",
            (last_sync.strftime("%Y-%m-%d"), datetime.now().isoformat()),
        )
        self.conn.commit()

        mock_get_matches.return_value = {"matches": [SAMPLE_MATCH]}
        init_or_sync_cache(self.conn, today, "api-key")

        mock_get_matches.assert_called_once()
        args = mock_get_matches.call_args
        self.assertEqual(
            args.kwargs.get("date_from") or args.args[1],
            today - timedelta(days=5),
        )


if __name__ == "__main__":
    unittest.main()
