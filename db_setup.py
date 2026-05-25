import sqlite3
import os

# Create database folder if not exists
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = os.path.join(BASE_DIR, "database")
os.makedirs(DB_FOLDER, exist_ok=True)

DB_PATH = os.path.join(DB_FOLDER, "feedback.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# USERS TABLE (Added subject column)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    subject TEXT
)
""")

# STUDENT STATUS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS student_status (
    student_id TEXT PRIMARY KEY,
    has_submitted INTEGER DEFAULT 0
)
""")

# FEEDBACK TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT,
    subject TEXT,
    teacher TEXT,
    feedback_text TEXT,
    sentiment TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully!")