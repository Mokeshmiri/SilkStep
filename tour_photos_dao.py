import sqlite3

# tour photos table - up to 5 per tour (exam requirement)
MAX_PHOTOS_PER_TOUR = 5


def get_photos_for_tour(tour_id):
    # gallery on tour detail + edit page
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, tour_id, photo_path, sort_order FROM tour_photos WHERE tour_id = ? ORDER BY sort_order, id",
        (tour_id,),
    ).fetchall()
    conn.close()
    return rows


def count_photos_for_tour(tour_id):
    # check before upload so we dont go over 5
    conn = sqlite3.connect("silkstep.db")
    count = conn.execute("SELECT COUNT(*) FROM tour_photos WHERE tour_id = ?", (tour_id,)).fetchone()[0]
    conn.close()
    return count


def add_photo(tour_id, photo_path):
    # save db row after file lands in static/uploads
    sort_order = count_photos_for_tour(tour_id) + 1
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tour_photos (tour_id, photo_path, sort_order) VALUES (?, ?, ?)",
        (tour_id, photo_path, sort_order),
    )
    photo_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return photo_id


def get_photo_by_id(photo_id):
    # delete photo route
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM tour_photos WHERE id = ?", (photo_id,)).fetchone()
    conn.close()
    return row


def delete_photo(photo_id):
    # row only - app.py also deletes the file on disk
    conn = sqlite3.connect("silkstep.db")
    conn.execute("DELETE FROM tour_photos WHERE id = ?", (photo_id,))
    conn.commit()
    conn.close()
