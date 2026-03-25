CREATE_MATCHES_TABLES = """
    CREATE TABLE IF NOT EXISTS cache_meta(
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT
    );      

    CREATE TABLE IF NOT EXISTS areas (
        area_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        code TEXT
    );

    CREATE TABLE IF NOT EXISTS competitions (
        competition_id INTEGER PRIMARY KEY,
        area_id INTEGER,
        name TEXT NOT NULL,
        code TEXT,
        type TEXT,
        FOREIGN KEY (area_id) REFERENCES areas(area_id)
    );

    CREATE TABLE IF NOT EXISTS seasons (
        season_id INTEGER PRIMARY KEY,
        competition_id INTEGER,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        current_matchday INTEGER,
        winner TEXT,
        FOREIGN KEY (competition_id) REFERENCES competitions(competition_id)
    );

    CREATE TABLE IF NOT EXISTS teams (
        team_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        short_name TEXT,
        tla TEXT
    );

    CREATE TABLE IF NOT EXISTS matches (
        match_id INTEGER PRIMARY KEY,
        area_id INTEGER,
        competition_id INTEGER,
        season_id INTEGER,
        home_team_id INTEGER,
        away_team_id INTEGER,
        utc_date TIMESTAMP NOT NULL,
        status TEXT,
        matchday INTEGER,
        stage TEXT,
        group_name TEXT,
        last_updated TIMESTAMP,
        FOREIGN KEY (area_id) REFERENCES areas(area_id),
        FOREIGN KEY (competition_id) REFERENCES competitions(competition_id),
        FOREIGN KEY (season_id) REFERENCES seasons(season_id),
        FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
        FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
    );

    CREATE TABLE IF NOT EXISTS scores (
        match_id INTEGER PRIMARY KEY,
        winner TEXT,
        duration TEXT,
        full_time_home INTEGER,
        full_time_away INTEGER,
        half_time_home INTEGER,
        half_time_away INTEGER,
        FOREIGN KEY (match_id) REFERENCES matches(match_id)
    );

    CREATE TABLE IF NOT EXISTS referees (
        referee_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT,
        nationality TEXT
    );

    CREATE TABLE IF NOT EXISTS match_referees (
        match_id INTEGER,
        referee_id INTEGER,
        PRIMARY KEY (match_id, referee_id),
        FOREIGN KEY (match_id) REFERENCES matches(match_id),
        FOREIGN KEY (referee_id) REFERENCES referees(referee_id)
    );
                        
    CREATE INDEX IF NOT EXISTS idx_matches_utc_date ON matches(utc_date);
"""
