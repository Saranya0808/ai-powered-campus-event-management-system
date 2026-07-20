import sqlite3

conn = sqlite3.connect('campus.db')
cursor = conn.cursor()

try:
    cursor.execute("SELECT user_id, username, password, role FROM users")
    rows = cursor.fetchall()
    print('\n--- ACCOUNTS CURRENTLY INSIDE YOUR DATABASE ---')
    for row in rows:
        print(f'Username: {row[1]} | Password: {row[2]} | Role: {row[3]}')
    print('-----------------------------------------------\n')
except Exception as e:
    print(f'Error accessing database: {e}')

conn.close()
