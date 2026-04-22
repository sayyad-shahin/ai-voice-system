import sqlite3, os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "database", "voiceai.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH)
conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
        created_at TEXT DEFAULT (datetime('now')), last_login TEXT
    );
    CREATE TABLE IF NOT EXISTS login_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, username TEXT, action TEXT, ip TEXT,
        ts TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, username TEXT,
        input_text TEXT, output_text TEXT,
        language TEXT, audio_url TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
""")
conn.commit(); conn.close()
print("Database ready:", DB_PATH)