import sqlite3

def check():
    conn = sqlite3.connect('instance/summarizer.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(book)")
    cols = [row[1] for row in cursor.fetchall()]
    conn.close()
    print("Current columns in 'book' table:", cols)

if __name__ == "__main__":
    check()
