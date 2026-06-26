import sqlite3

def create_booking(tour_id, participant_id, tour_date, party_size, notes):
    """create a booking row for one participant and their party."""
    query = """
        INSERT INTO bookings (tour_id, participant_id, tour_date, party_size, notes, status)
        VALUES (?, ?, ?, ?, ?, 'confirmed')
    """
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute(query, (tour_id, participant_id, tour_date, party_size, notes))
    conn.commit()
    cursor.close()
    conn.close()

def get_bookings_by_participant(participant_id):
    """return all bookings made by one participant (newest first)."""
    query = """
        SELECT b.id, b.tour_id, b.tour_date, b.party_size, b.notes, b.status, b.created_at,
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
    """delete only the booking that belongs to the participant."""
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
    """return true if at least one booking exists for a tour."""
    conn = sqlite3.connect("silkstep.db")
    row = conn.execute(
        "SELECT COUNT(*) FROM bookings WHERE tour_id = ?",
        (tour_id,)
    ).fetchone()
    conn.close()
    return row[0] > 0

def get_bookings_by_guide(guide_id):
    query = """
        SELECT b.id, b.tour_id, b.tour_date, b.party_size, b.notes, b.status, b.created_at,
               t.title AS tour_title,
               u.name AS participant_name, u.surname AS participant_surname, u.email AS participant_email
        FROM bookings b
        JOIN tours t ON t.id = b.tour_id
        JOIN users u ON u.id = b.participant_id
        WHERE t.guide_id = ?
        ORDER BY b.id DESC
    """
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, (guide_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def count_bookings():
    conn = sqlite3.connect("silkstep.db")
    row = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()
    conn.close()
    return row[0]

def get_booked_spots(tour_id, tour_date):
    """return total people already booked for one tour on one date."""
    query = """
        SELECT COALESCE(SUM(party_size), 0)
        FROM bookings
        WHERE tour_id = ? AND tour_date = ? AND status = 'confirmed'
    """
    conn = sqlite3.connect("silkstep.db")
    row = conn.execute(query, (tour_id, tour_date)).fetchone()
    conn.close()
    return row[0]