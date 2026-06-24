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

def create_tour(title, schedule, duration, payment, summary, guide_id):
    query = """
        INSERT INTO tours (title, schedule, duration, payment, summary, guide_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute(query, (title, schedule, duration, payment, summary, guide_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_tour_by_id(tour_id):
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tours WHERE id = ?", (tour_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def update_tour(tour_id, title, schedule, duration, payment, summary):
    query = """
        UPDATE tours SET title = ?, schedule = ?, duration = ?, payment = ?, summary = ? WHERE id = ?
    """
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute(query, (title, schedule, duration, payment, summary, tour_id))
    conn.commit()
    cursor.close()
    conn.close()
    
def delete_tour(tour_id):
    query = """
        DELETE FROM tours WHERE id = ?
    """
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute(query, (tour_id,))
    conn.commit()
    cursor.close()
    conn.close()

def count_tours():
    conn = sqlite3.connect("silkstep.db")
    row = conn.execute("SELECT COUNT(*) FROM tours").fetchone()
    conn.close()
    return row[0]