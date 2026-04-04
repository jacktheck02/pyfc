import json
from urllib.error import HTTPError, URLError
import urllib.request
from datetime import datetime
import pyfc.config
import sys


def get_matches(
    football_data_api_key: str, date_from: datetime, date_to: datetime
) -> dict:
    req = urllib.request.Request(
        url=pyfc.config.FOOTBALL_DATA_BASE_URL
        + f"v4/matches?dateFrom={date_from.strftime('%Y-%m-%d')}&dateTo={date_to.strftime('%Y-%m-%d')}",
        headers={"X-Auth-Token": football_data_api_key},
    )

    try:
        with urllib.request.urlopen(req) as resp:
            matches_data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"HTTP {e.code}: {error_body}")
        sys.exit(1)
    except URLError as e:
        print(f"URL Error: {e.reason}")
        sys.exit(1)

    return matches_data
