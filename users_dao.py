import sqlite3

def new_user(name, surname, email, password, role):
    query = "INSERT INTO users (name, surname, email, password, role) VALUES (?, ?, ?, ?, ?)"
    conn = sqlite3.connect("silkstep.db")
    cursor = conn.cursor()
    cursor.execute(query, (name, surname, email, password, role))
    conn.commit()
    cursor.close()
    conn.close()

def get_user_by_email(email):
    query = "SELECT * FROM users WHERE email = ?"
    conn = sqlite3.connect("silkstep.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def count_users():
    conn = sqlite3.connect("silkstep.db")
    row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    conn.close()
    return row[0]

def count_by_role(role):
    conn = sqlite3.connect("silkstep.db")
    row = conn.execute("SELECT COUNT(*) FROM users WHERE role = ?", (role,)).fetchone()
    conn.close()
    return row[0]