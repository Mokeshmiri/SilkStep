import sqlite3

# tour db access — tours, languages, delete cleanup


def get_tours():
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT t.*,
               GROUP_CONCAT(tl.language, ', ') AS languages,
               (SELECT COUNT(*) FROM bookings b WHERE b.tour_id = t.id) AS booking_count
        FROM tours t
        LEFT JOIN tour_languages tl ON tl.tour_id = t.id
        GROUP BY t.id
        """
    ).fetchall()
    conn.close()
    return rows


def get_tours_by_language(language):
    if not language:
        return get_tours()
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT t.*,
               GROUP_CONCAT(tl.language, ', ') AS languages,
               (SELECT COUNT(*) FROM bookings b WHERE b.tour_id = t.id) AS booking_count
        FROM tours t
        JOIN tour_languages tl ON tl.tour_id = t.id
        WHERE tl.language = ?
        GROUP BY t.id
        """,
        (language,),
    ).fetchall()
    conn.close()
    return rows


def get_tour_by_id(tour_id):
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM tours WHERE id = ?", (tour_id,)).fetchone()
    conn.close()
    return row


def create_tour(title, schedule, duration, payment, summary, photo_url,
                meeting_point, meeting_map_link, max_participants, guide_id):
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO tours (title, schedule, duration, payment, summary, photo_url,
                           meeting_point, meeting_map_link, max_participants, guide_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (title, schedule, duration, payment, summary, photo_url,
         meeting_point, meeting_map_link, max_participants, guide_id),
    )
    tour_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return tour_id


def update_tour(tour_id, title, schedule, duration, payment, summary, photo_url,
                meeting_point, meeting_map_link, max_participants):
    conn = sqlite3.connect("silkstep.db")
    conn.execute(
        """
        UPDATE tours
        SET title = ?, schedule = ?, duration = ?, payment = ?, summary = ?,
            photo_url = ?, meeting_point = ?, meeting_map_link = ?, max_participants = ?
        WHERE id = ?
        """,
        (title, schedule, duration, payment, summary, photo_url,
         meeting_point, meeting_map_link, max_participants, tour_id),
    )
    conn.commit()
    conn.close()


def delete_tour(tour_id):
    # clean up related rows before deleting the tour
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tour_languages WHERE tour_id = ?", (tour_id,))
    cursor.execute("DELETE FROM tour_photos WHERE tour_id = ?", (tour_id,))
    cursor.execute("DELETE FROM bookings WHERE tour_id = ?", (tour_id,))
    cursor.execute("DELETE FROM tours WHERE id = ?", (tour_id,))
    conn.commit()
    cursor.close()
    conn.close()


def get_languages_for_tour(tour_id):
    conn = sqlite3.connect("silkstep.db")
    rows = conn.execute(
        "SELECT language FROM tour_languages WHERE tour_id = ? ORDER BY language",
        (tour_id,),
    ).fetchall()
    conn.close()
    return [row[0] for row in rows]


def set_tour_languages(tour_id, languages):
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


def count_tours():
    conn = sqlite3.connect("silkstep.db")
    count = conn.execute("SELECT COUNT(*) FROM tours").fetchone()[0]
    conn.close()
    return count
