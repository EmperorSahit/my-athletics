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
        name TEXT NOT NULL,
        team_type TEXT NOT NULL
    )
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
        team_id INTEGER
    )
    """)

    # =========================
    # EVENTS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER,
        event_name TEXT NOT NULL,
        event_type TEXT NOT NULL
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
        athlete_id INTEGER
    )
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
    # RESULTS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        heat_id INTEGER,
        athlete_id INTEGER,
        performance TEXT,
        position INTEGER
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