import os
import sqlite3

# absolute path to the db so it works no matter the working directory (e.g. on pythonanywhere)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "silkstep.db")

# tours + tour_languages tables


def get_tours():
    # home + tours page, includes language list and booking count
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT t.*,
               GROUP_CONCAT(tl.language, ', ') AS languages,
               (gu.name || ' ' || gu.surname) AS guide_name,
               (SELECT COUNT(*) FROM bookings b WHERE b.tour_id = t.id) AS booking_count
        FROM tours t
        LEFT JOIN tour_languages tl ON tl.tour_id = t.id
        LEFT JOIN users gu ON gu.id = t.guide_id
        GROUP BY t.id
        """
    ).fetchall()
    conn.close()
    return rows


def get_tours_by_language(language):
    # filter dropdown on /tours
    if not language:
        return get_tours()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT t.*,
               GROUP_CONCAT(tl.language, ', ') AS languages,
               (gu.name || ' ' || gu.surname) AS guide_name,
               (SELECT COUNT(*) FROM bookings b WHERE b.tour_id = t.id) AS booking_count
        FROM tours t
        JOIN tour_languages tl ON tl.tour_id = t.id
        LEFT JOIN users gu ON gu.id = t.guide_id
        WHERE tl.language = ?
        GROUP BY t.id
        """,
        (language,),
    ).fetchall()
    conn.close()
    return rows


def get_tour_by_id(tour_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM tours WHERE id = ?", (tour_id,)).fetchone()
    conn.close()
    return row


def create_tour(title, schedule, duration, payment, summary, photo_url,
                meeting_point, meeting_map_link, max_participants, guide_id,
                duration_minutes=None):
    # returns new tour id; schedule/duration are display text, duration_minutes is structured
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO tours (title, schedule, duration, payment, summary, photo_url,
                           meeting_point, meeting_map_link, max_participants, guide_id,
                           duration_minutes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (title, schedule, duration, payment, summary, photo_url,
         meeting_point, meeting_map_link, max_participants, guide_id,
         duration_minutes),
    )
    tour_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return tour_id


def update_tour(tour_id, title, schedule, duration, payment, summary, photo_url,
                meeting_point, meeting_map_link, max_participants,
                duration_minutes=None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        UPDATE tours
        SET title = ?, schedule = ?, duration = ?, payment = ?, summary = ?,
            photo_url = ?, meeting_point = ?, meeting_map_link = ?, max_participants = ?,
            duration_minutes = ?
        WHERE id = ?
        """,
        (title, schedule, duration, payment, summary, photo_url,
         meeting_point, meeting_map_link, max_participants, duration_minutes, tour_id),
    )
    conn.commit()
    conn.close()


def delete_tour(tour_id):
    # remove linked languages, photos, bookings first
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tour_languages WHERE tour_id = ?", (tour_id,))
    cursor.execute("DELETE FROM tour_photos WHERE tour_id = ?", (tour_id,))
    cursor.execute("DELETE FROM tour_stops WHERE tour_id = ?", (tour_id,))
    cursor.execute("DELETE FROM tour_schedule WHERE tour_id = ?", (tour_id,))
    cursor.execute("DELETE FROM bookings WHERE tour_id = ?", (tour_id,))
    cursor.execute("DELETE FROM tours WHERE id = ?", (tour_id,))
    conn.commit()
    cursor.close()
    conn.close()


def get_languages_for_tour(tour_id):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT language FROM tour_languages WHERE tour_id = ? ORDER BY language",
        (tour_id,),
    ).fetchall()
    conn.close()
    return [row[0] for row in rows]


def set_tour_languages(tour_id, languages):
    # wipe old ones and save new checkboxes from form
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM tours").fetchone()[0]
    conn.close()
    return count
