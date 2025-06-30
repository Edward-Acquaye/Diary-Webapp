# migrate_data.py

import sqlite3
from app import db, User, JournalEntry, app

# Step 1: Connect to the old SQLite database
sqlite_conn = sqlite3.connect('diary.db')
sqlite_cursor = sqlite_conn.cursor()

# Step 2: Query data from SQLite
sqlite_cursor.execute("SELECT id, username, password FROM user")
users = sqlite_cursor.fetchall()

sqlite_cursor.execute("SELECT id, title, content, timestamp, user_id FROM journal_entry")
entries = sqlite_cursor.fetchall()

# Step 3: Insert into PostgreSQL via SQLAlchemy
with app.app_context():
    for u in users:
        user = User(id=u[0], username=u[1], password=u[2])
        db.session.add(user)

    for e in entries:
        entry = JournalEntry(id=e[0], title=e[1], content=e[2], timestamp=e[3], user_id=e[4])
        db.session.add(entry)

    db.session.commit()

print("✅ Migration complete!")
