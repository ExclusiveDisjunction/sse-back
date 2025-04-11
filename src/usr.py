"""
This module handles all user information, including Network and Database classes.
"""

import sqlite3
from typing import Self

class NetworkUser:
    """
    Represents a user that would be sent to a client over the network. 
    It does not include information about passwords or tokens.
    """
    def __init__(self, f_name: str, l_name: str, username: str):
        self.fname = f_name
        self.lname = l_name
        self.username = username

    def to_dict(self) -> dict:
        """ 
        Converts the NetworkUser into a JSON serializable type.
        """
        return {
            "first_name": self.fname,
            "last_name": self.lname,
            "username": self.username
        }

    @staticmethod
    def from_dict(val: dict[str: str]) -> Self | None:
        """
        Attempts to convert a dictionary into a `NetworkUser` interface.
        """
        try:
            first_name = val["first_name"]
            last_name = val["last_name"]
            username = val["username"]
        except KeyError:
            return None

        return NetworkUser(first_name, last_name, username)


    def __str__(self):
        return f"{self.lname}, {self.fname} ({self.username})"

class User:
    """ 
    Represents User information that is stored inside of the database.
    """
    def __init__(self, u_id: int, net: NetworkUser, password: bytes, salt: bytes):
        self.u_id = u_id
        self.net = net
        self.password = password
        self.salt = salt

    def sql_pack(self, uid: bool) -> tuple[str | int]:
        """
            Creates a set of tuples that can be used by sqlite for writing values. The order is:
            [u_id], fname, lname, username, password, salt
        """
        if uid:
            return (
                self.u_id,
                self.net.fname,
                self.net.lname,
                self.net.username,
                self.password,
                self.salt
            )

        return (
            self.net.fname,
            self.net.lname,
            self.net.username,
            self.password,
            self.salt
        )

    def __str__(self):
        return str(self.net)

    def insert_db(self, cur: sqlite3.Cursor) -> bool:
        """
        Attempts to insert the user into the database.
        """
        try:
            cur.execute(
                "INSERT INTO USERS (F_NAME, L_NAME, USERNAME, PASSWD, SALT) VALUES (?, ?, ?, ?, ?)", 
                self.sql_pack(False)
            )
            self.u_id = int(cur.lastrowid())
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
                "UPDATE USERS SET F_NAME=?, L_NAME=?, USERNAME=?, PASSWD=?, SALT=? WHERE U_ID=?", 
                (self.net.fname, self.net.lname, self.net.username, self.password, self.u_id)
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
            cur.execute("DELETE FROM USERS WHERE U_ID=?", (self.u_id))
            return True
        except sqlite3.IntegrityError as e:
            print(f"[ERROR] Unable to delete user '{self}' because of '{e}' (IntegrityError)")
            return False
        except sqlite3.DataError as e:
            print(f"[ERROR] Data error on DB delete '{e}'")
            return False

    @staticmethod
    def lookup_db(cur: sqlite3.Cursor, username: str) -> Self | None:
        """
        Attempts to look up a specific username from the database.
        """
        result = cur.execute(
            "SELECT U_ID, F_NAME, L_NAME, PASSWD, SALT FROM USERS WHERE USERNAME = (?)", 
            (username, )
        )

        row = result.fetchone()
        if row is None:
            return None

        u_id, f_name, l_name, passwd, salt = row
        net_user = NetworkUser(f_name, l_name, username)
        return User(u_id, net_user, passwd, salt)

    @staticmethod
    def get_all_users(cur: sqlite3.Cursor) -> list[Self] | None:
        """
        Attempts to retreive all `User`s from the database.
        """
        result = cur.execute("SELECT U_ID, F_NAME, L_NAME, USERNAME, PASSWD, SALT FROM USERS")
        vals = result.fetchall()
        if vals is None:
            return None

        return_list = []
        for val in vals:
            u_id, f_name, l_name, username, password, salt = val
            net_user = NetworkUser(f_name, l_name, username)
            return_list.append(User(u_id, net_user, password, salt))

        return return_list

class SignInRequest:
    """
    A JSON serializeable class that represents a request from the client
    to sign in with specific credentials. 
    """
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    @staticmethod
    def from_dict(val: dict) -> None | Self:
        """
        Attempts to convert a dictonary to an instance of `SignInRequest`.
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
    def __init__(self, user: NetworkUser, password: str):
        self.user = user
        self.password = password

    @staticmethod
    def from_dict(val: dict) -> Self | None:
        """
        Attempts to convert a dictonary to an instance of `CreateUserRequest`.
        """
        try:
            user = NetworkUser.from_dict(val.get("user", {}))
            password = val["password"]
        except KeyError:
            return None

        if user is None or password is None:
            return None

        return CreateUserRequest(user, password)

class AuthenticatedUser:
    """
    Combines a `NetworkUser` with a specific JWT token.
    """
    def __init__(self, user: NetworkUser, token: str):
        self.user = user
        self.token = token

    def to_dict(self) -> dict[str: NetworkUser | str]:
        """
        Converts this instance into a `dict`, for JSON serializing. 
        """
        return {
            "user": self.user.to_dict(),
            "token": self.token
        }

class SignInResponse:
    """
    Represents the response from the server to a `SignInRequest` or `CreateUserRequest`.
    """
    def __init__(self, ok: bool, message: str, user: None | AuthenticatedUser):
        self.ok = ok
        self.message = message
        self.user = user

    def to_dict(self) -> dict[str: dict | bool | str]:
        """
        Converts this instance into a `dict`, for JSON serializing. 
        """
        return {
            "ok": self.ok,
            "message": self.message,
            "user": self.user.to_dict()
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

    def get_auth(self, jwt: str) -> User | None:
        """
        Retreives a user's authentication, if stored.
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
