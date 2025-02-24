

class User:
    def __init__(self, first_name: str, last_name: str, username: str, token: str):
        self.fname = first_name
        self.lname = last_name
        self.uname = username
        self.token = token

    def to_dict(self) -> dict:
        return {
            "first_name": self.fname,
            "last_name": self.lname,
            "username": self.uname,
            "token": self.token
        }

    
class SignInMessage:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    def from_dict(val: dict): 
        username = val["username"]
        password = val["password"]

        if username is None or password is None:
            raise ValueError("not all members are provided")
        
        return SignInMessage(username, password)

    def get_dict(self) -> dict:
        return {
            "username": self.username,
            "password": self.password
        }