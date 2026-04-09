import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "database", "database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("\n===== USERS =====")
for row in cursor.execute("SELECT * FROM users"):
    print(row)

print("\n===== CONVERSATIONS =====")
for row in cursor.execute("SELECT * FROM conversations"):
    print(row)

conn.close()