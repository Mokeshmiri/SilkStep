import sqlite3

def get_tours():
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tours")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows