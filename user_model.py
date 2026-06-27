from flask_login import UserMixin


class User(UserMixin):
    # wraps a sqlite user row so flask-login can use it

    def __init__(self, row):
        # copy fields from sqlite row into the user object
        self.id = row["id"]
        self.name = row["name"]
        self.surname = row["surname"]
        self.email = row["email"]
        self.password = row["password"]
        self.role = row["role"]
