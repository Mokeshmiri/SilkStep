import sqlite3

# all user db access lives here


def new_user(name, surname, email, password, role):
    conn = sqlite3.connect("silkstep.db")
    conn.execute(
        "INSERT INTO users (name, surname, email, password, role) VALUES (?, ?, ?, ?, ?)",
        (name, surname, email, password, role),
    )
    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def get_users_by_role(role):
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, name, surname, email, role FROM users WHERE role = ? ORDER BY name, surname",
        (role,),
    ).fetchall()
    conn.close()
    return rows


def count_users():
    conn = sqlite3.connect("silkstep.db")
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return count


def count_by_role(role):
    conn = sqlite3.connect("silkstep.db")
    count = conn.execute("SELECT COUNT(*) FROM users WHERE role = ?", (role,)).fetchone()[0]
    conn.close()
    return count
