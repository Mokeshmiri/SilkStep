import sqlite3

# weekly schedule per tour - weekday 0=Mon ... 6=Sun, one start time per day


def get_schedule_for_tour(tour_id):
    # list of {weekday, start_time} in day order
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT weekday, start_time
        FROM tour_schedule
        WHERE tour_id = ?
        ORDER BY weekday
        """,
        (tour_id,),
    ).fetchall()
    conn.close()
    return rows


def set_tour_schedule(tour_id, schedule):
    # schedule = list of {"weekday": int, "start_time": "HH:MM"}; wipe + re-insert
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tour_schedule WHERE tour_id = ?", (tour_id,))
    for item in schedule:
        cursor.execute(
            "INSERT INTO tour_schedule (tour_id, weekday, start_time) VALUES (?, ?, ?)",
            (tour_id, item["weekday"], item["start_time"]),
        )
    conn.commit()
    cursor.close()
    conn.close()


def get_start_time(tour_id, weekday):
    # start time for a tour on a given weekday, or None if not scheduled
    conn = sqlite3.connect("silkstep.db")
    row = conn.execute(
        "SELECT start_time FROM tour_schedule WHERE tour_id = ? AND weekday = ?",
        (tour_id, weekday),
    ).fetchone()
    conn.close()
    return row[0] if row else None


def get_tour_ids_for_weekday(weekday):
    # set of tour ids that run on this weekday - used by date filter
    conn = sqlite3.connect("silkstep.db")
    rows = conn.execute(
        "SELECT tour_id FROM tour_schedule WHERE weekday = ?",
        (weekday,),
    ).fetchall()
    conn.close()
    return {row[0] for row in rows}
