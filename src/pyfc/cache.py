from datetime import datetime, timedelta
import sqlite3

from pyfc.api import get_matches
from pyfc.schemas import CREATE_MATCHES_TABLES


def insert_matches_into_cache(
    connection: sqlite3.Connection, matches_data: dict, todays_date: datetime
):
    cursor = connection.cursor()
    for match in matches_data.get("matches", []):
        # insert area
        area = match["area"]
        cursor.execute(
            "INSERT OR REPLACE INTO areas (area_id, name, code) VALUES (?, ?, ?)",
            (area["id"], area["name"], area.get("code")),
        )

        # insert competition
        competition = match["competition"]
        cursor.execute(
            "INSERT OR REPLACE INTO competitions (competition_id, area_id, name, code, type) VALUES (?, ?, ?, ?, ?)",
            (
                competition["id"],
                area["id"],
                competition["name"],
                competition.get("code"),
                competition.get("type"),
            ),
        )

        # insert season
        season = match["season"]
        cursor.execute(
            "INSERT OR REPLACE INTO seasons (season_id, competition_id, start_date, end_date, current_matchday, winner) VALUES (?, ?, ?, ?, ?, ?)",
            (
                season["id"],
                competition["id"],
                season["startDate"],
                season["endDate"],
                season.get("currentMatchday"),
                season.get("winner"),
            ),
        )

        # insert teams
        home_team = match["homeTeam"]
        away_team = match["awayTeam"]

        cursor.execute(
            "INSERT OR REPLACE INTO teams (team_id, name, short_name, tla) VALUES (?, ?, ?, ?)",
            (
                home_team["id"],
                home_team["name"],
                home_team.get("shortName"),
                home_team.get("tla"),
            ),
        )

        cursor.execute(
            "INSERT OR REPLACE INTO teams (team_id, name, short_name, tla) VALUES (?, ?, ?, ?)",
            (
                away_team["id"],
                away_team["name"],
                away_team.get("shortName"),
                away_team.get("tla"),
            ),
        )

        # insert match
        cursor.execute(
            "INSERT OR REPLACE INTO matches (match_id, area_id, competition_id, season_id, home_team_id, away_team_id, utc_date, status, matchday, stage, group_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                match["id"],
                area["id"],
                competition["id"],
                season["id"],
                home_team["id"],
                away_team["id"],
                match["utcDate"],
                match.get("status"),
                match.get("matchday"),
                match.get("stage"),
                match.get("group"),
            ),
        )

        # insert scores
        score = match["score"]
        cursor.execute(
            "INSERT OR REPLACE INTO scores (match_id, winner, duration, full_time_home, full_time_away, half_time_home, half_time_away) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                match["id"],
                score.get("winner"),
                score.get("duration"),
                score["fullTime"].get("home"),
                score["fullTime"].get("away"),
                score["halfTime"].get("home"),
                score["halfTime"].get("away"),
            ),
        )

        # insert referees
        for referee in match.get("referees", []):
            cursor.execute(
                "INSERT OR REPLACE INTO referees (referee_id, name, type, nationality) VALUES (?, ?, ?, ?)",
                (
                    referee["id"],
                    referee["name"],
                    referee.get("type"),
                    referee.get("nationality"),
                ),
            )
            cursor.execute(
                "INSERT OR REPLACE INTO match_referees (match_id, referee_id) VALUES (?, ?)",
                (match["id"], referee["id"]),
            )

    cursor.execute(
        "INSERT OR REPLACE INTO cache_meta (key, value, updated_at) VALUES ('last_full_sync', ?, ?)",
        (todays_date.strftime("%Y-%m-%d"), todays_date.isoformat()),
    )

    connection.commit()


def init_or_sync_cache(
    connection: sqlite3.Connection, todays_date: datetime, football_data_api_key: str
):
    cursor = connection.cursor()

    cursor.executescript(CREATE_MATCHES_TABLES)

    connection.execute("PRAGMA foreign_keys = ON")

    connection.commit()

    last_sync_date_query = "SELECT value FROM cache_meta WHERE key = 'last_full_sync'"
    cursor.execute(last_sync_date_query)
    last_sync_row = cursor.fetchone()

    if last_sync_row is None:
        last_sync_date = datetime.min
    else:
        last_sync_date = datetime.strptime(last_sync_row[0], "%Y-%m-%d")
    time_delta = todays_date - last_sync_date

    if time_delta >= timedelta(hours=24):
        if time_delta >= timedelta(days=10):
            cursor.execute("DELETE FROM match_referees;")
            cursor.execute("DELETE FROM scores;")
            cursor.execute("DELETE FROM matches;")
            cursor.execute("DELETE FROM teams;")
            cursor.execute("DELETE FROM seasons;")
            cursor.execute("DELETE FROM competitions;")
            cursor.execute("DELETE FROM areas;")
            cursor.execute("DELETE FROM referees;")

            matches_data = get_matches(
                football_data_api_key,
                date_from=todays_date - timedelta(days=5),
                date_to=todays_date + timedelta(days=5),
            )

            insert_matches_into_cache(connection, matches_data, todays_date)
        else:
            cutoff_date = (todays_date - timedelta(days=5)).strftime("%Y-%m-%d")
            cursor.execute(
                "DELETE FROM scores WHERE match_id IN (SELECT match_id FROM matches WHERE utc_date < ?);",
                (cutoff_date,),
            )
            cursor.execute(
                "DELETE FROM match_referees WHERE match_id IN (SELECT match_id FROM matches WHERE utc_date < ?);",
                (cutoff_date,),
            )
            cursor.execute("DELETE FROM matches WHERE utc_date < ?;", (cutoff_date,))
            cursor.execute(
                "DELETE FROM teams WHERE team_id NOT IN (SELECT home_team_id FROM matches) AND team_id NOT IN (SELECT away_team_id FROM matches)"
            )
            cursor.execute(
                "DELETE FROM seasons WHERE season_id NOT IN (SELECT season_id FROM matches)"
            )
            cursor.execute(
                "DELETE FROM competitions WHERE competition_id NOT IN (SELECT competition_id FROM matches)"
            )
            cursor.execute(
                "DELETE FROM areas WHERE area_id NOT IN (SELECT area_id FROM matches)"
            )
            cursor.execute(
                "DELETE FROM referees WHERE referee_id NOT IN (SELECT referee_id FROM match_referees);"
            )

            matches_data = get_matches(
                football_data_api_key,
                date_from=todays_date - timedelta(days=5),
                date_to=todays_date + timedelta(days=5),
            )

            insert_matches_into_cache(connection, matches_data, todays_date)
