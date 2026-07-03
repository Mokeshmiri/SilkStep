from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, row):
        self.id = row["id"]
        self.name = row["name"]
        self.surname = row["surname"]
        self.email = row["email"]
        self.password = row["password"]
        self.role = row["role"]
