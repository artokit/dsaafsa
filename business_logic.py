import sqlite3
from dataclasses import dataclass


@dataclass
class User:
    user_id: int
    subscribe: bool


class DB:
    def __init__(self):
        self.connect = sqlite3.connect('db.sqlite3')
        self.cursor = self.connect.cursor()

    def add_user(self, user_id: int):
        try:
            self.cursor.execute(f'INSERT INTO USERS VALUES ({user_id}, 1)')
            self.connect.commit()
        except sqlite3.IntegrityError:
            pass

    def get_user(self, user_id) -> User:
        return User(*self.cursor.execute(f'SELECT * FROM USERS WHERE user_id = {user_id}').fetchall()[0])

    def set_subscribe(self, user_id):
        self.cursor.execute(f'UPDATE USERS set subscribe = 1 where user_id = {user_id}')
        self.connect.commit()
