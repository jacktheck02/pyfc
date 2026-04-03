from datetime import datetime, timezone


def _utc_to_local_time(utc_time: str) -> datetime:
    dt_utc = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    return dt_utc.astimezone()


def _ordinal(n: int) -> str:
    if 11 <= n % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def display_todays_matches(matches_data: dict, date_from: datetime, date_to: datetime):
    dates: dict = {}
    league_areas: dict = {}

    if "matches" in matches_data and isinstance(matches_data["matches"], list):
        for match in matches_data["matches"]:
            competition_name = match["competition"]
            area = match["area"]
            league_areas[competition_name] = area
            local_time = _utc_to_local_time(match["utc_date"])
            date_key = local_time.date()
            dates.setdefault(date_key, {}).setdefault(competition_name, []).append(
                match
            )

    if len(dates) == 0:
        print(
            f"No matches from {date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')}!"
        )
        return

    for date_key, leagues in dates.items():
        day_name = date_key.strftime("%A")
        month_name = date_key.strftime("%B")
        day_ord = _ordinal(date_key.day)
        print(f"⚽ Matches on {day_name} {month_name} {day_ord}, {date_key.year} ⚽")
        print("================================================")

        for league_name, matches in leagues.items():
            print(f"🏆 {league_name} [{league_areas[league_name]}]")
            print("------------------------------------------------")
            for match in matches:
                home_team = match["home_team"]
                away_team = match["away_team"]
                local_time = _utc_to_local_time(match["utc_date"])
                print(f"[{local_time.strftime('%I:%M %p')}] {home_team} vs {away_team}")
            print()
        print()
