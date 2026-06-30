import os
import sqlite3

# db path - works on pythonanywhere too
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "silkstep.db")

# tour stops - at least 4 per tour (exam requirement)
MIN_STOPS_PER_TOUR = 4
MAX_STOPS_PER_TOUR = 15


def get_stops_for_tour(tour_id):
    # list stops in order for tour detail page
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT id, tour_id, stop_order, name, description
        FROM tour_stops
        WHERE tour_id = ?
        ORDER BY stop_order, id
        """,
        (tour_id,),
    ).fetchall()
    conn.close()
    return rows


def count_stops_for_tour(tour_id):
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute(
        "SELECT COUNT(*) FROM tour_stops WHERE tour_id = ?",
        (tour_id,),
    ).fetchone()[0]
    conn.close()
    return count


def set_tour_stops(tour_id, stops):
    # stops = list of {"name": "...", "description": "..."}
    # wipe old stops and insert new ones from the form
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tour_stops WHERE tour_id = ?", (tour_id,))
    for i, stop in enumerate(stops, start=1):
        name = stop.get("name", "").strip()
        description = stop.get("description", "").strip()
        if not name:
            continue
        cursor.execute(
            """
            INSERT INTO tour_stops (tour_id, stop_order, name, description)
            VALUES (?, ?, ?, ?)
            """,
            (tour_id, i, name, description or ""),
        )
    conn.commit()
    cursor.close()
    conn.close()