import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pyfc.config import (
    get_pyfc_config_path,
    get_pyfc_cache_path,
    read_kv_file,
    write_kv_file,
    get_football_data_api_key,
)


class TestGetPyfcConfigPath(unittest.TestCase):
    @patch("pyfc.config.Path.mkdir")
    @patch.dict("os.environ", {"XDG_CONFIG_HOME": "/tmp/test_xdg_config"}, clear=False)
    def test_uses_xdg_config_home_when_set(self, mock_mkdir):
        result = get_pyfc_config_path()
        self.assertEqual(result, Path("/tmp/test_xdg_config/pyfc/credentials.env"))

    @patch("pyfc.config.Path.mkdir")
    @patch.dict("os.environ", {"XDG_CONFIG_HOME": ""}, clear=False)
    def test_falls_back_to_home_when_xdg_empty(self, mock_mkdir):
        result = get_pyfc_config_path()
        self.assertEqual(result, Path.home() / ".config" / "pyfc" / "credentials.env")

    @patch("pyfc.config.Path.mkdir")
    @patch.dict("os.environ", {"XDG_CONFIG_HOME": "   "}, clear=False)
    def test_falls_back_to_home_when_xdg_whitespace(self, mock_mkdir):
        result = get_pyfc_config_path()
        self.assertEqual(result, Path.home() / ".config" / "pyfc" / "credentials.env")

    @patch("pyfc.config.Path.mkdir")
    @patch.dict("os.environ", {}, clear=False)
    def test_falls_back_to_home_when_xdg_unset(self, mock_mkdir):
        import os
        os.environ.pop("XDG_CONFIG_HOME", None)
        result = get_pyfc_config_path()
        self.assertEqual(result, Path.home() / ".config" / "pyfc" / "credentials.env")


class TestGetPyfcCachePath(unittest.TestCase):
    @patch("pyfc.config.Path.mkdir")
    @patch.dict("os.environ", {"XDG_CACHE_HOME": "/tmp/test_xdg_cache"}, clear=False)
    def test_uses_xdg_cache_home_when_set(self, mock_mkdir):
        result = get_pyfc_cache_path()
        self.assertEqual(result, Path("/tmp/test_xdg_cache/pyfc/cache.db"))

    @patch("pyfc.config.Path.mkdir")
    @patch.dict("os.environ", {"XDG_CACHE_HOME": ""}, clear=False)
    def test_falls_back_to_home_when_xdg_empty(self, mock_mkdir):
        result = get_pyfc_cache_path()
        self.assertEqual(result, Path.home() / ".cache" / "pyfc" / "cache.db")

    @patch("pyfc.config.Path.mkdir")
    @patch.dict("os.environ", {"XDG_CACHE_HOME": "   "}, clear=False)
    def test_falls_back_to_home_when_xdg_whitespace(self, mock_mkdir):
        result = get_pyfc_cache_path()
        self.assertEqual(result, Path.home() / ".cache" / "pyfc" / "cache.db")

    @patch("pyfc.config.Path.mkdir")
    @patch.dict("os.environ", {}, clear=False)
    def test_falls_back_to_home_when_xdg_unset(self, mock_mkdir):
        import os
        os.environ.pop("XDG_CACHE_HOME", None)
        result = get_pyfc_cache_path()
        self.assertEqual(result, Path.home() / ".cache" / "pyfc" / "cache.db")


class TestReadKvFile(unittest.TestCase):
    def test_returns_empty_dict_when_file_missing(self):
        result = read_kv_file(Path("/nonexistent/file.env"))
        self.assertEqual(result, {})

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.read_text", return_value="KEY1=value1\nKEY2=value2\n")
    def test_parses_key_value_pairs(self, mock_read, mock_exists):
        result = read_kv_file(Path("/fake/file.env"))
        self.assertEqual(result, {"KEY1": "value1", "KEY2": "value2"})

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.read_text", return_value="# comment\n\nKEY=val\n")
    def test_skips_comments_and_empty_lines(self, mock_read, mock_exists):
        result = read_kv_file(Path("/fake/file.env"))
        self.assertEqual(result, {"KEY": "val"})

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.read_text", return_value="INVALID_LINE\n")
    def test_raises_on_missing_equals(self, mock_read, mock_exists):
        with self.assertRaises(ValueError):
            read_kv_file(Path("/fake/file.env"))

    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.read_text", return_value="KEY=val=ue\n")
    def test_handles_value_with_equals(self, mock_read, mock_exists):
        result = read_kv_file(Path("/fake/file.env"))
        self.assertEqual(result, {"KEY": "val=ue"})


class TestWriteKvFile(unittest.TestCase):
    @patch("pathlib.Path.write_text")
    def test_writes_key_value_pairs(self, mock_write):
        write_kv_file(Path("/fake/file.env"), {"A": "1", "B": "2"})
        mock_write.assert_called_once_with("A=1\nB=2\n", encoding="utf-8")


class TestGetFootballDataApiKey(unittest.TestCase):
    @patch("pyfc.config.write_kv_file")
    @patch("pyfc.config.read_kv_file", return_value={"FOOTBALL_DATA_API_KEY": "existing-key"})
    @patch("pyfc.config.get_pyfc_config_path", return_value=Path("/fake/credentials.env"))
    def test_returns_existing_key(self, mock_path, mock_read, mock_write):
        result = get_football_data_api_key()
        self.assertEqual(result, "existing-key")
        mock_write.assert_not_called()

    @patch("pyfc.config.write_kv_file")
    @patch("pyfc.config.read_kv_file", return_value={})
    @patch("pyfc.config.get_pyfc_config_path", return_value=Path("/fake/credentials.env"))
    @patch("pyfc.config.getpass.getpass", return_value="new-key")
    def test_prompts_and_stores_new_key(self, mock_getpass, mock_path, mock_read, mock_write):
        result = get_football_data_api_key()
        self.assertEqual(result, "new-key")
        mock_write.assert_called_once_with(
            Path("/fake/credentials.env"), {"FOOTBALL_DATA_API_KEY": "new-key"}
        )


if __name__ == "__main__":
    unittest.main()
