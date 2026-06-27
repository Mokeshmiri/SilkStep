import sqlite3

# bookings table queries


def create_booking(tour_id, participant_id, tour_date, party_size, notes, announce_email="", announce_phone=""):
    # participant books from tour detail form
    conn = sqlite3.connect("silkstep.db")
    conn.execute(
        """
        INSERT INTO bookings (tour_id, participant_id, tour_date, party_size, notes,
                              announce_email, announce_phone, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'confirmed')
        """,
        (tour_id, participant_id, tour_date, party_size, notes, announce_email, announce_phone),
    )
    conn.commit()
    conn.close()


def get_bookings_by_participant(participant_id):
    # my bookings page
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT b.id, b.tour_id, b.tour_date, b.party_size, b.notes, b.status, b.created_at,
               b.announce_email, b.announce_phone,
               t.title AS tour_title, t.schedule AS tour_schedule
        FROM bookings b
        JOIN tours t ON t.id = b.tour_id
        WHERE b.participant_id = ?
        ORDER BY b.id DESC
        """,
        (participant_id,),
    ).fetchall()
    conn.close()
    return rows


def get_bookings_by_guide(guide_id):
    # guide dashboard — bookings on their tours only
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT b.id, b.tour_id, b.tour_date, b.party_size, b.notes, b.status, b.created_at,
               b.announce_email, b.announce_phone,
               t.title AS tour_title,
               u.name AS participant_name, u.surname AS participant_surname, u.email AS participant_email
        FROM bookings b
        JOIN tours t ON t.id = b.tour_id
        JOIN users u ON u.id = b.participant_id
        WHERE t.guide_id = ?
        ORDER BY b.id DESC
        """,
        (guide_id,),
    ).fetchall()
    conn.close()
    return rows


def get_all_bookings():
    # admin — every booking with guide + participant info
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT b.id, b.tour_id, b.tour_date, b.party_size, b.notes, b.status, b.created_at,
               b.announce_email, b.announce_phone,
               t.title AS tour_title,
               g.name AS guide_name, g.surname AS guide_surname, g.email AS guide_email,
               u.name AS participant_name, u.surname AS participant_surname, u.email AS participant_email
        FROM bookings b
        JOIN tours t ON t.id = b.tour_id
        JOIN users g ON g.id = t.guide_id
        JOIN users u ON u.id = b.participant_id
        ORDER BY b.id DESC
        """
    ).fetchall()
    conn.close()
    return rows


def cancel_booking(booking_id, participant_id):
    # only delete if it belongs to this user
    conn = sqlite3.connect("silkstep.db")
    conn.execute("DELETE FROM bookings WHERE id = ? AND participant_id = ?", (booking_id, participant_id))
    conn.commit()
    conn.close()


def tour_has_bookings(tour_id):
    # if true, guide cant edit tour anymore
    conn = sqlite3.connect("silkstep.db")
    count = conn.execute("SELECT COUNT(*) FROM bookings WHERE tour_id = ?", (tour_id,)).fetchone()[0]
    conn.close()
    return count > 0


def count_bookings():
    # admin stat card
    conn = sqlite3.connect("silkstep.db")
    count = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    conn.close()
    return count


def get_booked_spots(tour_id, tour_date):
    # sum party_size — capacity check in book_tour()
    conn = sqlite3.connect("silkstep.db")
    booked = conn.execute(
        """
        SELECT COALESCE(SUM(party_size), 0)
        FROM bookings
        WHERE tour_id = ? AND tour_date = ? AND status = 'confirmed'
        """,
        (tour_id, tour_date),
    ).fetchone()[0]
    conn.close()
    return booked
