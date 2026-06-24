import sqlite3

def create_booking(tour_id, participant_id, tour_date):
    query = """
        INSERT INTO bookings (tour_id, participant_id, tour_date, status)
        VALUES (?, ?, ?, 'confirmed')
    """
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute(query, (tour_id, participant_id, tour_date))
    conn.commit()
    cursor.close()
    conn.close()

def get_bookings_by_participant(participant_id):
    query = """
        SELECT b.id, b.tour_id, b.tour_date, b.status, b.created_at,
               t.title AS tour_title, t.schedule AS tour_schedule
        FROM bookings b
        JOIN tours t ON t.id = b.tour_id
        WHERE b.participant_id = ?
        ORDER BY b.id DESC
    """
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, (participant_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def cancel_booking(booking_id, participant_id):
    query = """
        DELETE FROM bookings
        WHERE id = ? AND participant_id = ?
    """
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute(query, (booking_id, participant_id))
    conn.commit()
    cursor.close()
    conn.close()

def tour_has_bookings(tour_id):
    conn = sqlite3.connect("silkstep.db")
    row = conn.execute(
        "SELECT COUNT(*) FROM bookings WHERE tour_id = ?",
        (tour_id,)
    ).fetchone()
    conn.close()
    return row[0] > 0