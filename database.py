import os
import sqlite3


# =========================
# ATHLETIDESK DATABASE
# =========================
DB_NAME = "AthletiDesk.db"
LEGACY_DB_NAME = "my_athletics.db"


def migrate_database_filename():
    """
    Safely rename the legacy database on first launch.

    If AthletiDesk.db already exists it is never overwritten.
    The old database is only renamed when it is the sole
    database present, preserving all existing meetings/data.
    """

    if (
        not os.path.exists(DB_NAME)
        and os.path.exists(LEGACY_DB_NAME)
    ):
        os.replace(LEGACY_DB_NAME, DB_NAME)


# Perform the one-time filename migration before any connection.
migrate_database_filename()


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
    (1, 'AthletiDesk', '1.0')
    """)

    # Upgrade the branding stored by older databases.
    cur.execute("""
    UPDATE settings
    SET app_name = 'AthletiDesk'
    WHERE id = 1
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
        status TEXT,
        host_name TEXT,
        host_logo BLOB
    )
    """)

    # =========================
    # MEETING HOST BRANDING
    # SAFE DATABASE MIGRATION
    # =========================
    cur.execute("""
    PRAGMA table_info(meetings)
    """)

    meeting_columns = {
        row[1]
        for row in cur.fetchall()
    }

    if "host_name" not in meeting_columns:
        cur.execute("""
        ALTER TABLE meetings
        ADD COLUMN host_name TEXT
        """)

    if "host_logo" not in meeting_columns:
        cur.execute("""
        ALTER TABLE meetings
        ADD COLUMN host_logo BLOB
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
    # ATHLETE IMPORT FIELDS
    # SAFE DATABASE MIGRATION
    # =========================

    cur.execute("""
    PRAGMA table_info(athletes)
    """)

    athlete_columns = {
        row[1]
        for row in cur.fetchall()
    }

    if "entry_number" not in athlete_columns:

        cur.execute("""
        ALTER TABLE athletes
        ADD COLUMN entry_number TEXT
        """)

    if "first_name" not in athlete_columns:

        cur.execute("""
        ALTER TABLE athletes
        ADD COLUMN first_name TEXT
        """)

    if "surname" not in athlete_columns:

        cur.execute("""
        ALTER TABLE athletes
        ADD COLUMN surname TEXT
        """)

    if "date_of_birth" not in athlete_columns:

        cur.execute("""
        ALTER TABLE athletes
        ADD COLUMN date_of_birth TEXT
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
    # EVENT COMPETITION FORMAT
    # SAFE DATABASE MIGRATION
    # =========================

    cur.execute("""
    PRAGMA table_info(events)
    """)

    event_columns = {
        row[1]
        for row in cur.fetchall()
    }

    if "competition_format" not in event_columns:

        cur.execute("""
        ALTER TABLE events
        ADD COLUMN competition_format
        TEXT NOT NULL
        DEFAULT 'Timed Finals'
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
    # HIGH JUMP HEIGHTS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS high_jump_heights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        height_order INTEGER NOT NULL,
        height REAL NOT NULL,
        UNIQUE(event_id, height_order),
        UNIQUE(event_id, height)
    )
    """)

    # =========================
    # HIGH JUMP ATTEMPTS
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS high_jump_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meeting_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        athlete_id INTEGER NOT NULL,
        height_id INTEGER NOT NULL,
        attempt_number INTEGER NOT NULL,
        result TEXT NOT NULL,
        UNIQUE(
            event_id,
            athlete_id,
            height_id,
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