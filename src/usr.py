import sqlite3
import random
import string
from typing import Self

class User:
    def __init__(self, u_id: int, first_name: str, last_name: str, username: str, password_hash: str):
        self.u_id = u_id
        self.fname = first_name
        self.lname = last_name
        self.username = username
        self.password_hash = password_hash

    def sql_pack(self, uid: bool) -> tuple[str | int]:
        """
            Creates a set of tuples that can be used by sqlite for writing values. The order is:
            [u_id], fname, lname, username, password
        """
        if uid:
            return (
                self.u_id,
                self.fname,
                self.lname,
                self.username,
                self.password_hash
            )
        else:
            return (
                self.fname,
                self.lname,
                self.username,
                self.password_hash
            )
    
    def __str__(self): 
        return f"{self.lname}, {self.fname} ({self.username})"

class NetworkUser:
    """
    Represents a user that would be sent to a client over the network. It does not include information about passwords or tokens.
    """
    def __init__(self, user: User):
        self.fname = user.fname
        self.lname = user.lname
        self.username = user.username

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

    
def retreive_user(cur: sqlite3.Cursor, username: str) -> User | None:
    res = cur.execute("SELECT U_ID, F_NAME, L_NAME, PASSWD FROM USERS WHERE USERNAME = (?)", (username, ))
    row = res.fetchone()
    if row is None:
        return None
    
    u_id, f_name, l_name, passwd = row
    return User(u_id, f_name, l_name, username, passwd)

def write_user(cur: sqlite3.Cursor, user: User) -> bool:
    try:
        cur.execute("INSERT INTO USERS (F_NAME, L_NAME, USERNAME, PASSWD) VALUES (?, ?, ?, ?)", user.sql_pack(False))
        return True
    except Exception as e:
        print(f"[ERROR] Unable to insert user '{user}' because of '{e}'")
        return False
    
def update_user(cur: sqlite3.Cursor, user: User) -> bool:
    try:
        cur.execute("UPDATE USERS SET F_NAME=?, L_NAME=?, USERNAME=?, PASSWD=? WHERE U_ID=?", (user.fname, user.lname, user.username, user.password_hash, user.u_id))
        return True
    except:
        return False

if __name__ == "__main__":
    from db import open_db

    conn = open_db("temporary.sqlite")
    
    if conn is None:
        print("Unable to open database, quitting")
    else:
        cur = conn.cursor()
        while True:
            res = retreive_user(cur, "temporary")

            if res is None:
                print("Did not find user, adding.")
                user = User(0, "Alan", "Turing", "temporary", "asdfljasdlkfjasdl")
                if not write_user(cur, user):
                    print("Unable to write user")
                    break 

                conn.commit()
            else:
                print(f"got user '{res}' password '{res.password_hash}'")

                res.password_hash = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                if not update_user(cur, res):
                    print("Could not update user")
                else:
                    print("Updated user")

                    new_res = retreive_user(cur, "temporary")
                    assert new_res.password_hash == res.password_hash
                break

    conn.close()