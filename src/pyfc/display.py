from datetime import datetime, timezone


def utc_to_local_time(utc_time: str) -> datetime:
    dt_utc = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    return dt_utc.astimezone()


def display_todays_matches(matches_data: dict):
    leagues = {}
    league_areas = {}

    if "matches" in matches_data and isinstance(matches_data["matches"], list):
        for match in matches_data["matches"]:
            competition_name = match["competition"]
            area = match["area"]
            league_areas[competition_name] = area
            leagues.setdefault(competition_name, []).append(match)

    if len(leagues) == 0:
        print("No matches today!")
        return

    print("⚽ Today's Matches ⚽")
    print("=================================\n")

    for league_name, matches in leagues.items():
        print(f"🏆 {league_name} [{league_areas[league_name]}]")
        print("-----------------------")
        for match in matches:
            home_team = match["home_team"]
            away_team = match["away_team"]
            utc_time = match["utc_date"]

            local_time = utc_to_local_time(utc_time)

            print(f"[{local_time.strftime('%X')}] {home_team} vs {away_team}")
        print()
