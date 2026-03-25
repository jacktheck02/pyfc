from datetime import datetime
import sys
import sqlite3

from pyfc.cache import init_or_sync_cache
from pyfc.config import get_football_data_api_key, get_pyfc_cache_path
from pyfc.display import display_todays_matches


def main():
    football_data_api_key = get_football_data_api_key()
    todays_date = datetime.now()

    pyfc_cache_path = get_pyfc_cache_path()
    with sqlite3.connect(pyfc_cache_path) as connection:
        connection.row_factory = sqlite3.Row

        init_or_sync_cache(
            connection=connection,
            todays_date=todays_date,
            football_data_api_key=football_data_api_key,
        )

        cursor = connection.cursor()
        get_matches_query = """
            SELECT m.utc_date, t1.name AS home_team, t2.name AS away_team, c.name AS competition, a.name AS area
            FROM matches m
            JOIN teams t1 ON m.home_team_id = t1.team_id
            JOIN teams t2 ON m.away_team_id = t2.team_id
            JOIN competitions c ON m.competition_id = c.competition_id
            JOIN areas a ON m.area_id = a.area_id
            WHERE m.utc_date LIKE ? || '%'
            ORDER BY m.utc_date ASC
        """

        cursor.execute(get_matches_query, (todays_date.strftime("%Y-%m-%d"),))
        today_matches_rows = cursor.fetchall()

    matches_data = {"matches": [dict(row) for row in today_matches_rows]}

    display_todays_matches(matches_data)


if __name__ == "__main__":
    sys.exit(main())
