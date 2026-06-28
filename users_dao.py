import sqlite3

# user table queries


def new_user(name, surname, email, password, role):
    # insert after register form, returns the new user id
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, surname, email, password, role) VALUES (?, ?, ?, ?, ?)",
        (name, surname, email, password, role),
    )
    user_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return user_id


def get_user_by_email(email):
    # used on login
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    # flask-login user_loader needs this
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def get_users_by_role(role):
    # admin dashboard tables
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, name, surname, email, role FROM users WHERE role = ? ORDER BY name, surname",
        (role,),
    ).fetchall()
    conn.close()
    return rows

def update_profile(user_id, name, surname):
    conn = sqlite3.connect("silkstep.db")
    conn.execute(
        "UPDATE users SET name = ?, surname = ? WHERE id = ?",
        (name, surname, user_id),
    )
    conn.commit()
    conn.close()

def update_password(user_id, new_password):
    conn = sqlite3.connect("silkstep.db")
    conn.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        (new_password, user_id),
    )
    conn.commit()
    conn.close()

def get_user_languages(user_id):
    # languages a guide speaks (used to limit tour languages + show on profile)
    conn = sqlite3.connect("silkstep.db")
    rows = conn.execute(
        "SELECT language FROM user_languages WHERE user_id = ? ORDER BY language",
        (user_id,),
    ).fetchall()
    conn.close()
    return [row[0] for row in rows]


def set_user_languages(user_id, languages):
    # wipe + save the languages picked at registration
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_languages WHERE user_id = ?", (user_id,))
    for lang in languages:
        cursor.execute(
            "INSERT INTO user_languages (user_id, language) VALUES (?, ?)",
            (user_id, lang),
        )
    conn.commit()
    cursor.close()
    conn.close()


def count_users():
    conn = sqlite3.connect("silkstep.db")
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return count


def count_by_role(role):
    # admin stat cards
    conn = sqlite3.connect("silkstep.db")
    count = conn.execute("SELECT COUNT(*) FROM users WHERE role = ?", (role,)).fetchone()[0]
    conn.close()
    return count
