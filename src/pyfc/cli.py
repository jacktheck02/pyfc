from datetime import datetime, timedelta
import sys
import sqlite3
import argparse

from pyfc.cache import init_or_sync_cache
from pyfc.config import get_football_data_api_key, get_pyfc_cache_path
from pyfc.display import display_todays_matches
from pyfc.api import get_matches

parser = argparse.ArgumentParser(prog="pyfc", description="", epilog="")
parser.add_argument("--date-from", type=str, required=False)
parser.add_argument("--date-to", type=str, required=False)


def assign_date_arguments(
    args: argparse.Namespace, todays_date: datetime
) -> tuple[datetime, datetime]:
    if args.date_from is not None:
        try:
            date_from = datetime.strptime(args.date_from, "%Y-%m-%d")
        except ValueError:
            parser.error(f"{args.date_from} does not match format 'yyyy-MM-dd'")
    else:
        date_from = todays_date

    if args.date_to is not None:
        try:
            date_to = datetime.strptime(args.date_to, "%Y-%m-%d")
        except ValueError:
            parser.error(f"{args.date_to} does not match format 'yyyy-MM-dd'")
    else:
        date_to = todays_date + timedelta(hours=24)

    if date_from > date_to:
        parser.error("--date-from must be before --date-to")

    return date_from, date_to


def adapt_api_matches_data(api_matches_data: dict) -> dict:
    adapted_matches_data = {"matches": []}
    for match in api_matches_data["matches"]:
        adapted_matches_data["matches"].append(
            {
                "utc_date": match["utcDate"],
                "home_team": match["homeTeam"]["name"],
                "away_team": match["awayTeam"]["name"],
                "competition": match["competition"]["name"],
                "area": match["area"]["name"],
            }
        )

    return adapted_matches_data


def main():
    args = parser.parse_args()

    football_data_api_key = get_football_data_api_key()
    todays_date = datetime.now()

    date_from, date_to = assign_date_arguments(args, todays_date)

    pyfc_cache_path = get_pyfc_cache_path()
    with sqlite3.connect(pyfc_cache_path) as connection:
        connection.row_factory = sqlite3.Row

        init_or_sync_cache(
            connection=connection,
            todays_date=todays_date,
            football_data_api_key=football_data_api_key,
        )

        cursor = connection.cursor()
        if date_from < todays_date - timedelta(
            days=5
        ) or date_to > todays_date + timedelta(days=5):
            matches_data = get_matches(
                football_data_api_key=football_data_api_key,
                date_from=date_from,
                date_to=date_to,
            )

            matches_data = adapt_api_matches_data(matches_data)

            display_todays_matches(matches_data, date_from, date_to)
        else:
            get_matches_query = """
                SELECT m.utc_date, t1.name AS home_team, t2.name AS away_team, c.name AS competition, a.name AS area
                FROM matches m
                JOIN teams t1 ON m.home_team_id = t1.team_id
                JOIN teams t2 ON m.away_team_id = t2.team_id
                JOIN competitions c ON m.competition_id = c.competition_id
                JOIN areas a ON m.area_id = a.area_id
                WHERE m.utc_date >= ? AND m.utc_date < ?
                ORDER BY m.utc_date ASC
            """

            cursor.execute(get_matches_query, (date_from, date_to))
            today_matches_rows = cursor.fetchall()

            matches_data = {"matches": [dict(row) for row in today_matches_rows]}

            display_todays_matches(matches_data, date_from, date_to)


if __name__ == "__main__":
    sys.exit(main())
