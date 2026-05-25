import sqlite3

conn = sqlite3.connect("database/feedback.db")
cursor = conn.cursor()

users = [
    ("6141501", "testethel", "student"),
    ("21UM060", "03-11-2004", "student"),
    ("21UM058", "04-02-2006", "student"),
    ("KARE3124", "10-08-1990", "staff"),
    ("PRINC001", "01-01-1975", "principal")
]

cursor.executemany(
    "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
    users
)

conn.commit()
conn.close()

print("Users inserted successfully")