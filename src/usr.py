import sqlite3
import random
import string

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
    def __init__(self, user: User, token: str):
        self.fname = user.fname
        self.lname = user.lname
        self.username = user.username
        self.token = token

    def to_dict(self) -> dict:
        return {
            "first_name": self.fname,
            "last_name": self.lname,
            "username": self.username,
            "token": self.token
        }
    
    def __str__(self):
        return f"{self.lname}, {self.fname} ({self.username})"
    
class SignInMessage:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    def from_dict(val: dict): 
        username = val["username"]
        password = val["password"]

        if username is None or password is None or not isinstance(username, str) or not isinstance(password, str):
            raise ValueError("not all members are provided")
        
        return SignInMessage(username, password)

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "password": self.password
        }
    
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