import sqlite3

def diagnose_db():
    try:
        conn = sqlite3.connect('campus.db')
        cursor = conn.cursor()
        
        # 1. Verify tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in database: {[t[0] for t in tables]}")
        
        # 2. Check rows in registrations
        if ('registrations',) in tables:
            cursor.execute("SELECT * FROM registrations")
            rows = cursor.fetchall()
            print(f"Number of rows in 'registrations': {len(rows)}")
            if rows:
                print(f"Actual data: {rows}")
        else:
            print("Error: 'registrations' table not found!")
            
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    diagnose_db()