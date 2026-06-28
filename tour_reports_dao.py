import sqlite3

# post-tour reports: one per (tour, past date) - how many people actually came + a photo


def get_report(tour_id, tour_date):
    # current report for a date, or None if the guide hasnt filed one yet
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT id, tour_id, tour_date, attended_count, photo_path FROM tour_reports WHERE tour_id = ? AND tour_date = ?",
        (tour_id, tour_date),
    ).fetchone()
    conn.close()
    return row


def save_report(tour_id, tour_date, attended_count, photo_path):
    # insert or update the report for this date (one per date)
    conn = sqlite3.connect("silkstep.db")
    conn.execute(
        """
        INSERT INTO tour_reports (tour_id, tour_date, attended_count, photo_path)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(tour_id, tour_date)
        DO UPDATE SET attended_count = excluded.attended_count,
                      photo_path = COALESCE(excluded.photo_path, tour_reports.photo_path)
        """,
        (tour_id, tour_date, attended_count, photo_path),
    )
    conn.commit()
    conn.close()
