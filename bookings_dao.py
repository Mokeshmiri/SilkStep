import os
import sqlite3

# db path - works on pythonanywhere too
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "silkstep.db")

# bookings table queries


def create_booking(tour_id, participant_id, tour_date, party_size, notes, announce_email="", announce_phone=""):
    # participant books from tour detail form
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO bookings (tour_id, participant_id, tour_date, party_size, notes,
                              announce_email, announce_phone, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'confirmed')
        """,
        (tour_id, participant_id, tour_date, party_size, notes, announce_email, announce_phone),
    )
    booking_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return booking_id

def add_booking_guests(booking_id, guests):
    # guests = list of {"first_name": "...", "last_name": "..."}
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for guest in guests:
        cursor.execute(
            """
            INSERT INTO booking_guests (booking_id, first_name, last_name)
            VALUES (?, ?, ?)
            """,
            (booking_id, guest["first_name"], guest["last_name"]),
        )
    conn.commit()
    cursor.close()
    conn.close()

def get_guests_for_booking(booking_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT first_name, last_name
        FROM booking_guests
        WHERE booking_id = ?
        ORDER BY id
        """,
        (booking_id,),
    ).fetchall()
    conn.close()
    return rows


def get_bookings_by_participant(participant_id):
    # my bookings page
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT b.id, b.tour_id, b.tour_date, b.party_size, b.notes, b.status, b.created_at,
               b.announce_email, b.announce_phone,
               t.title AS tour_title, t.schedule AS tour_schedule,
               t.meeting_point AS meeting_point
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
    # guide dashboard - bookings on their tours only
    conn = sqlite3.connect(DB_PATH)
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
    # admin - every booking with guide + participant info
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM bookings WHERE id = ? AND participant_id = ?", (booking_id, participant_id))
    conn.commit()
    conn.close()


def tour_has_bookings(tour_id):
    # if true, guide cant edit tour anymore
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM bookings WHERE tour_id = ?", (tour_id,)).fetchone()[0]
    conn.close()
    return count > 0


def count_bookings():
    # admin stat card
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    conn.close()
    return count


def get_booking_by_id(booking_id):
    # used by cancel route to check owner + start time
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT id, tour_id, participant_id, tour_date, party_size, status FROM bookings WHERE id = ?",
        (booking_id,),
    ).fetchone()
    conn.close()
    return row


def get_booked_spots(tour_id, tour_date):
    # sum party_size - capacity check in book_tour()
    conn = sqlite3.connect(DB_PATH)
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
