import os
import sqlite3

# database file path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "silkstep.db")


def get_schedule_for_tour(tour_id):
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT start_time FROM tour_schedule WHERE tour_id = ? AND weekday = ?",
        (tour_id, weekday),
    ).fetchone()
    conn.close()
    return row[0] if row else None


def get_tour_ids_for_weekday(weekday):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT tour_id FROM tour_schedule WHERE weekday = ?",
        (weekday,),
    ).fetchall()
    conn.close()
    return {row[0] for row in rows}
