from pathlib import Path
import locale
import getpass
import os

locale.setlocale(locale.LC_TIME, "")

FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/"


def get_pyfc_config_path() -> Path:
    xdg_config_path = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_path is None or len(xdg_config_path.strip()) == 0:
        base_path = Path.home() / ".config"
    else:
        base_path = Path(xdg_config_path).expanduser()

    config_path = base_path / "pyfc"
    config_path.mkdir(parents=True, exist_ok=True)

    config_path = config_path / "credentials.env"

    return config_path


def get_pyfc_cache_path() -> Path:
    xdg_cache_path = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache_path is None or len(xdg_cache_path.strip()) == 0:
        base_path = Path.home() / ".cache"
    else:
        base_path = Path(xdg_cache_path).expanduser()

    cache_path = base_path / "pyfc"
    cache_path.mkdir(parents=True, exist_ok=True)

    cache_file = cache_path / "cache.db"

    return cache_file


def read_kv_file(path: Path) -> dict:
    data: dict[str, str] = {}
    if not path.exists():
        return data

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def write_kv_file(path: Path, data: dict):
    lines = [f"{k}={v}" for k, v in data.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_football_data_api_key() -> str:
    config_path = get_pyfc_config_path()

    environment_variables = read_kv_file(config_path)

    if "FOOTBALL_DATA_API_KEY" not in environment_variables:
        api_key = getpass.getpass("Football-data.org API key: ")
        environment_variables["FOOTBALL_DATA_API_KEY"] = api_key
        write_kv_file(config_path, environment_variables)
    else:
        api_key = environment_variables["FOOTBALL_DATA_API_KEY"]

    return api_key
