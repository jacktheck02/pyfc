import json
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError
import contextlib
from io import StringIO


from pyfc.api import get_matches


class TestGetMatches(unittest.TestCase):
    @patch("pyfc.api.urllib.request.urlopen")
    def test_successful_request_returns_matches_data(self, mock_urlopen):
        expected = {"matches": [{"id": 1}]}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(expected).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = get_matches("test-key", datetime(2026, 3, 20), datetime(2026, 3, 22))

        self.assertEqual(result, expected)
        call_args = mock_urlopen.call_args[0][0]
        self.assertIn("dateFrom=2026-03-20", call_args.full_url)
        self.assertIn("dateTo=2026-03-22", call_args.full_url)
        self.assertEqual(call_args.get_header("X-auth-token"), "test-key")

    @patch("pyfc.api.urllib.request.urlopen")
    def test_http_error_prints(self, mock_urlopen):
        error = HTTPError(
            url="http://example.com",
            code=403,
            msg="Forbidden",
            hdrs=MagicMock(),
            fp=MagicMock(read=MagicMock(return_value=b"forbidden")),
        )
        error.read = MagicMock(return_value=b"forbidden")
        mock_urlopen.side_effect = error
        out = StringIO()

        with self.assertRaises(SystemExit):
            with contextlib.redirect_stdout(out):
                get_matches("bad-key", datetime(2026, 3, 20), datetime(2026, 3, 22))
        
        
        self.assertIn('HTTP 403: forbidden\n', out.getvalue())

    @patch("pyfc.api.urllib.request.urlopen")
    def test_url_error_prints(self, mock_urlopen):
        error = URLError(
            reason="Invalid URL"
        )
        mock_urlopen.side_effect = error
        out = StringIO()

        with self.assertRaises(SystemExit):
            with contextlib.redirect_stdout(out):
                get_matches("key", datetime(2026, 3, 20), datetime(2026, 3, 22))
        
        
        self.assertIn('URL Error: Invalid URL\n', out.getvalue())


if __name__ == "__main__":
    unittest.main()
