import sqlite3
import random
import string
from typing import Self

class NetworkUser:
    """
    Represents a user that would be sent to a client over the network. It does not include information about passwords or tokens.
    """
    def __init__(self, f_name: str, l_name: str, username: str):
        self.fname = f_name
        self.lname = l_name
        self.username = username

    def to_dict(self) -> dict:
        return {
            "first_name": self.fname,
            "last_name": self.lname,
            "username": self.username
        }
    
    @staticmethod
    def from_dict(val: dict[str: str]) -> Self | None:
        pass


    def __str__(self):
        return f"{self.lname}, {self.fname} ({self.username})"

class User:
    def __init__(self, u_id: int, net: NetworkUser, password_hash: str):
        self.u_id = u_id
        self.net = net
        self.password_hash = password_hash

    def sql_pack(self, uid: bool) -> tuple[str | int]:
        """
            Creates a set of tuples that can be used by sqlite for writing values. The order is:
            [u_id], fname, lname, username, password
        """
        if uid:
            return (
                self.u_id,
                self.net.fname,
                self.net.lname,
                self.net.username,
                self.password_hash
            )
        else:
            return (
                self.net.fname,
                self.net.lname,
                self.net.username,
                self.password_hash
            )
    
    def __str__(self): 
        return str(self.net)
    
    def insert_db(self, cur: sqlite3.Cursor) -> bool:
        try:
            cur.execute("INSERT INTO USERS (F_NAME, L_NAME, USERNAME, PASSWD) VALUES (?, ?, ?, ?)", self.sql_pack(False))
            return True
        except Exception as e:
            print(f"[ERROR] Unable to insert user '{user}' because of '{e}'")
            return False
        
    def update_db(self, cur: sqlite3.Cursor) -> bool:
        try:
            cur.execute("UPDATE USERS SET F_NAME=?, L_NAME=?, USERNAME=?, PASSWD=? WHERE U_ID=?", (user.fname, user.lname, user.username, user.password_hash, user.u_id))
            return True
        except:
            return False
        
    def remove_db(self, cur: sqlite3.Cursor) -> bool:
        try:
            cur.execute("DELETE FROM USERS WHERE U_ID=?", (self.u_id))
            return True
        except Exception as e:
            print(f"[ERROR] Unable to delete user because '{e}'")
            return False
        
    @staticmethod
    def lookup_db(cur: sqlite3.Cursor, username: str) -> Self | None:
        res = cur.execute("SELECT U_ID, F_NAME, L_NAME, PASSWD FROM USERS WHERE USERNAME = (?)", (username, ))
        row = res.fetchone()
        if row is None:
            return None
        
        u_id, f_name, l_name, passwd = row
        return User(u_id, f_name, l_name, username, passwd)
    
    @staticmethod
    def get_all_users(cur: sqlite3.Cursor) -> list[Self] | None:
        result = cur.execute("SELECT U_ID, F_NAME, L_NAME, USERNAME, PASSWD FROM USERS")
        vals = result.fetchall()
        if vals is None:
            return None
        
        return_list = []
        for val in vals:
            return_list.append(User(val[0], val[1], val[2], val[3], val[4]))

        return return_list 

class SignInRequest:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    @staticmethod
    def from_dict(val: dict) -> None | Self: 
        try:
            username = val["username"]
            password = val["password"]
        except:
            return None

        if username is None or password is None or not isinstance(username, str) or not isinstance(password, str):
            return None
        
        return SignInRequest(username, password)

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "password": self.password
        }
    
class CreateUserRequest:
    def __init__(self, user: NetworkUser):
        self.user = user

    @staticmethod 
    def from_dict(val: dict) -> Self | None:
        try:
            user = NetworkUser.from_dict(val.get("user", {}))
        except:
            return None
        
        if user is None:
            return None
        
        return CreateUserRequest(user)
    def to_dict(self) -> dict[str: dict]:
        return {
            "user": self.user.to_dict()
        }
    
class AuthenticatedUser:
    def __init__(self, user: NetworkUser, token: str):
        self.user = user
        self.token = token

    def to_dict(self) -> dict[str: NetworkUser | str]:
        return {
            "user": self.user.to_dict(),
            "token": self.token
        }
    
    @staticmethod
    def from_dict(val: dict[str: dict | str]) -> Self | None:
        try:
            token = val["token"]
            user = NetworkUser.from_dict(val.get("user", {}))
        except:
            return None
        
        if token is None or user is None:
            return None
        
        return AuthenticatedUser(user, token)

class SignInResponse:
    def __init__(self, ok: bool, message: str, user: None | AuthenticatedUser):
        self.ok = ok
        self.message = message
        self.user = user
    
    def to_dict(self) -> dict[str: dict | bool | str]:
        return {
            "ok": self.ok,
            "message": self.message,
            "user": self.user.to_dict()
        }
    
    @staticmethod
    def from_dict(val: dict[str: dict | bool | str]) -> Self | None:
        try:
            ok = val["ok"]
            message = val["message"]
            user = AuthenticatedUser.from_dict(val.get("user", {}))
        except:
            return None
        
        if ok is None or message is None or user is None:
            return None
        
        return SignInResponse(ok, message, user)

class UserSessions:
    def __init__(self):
        self.users: dict[str: User] = {}

    def auth_user(self, jwt: str, user: User):
        self.users[jwt] = user

    def get_auth(self, jwt: str) -> User | None:
        self.users.get(jwt, None)

if __name__ == "__main__":
    from db import open_db

    conn = open_db("temporary.sqlite")
    
    if conn is None:
        print("Unable to open database, quitting")
    else:
        cur = conn.cursor()
        while True:
            res: User | None = user.lookup_db(cur, "temporary")

            if res is None:
                print("Did not find user, adding.")
                user = User(0, "Alan", "Turing", "temporary", "asdfljasdlkfjasdl")
                if not user.insert_db(cur):
                    print("Unable to write user")
                    break 

                conn.commit()
            else:
                print(f"got user '{res}' password '{res.password_hash}'")

                res.password_hash = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                if not res.update_db(cur):
                    print("Could not update user")
                else:
                    print("Updated user")

                    new_res = User.lookup_db(cur, "temporary")
                    assert new_res.password_hash == res.password_hash
                break

    conn.close()