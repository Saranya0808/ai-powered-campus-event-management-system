import sqlite3

conn = sqlite3.connect('campus.db')

try:
    conn.execute("ALTER TABLE events ADD COLUMN image_url TEXT DEFAULT ''")
    print("image_url column added successfully!")
except Exception as e:
    print(e)

conn.commit()
conn.close()