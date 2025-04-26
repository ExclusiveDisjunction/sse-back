"""
This module handles all user information, including Network and Database classes.
"""

import sqlite3
from typing import Self, Optional

class User:
    """ 
    Represents User information that is stored inside of the database.
    """
    def __init__(self, u_id: int, username: str, password: bytes, salt: bytes):
        self.u_id = u_id
        self.username = username
        self.password = password
        self.salt = salt

    def sql_with_uid(self) -> tuple[int, str, bytes, bytes]:
        """
        Creates a set of tuples that can be used by sqlite for writing values. The order is:
        u_id, username, password, salt
        """
        return (
            self.u_id,
            self.username,
            self.password,
            self.salt
        )

    def sql_pack(self) -> tuple[str, bytes, bytes]:
        """
            Creates a set of tuples that can be used by sqlite for writing values. The order is:
            username, password, salt
        """

        return (
            self.username,
            self.password,
            self.salt
        )

    def __str__(self):
        return self.username

    def __eq__(self, other):
        return (self.u_id == other.u_id and self.username == other.username
                and self.password == other.password and self.salt == other.salt)

    def __hash__(self):
        return hash((self.u_id, self.username, self.password, self.salt))

    def insert_db(self, cur: sqlite3.Cursor) -> bool:
        """
        Attempts to insert the user into the database.
        """
        try:
            cur.execute(
                "INSERT INTO USERS (USERNAME, PASSWD, SALT) VALUES (?, ?, ?)",
                self.sql_pack()
            )
            self.u_id = int(cur.lastrowid)
            return True
        except sqlite3.IntegrityError as e:
            print(f"[ERROR] Unable to insert user '{self}' because of '{e}' (IntegrityError)")
            return False
        except sqlite3.DataError as e:
            print(f"[ERROR] Data error on DB insert '{e}'")
            return False

    def update_db(self, cur: sqlite3.Cursor) -> bool:
        """
        Attempts to update the user stored in the database using the `U_ID`. 
        """
        try:
            cur.execute(
                "UPDATE USERS SET USERNAME=?, PASSWD=?, SALT=? WHERE U_ID=?",
                (self.username, self.password, self.u_id)
            )

            return True
        except sqlite3.IntegrityError as e:
            print(f"[ERROR] Unable to update user '{self}' because of '{e}' (IntegrityError)")
            return False
        except sqlite3.DataError as e:
            print(f"[ERROR] Data error on DB insert '{e}'")
            return False

    def remove_db(self, cur: sqlite3.Cursor) -> bool:
        """
        Removes the `User` from the database.
        """

        try:
            cur.execute("DELETE FROM USERS WHERE U_ID=?", (self.u_id, ))
            return True
        except sqlite3.IntegrityError as e:
            print(f"[ERROR] Unable to delete user '{self}' because of '{e}' (IntegrityError)")
            return False
        except sqlite3.DataError as e:
            print(f"[ERROR] Data error on DB delete '{e}'")
            return False

    @staticmethod
    def get_all_users(cur: sqlite3.Cursor) -> list[Self] | None:
        """
        Attempts to retrieve all `User`s from the database.
        """
        result = cur.execute("SELECT U_ID, USERNAME, PASSWD, SALT FROM USERS")
        vals = result.fetchall()
        if vals is None:
            return None

        return_list = []
        for val in vals:
            u_id, username, password, salt = val
            return_list.append(User(u_id, username, password, salt))

        return return_list

def create_user_dict(users: list[User]) -> dict[str: User]:
    """
    Converts a list of users into a dictionary, with the username as the key.
    """
    result = {}
    for user in users:
        result[user.username] = user

    return result

class SignInRequest:
    """
    A JSON serializable class that represents a request from the client
    to sign in with specific credentials. 
    """
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    @staticmethod
    def from_dict(val: dict) -> None | Self:
        """
        Attempts to convert a dictionary to an instance of `SignInRequest`.
        """
        try:
            username = val["username"]
            password = val["password"]
        except KeyError:
            return None

        nones = username is None or password is None
        incorrect_instance = not isinstance(username, str) or not isinstance(password, str)
        if nones or incorrect_instance:
            return None

        return SignInRequest(username, password)

class CreateUserRequest:
    """
    Represents a request from the client to create a new user 
    with specific credentials and information. 
    """
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password.encode()

    @staticmethod
    def from_dict(val: dict) -> Self | None:
        """
        Attempts to convert a dictonary to an instance of `CreateUserRequest`.
        """
        try:
            username = val["username"]
            password = val["password"]
        except KeyError:
            return None

        if username is None or password is None:
            return None

        return CreateUserRequest(username, password)

class SignInResponse:
    """
    Represents the response from the server to a `SignInRequest` or `CreateUserRequest`.
    """
    def __init__(self, ok: bool, message: str, jwt: str | None):
        self.ok = ok
        self.message = message
        self.jwt = jwt

    def to_dict(self) -> dict[str: dict | bool | str]:
        """
        Converts this instance into a `dict`, for JSON serializing. 
        """
        return {
            "ok": self.ok,
            "message": self.message,
            "token": self.jwt
        }

class UserSessions:
    """
    A centralized storage unit for keeping authenticated users.
    """
    def __init__(self):
        self.users: dict[str: User] = {}

    def auth_user(self, jwt: str, user: User):
        """
        Stores a user's authentication inside the structure.
        """
        self.users[jwt] = user

    def get_auth(self, jwt: str) -> Optional[User]:
        """
        Retrieves a user's authentication, if stored.
        """
        self.users.get(jwt, None)

    def user_signed_in(self, target: User) -> str | None:
        """
        Determines the JWT associated with a specific user. 
        """
        for (jwt, user) in self.users.items():
            if user == target:
                return jwt

        return None
