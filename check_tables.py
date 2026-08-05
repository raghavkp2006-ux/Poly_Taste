import sqlite3

def check():
    conn = sqlite3.connect("spotify_tokens.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    for table_name in [t[0] for t in tables]:
        print(f"\n--- Table {table_name} ---")
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            print("Columns:", [d[0] for d in cursor.description])
            for r in rows:
                print(r)
        except Exception as e:
            print("Error:", e)
    conn.close()

if __name__ == "__main__":
    check()
