import sqlite3

DB_NAME = "my_athletics.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():

    conn = get_connection()
    cur = conn.cursor()

    # =========================
    # SETTINGS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY,
        app_name TEXT,
        version TEXT
    )
    """)

    cur.execute("""
    INSERT OR IGNORE INTO settings
    (id, app_name, version)
    VALUES
    (1, 'My Athletics', '1.0')
    """)

    # =========================
    # MEETINGS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        date TEXT,
        team_mode TEXT,
        status TEXT
    )
    """)

    # =========================
    # TEAMS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER,
        name TEXT NOT NULL,
        team_type TEXT NOT NULL
    )
    """)

    # Add meeting_id to older databases
    cur.execute("""
    PRAGMA table_info(teams)
    """)

    team_columns = [
        row[1]
        for row in cur.fetchall()
    ]

    if "meeting_id" not in team_columns:

        cur.execute("""
        ALTER TABLE teams
        ADD COLUMN meeting_id INTEGER
        """)

    # =========================
    # ACTIVE MEETING
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS active_meeting (
        id INTEGER PRIMARY KEY,
        meeting_id INTEGER,
        user_mode TEXT
    )
    """)

    cur.execute("""
    INSERT OR IGNORE INTO active_meeting
    (id, meeting_id, user_mode)
    VALUES
    (1, NULL, 'Administrator')
    """)

    # =========================
    # ATHLETES
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS athletes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER,
        full_name TEXT NOT NULL,
        gender TEXT NOT NULL,
        age_group TEXT NOT NULL,
        team_id INTEGER,
        status TEXT NOT NULL DEFAULT 'Active'
    )
    """)

    # Add status to older databases
    cur.execute("""
    PRAGMA table_info(athletes)
    """)

    athlete_columns = [
        row[1]
        for row in cur.fetchall()
    ]

    if "status" not in athlete_columns:

        cur.execute("""
        ALTER TABLE athletes
        ADD COLUMN status TEXT NOT NULL DEFAULT 'Active'
        """)

    # =========================
    # EVENTS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER,
        event_name TEXT NOT NULL,
        event_type TEXT NOT NULL,
        gender TEXT,
        age_group TEXT
    )
    """)

    # =========================
    # EVENT ENTRIES
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS event_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER,
        event_id INTEGER,
        athlete_id INTEGER,
        status TEXT NOT NULL DEFAULT 'Active',
        UNIQUE(event_id, athlete_id)
    )
    """)

    # =========================
    # EVENT ENTRY STATUS MIGRATION
    # =========================
    cur.execute("""
    PRAGMA table_info(event_entries)
    """)

    event_entry_columns = [
        row[1]
        for row in cur.fetchall()
    ]

    if "status" not in event_entry_columns:

        cur.execute("""
        ALTER TABLE event_entries
        ADD COLUMN status TEXT
        NOT NULL DEFAULT 'Active'
        """)
        
    # =========================
    # HEATS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS heats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER,
        event_id INTEGER,
        heat_number INTEGER
    )
    """)

    # =========================
    # HEAT ENTRIES
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS heat_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        heat_id INTEGER,
        athlete_id INTEGER,
        lane_number INTEGER
    )
    """)

    # =========================
    # FINALS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS finals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        athlete_id INTEGER,
        seed_position INTEGER
    )
    """)
    # =========================
    # FINAL RESULTS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS final_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        athlete_id INTEGER,
        lane_number INTEGER,
        performance TEXT,
        position INTEGER,
        UNIQUE(event_id, athlete_id)
    )
    """)

    # =========================
    # FIELD ATTEMPTS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS field_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        athlete_id INTEGER NOT NULL,
        attempt_number INTEGER NOT NULL,
        performance TEXT,
        UNIQUE(
            event_id,
            athlete_id,
            attempt_number
        )
    )
    """)

    # =========================
    # POINTS CONFIGURATION
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS points_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER NOT NULL,
        position INTEGER NOT NULL,
        points REAL NOT NULL,
        UNIQUE(meeting_id, position)
    )
    """)

    # =========================
    # AWARDED POINTS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS awarded_points (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        athlete_id INTEGER NOT NULL,
        team_id INTEGER,
        position INTEGER NOT NULL,
        points REAL NOT NULL,
        UNIQUE(event_id, athlete_id)
    )
    """)

    # =========================
    # RESULTS
    # =========================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            heat_id INTEGER,
            athlete_id INTEGER,
            performance TEXT,
            position INTEGER,
            UNIQUE(heat_id, athlete_id)
        )
    """)

    conn.commit()
    conn.close()


def set_active_meeting(meeting_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE active_meeting
    SET meeting_id = ?
    WHERE id = 1
    """, (meeting_id,))

    conn.commit()
    conn.close()


def get_active_meeting():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT meeting_id
    FROM active_meeting
    WHERE id = 1
    """)

    row = cur.fetchone()

    conn.close()

    return row[0] if row else None


def set_user_mode(mode):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE active_meeting
    SET user_mode = ?
    WHERE id = 1
    """, (mode,))

    conn.commit()
    conn.close()


def get_user_mode():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT user_mode
    FROM active_meeting
    WHERE id = 1
    """)

    row = cur.fetchone()

    conn.close()

    return row[0] if row else "Administrator"