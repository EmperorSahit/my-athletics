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
    
    conn.commit()
    conn.close()
    