
import sqlite3
import json

try:
    conn = sqlite3.connect('users_database.json')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("Table 'users' does not exist.")
    else:
        cursor.execute("SELECT count(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"User count: {count}")
        if count > 0:
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
            print("Users:", rows)
    conn.close()
except sqlite3.Error as e:
    print(f"SQLite error: {e}")
except Exception as e:
    print(f"Error: {e}")
