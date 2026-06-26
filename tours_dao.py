import sqlite3

def get_tours():
    """fetch all tours with a comma-separated languages field."""
    query = """
        SELECT t.*,
        GROUP_CONCAT(tl.language, ', ') AS languages,
        (SELECT COUNT(*) FROM bookings b WHERE b.tour_id = t.id) AS booking_count
        FROM tours t
        LEFT JOIN tour_languages tl ON tl.tour_id = t.id
        GROUP BY t.id
    """
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def create_tour(title, schedule, duration, payment, summary, photo_url, meeting_point, meeting_map_link, max_participants, guide_id):
    """create a tour and return its new primary key id."""
    query = """
        INSERT INTO tours (title, schedule, duration, payment, summary, photo_url, meeting_point, meeting_map_link, max_participants, guide_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute(query, (title, schedule, duration, payment, summary, photo_url, meeting_point, meeting_map_link, max_participants, guide_id))    
    tour_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return tour_id

def get_tour_by_id(tour_id):
    """return one tour row by id or none if missing."""
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tours WHERE id = ?", (tour_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def get_languages_for_tour(tour_id):
    """return list of languages assigned to a tour."""
    query = "SELECT language FROM tour_languages WHERE tour_id = ? ORDER BY language"
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute(query, (tour_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]

def set_tour_languages(tour_id, languages):
    """replace all tour languages with the provided list."""
    
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tour_languages WHERE tour_id = ?", (tour_id,))
    for lang in languages:
        cursor.execute(
            "INSERT INTO tour_languages (tour_id, language) VALUES (?, ?)",
            (tour_id, lang),
        )
    conn.commit()
    cursor.close()
    conn.close()

def update_tour(tour_id, title, schedule, duration, payment, summary, photo_url, meeting_point, meeting_map_link, max_participants):
    """update editable tour fields."""
    query = """
        UPDATE tours SET title = ?, schedule = ?, duration = ?, payment = ?, summary = ?, photo_url = ?, meeting_point = ?, meeting_map_link = ?, max_participants = ?
        WHERE id = ?
    """
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute(query, (title, schedule, duration, payment, summary, photo_url, meeting_point, meeting_map_link, max_participants, tour_id))    
    conn.commit()
    cursor.close()
    conn.close()

def delete_tour(tour_id):
    """delete tour and cleanup language and photo mappings."""
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tour_languages WHERE tour_id = ?", (tour_id,))
    cursor.execute("DELETE FROM tour_photos WHERE tour_id = ?", (tour_id,))
    cursor.execute("DELETE FROM tours WHERE id = ?", (tour_id,))
    conn.commit()
    cursor.close()
    conn.close()

def count_tours():
    """return total number of tours."""
    conn = sqlite3.connect("silkstep.db")
    row = conn.execute("SELECT COUNT(*) FROM tours").fetchone()
    conn.close()
    return row[0]

def get_tours_by_language(language):
    if not language:
        return get_tours()
    query = """
        SELECT t.*,
               GROUP_CONCAT(tl.language, ', ') AS languages,
               (SELECT COUNT(*) FROM bookings b WHERE b.tour_id = t.id) AS booking_count
        FROM tours t
        JOIN tour_languages tl ON tl.tour_id = t.id
        WHERE tl.language = ?
        GROUP BY t.id
    """
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, (language,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
