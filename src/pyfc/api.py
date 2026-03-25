import json
from urllib.error import HTTPError, URLError
import urllib.request
from datetime import datetime
import pyfc.config


class ApiHttpError(Exception):
    def __init__(self, code: int, body: str):
        self.code = code
        self.body = body
        super().__init__(f"HTTP {code}: {body}")


class ApiUrlError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"URL Error: {reason}")


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
        raise ApiHttpError(e.code, e.read().decode("utf-8")) from e
    except URLError as e:
        raise ApiUrlError(str(e.reason)) from e

    return matches_data
