import sqlite3

MAX_PHOTOS_PER_TOUR = 5


def get_photos_for_tour(tour_id):
    """return all photo rows for a tour ordered by sort_order then id."""
    query = """
        SELECT id, tour_id, photo_path, sort_order
        FROM tour_photos
        WHERE tour_id = ?
        ORDER BY sort_order, id
    """
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, (tour_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def count_photos_for_tour(tour_id):
    conn = sqlite3.connect("silkstep.db")
    row = conn.execute(
        "SELECT COUNT(*) FROM tour_photos WHERE tour_id = ?",
        (tour_id,),
    ).fetchone()
    conn.close()
    return row[0]


def add_photo(tour_id, photo_path):
    """insert one photo row and return its new id."""
    sort_order = count_photos_for_tour(tour_id) + 1
    query = """
        INSERT INTO tour_photos (tour_id, photo_path, sort_order)
        VALUES (?, ?, ?)
    """
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute(query, (tour_id, photo_path, sort_order))
    photo_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return photo_id


def get_photo_by_id(photo_id):
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM tour_photos WHERE id = ?",
        (photo_id,),
    ).fetchone()
    conn.close()
    return row


def delete_photo(photo_id):
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tour_photos WHERE id = ?", (photo_id,))
    conn.commit()
    cursor.close()
    conn.close()


def delete_photos_for_tour(tour_id):
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tour_photos WHERE tour_id = ?", (tour_id,))
    conn.commit()
    cursor.close()
    conn.close()
