"""
Simple utilities to manage the database & its connections.
"""

import sqlite3

def open_db(path: str) -> sqlite3.Connection | None:
    """
    Opens the database at `path`, and runs the `ensure_tables` function.
    """
    try:
        conn = sqlite3.connect(path)
    except sqlite3.DatabaseError as e:
        print(f"Database Error: '{e}'")
        return None
    except sqlite3.Error as e:
        print(f"General SQLite Error: '{e}'")

    cur = conn.cursor()
    if not ensure_tables(cur):
        return None

    return conn

def ensure_tables(cur: sqlite3.Cursor) -> bool:
    """
    Runs the create table scripts, if the tables do not exist.
    """
    try:
        contents = str()
        with open("table_create.sql", "r", encoding="utf-8") as file:
            contents = file.read()

        cur.executescript(contents)

        return True
    except sqlite3.Error as e:
        print(f"Unable to create tables '{e}'")
        return False
 
if __name__ == "__main__":
    # Attempt to create the database
    connection = open_db("test-db.sqlite")
