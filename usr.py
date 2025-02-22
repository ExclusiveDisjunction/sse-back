from typing import Self

class User:
    def __init__(self, username: str, first_name: str, last_name: str, token: str) -> Self:
        self.__username = username
        self.__fname = first_name
        self.__lname = last_name
        self.__token = token

    def username(self) -> str:
        self.__username

    def first_name(self) -> str:
        self.__fname

    def last_name(self) -> str:
        self.__lname

    def token(self) -> str:
        self.__token