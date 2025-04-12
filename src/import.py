import sys
import pandas
import sqlite3
from db import open_db

def import_nodes(cur: sqlite3.Cursor):
    """
    Imports from the import/nodes.csv file.
    """

    df = pandas.read_csv("import/nodes.csv")
    print("Node stats:")
    df.info()

    cur.execute("DELETE FROM NODES")

    for (n_id, x, y, name, group, is_path) in df.values:
        cur.execute(
            """
            INSERT INTO NODES(N_ID, X, Y, NODE_NAME, NODE_GROUP, IS_PATH) 
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (n_id, x, y, name, group, is_path)
        )

def import_edges(cur: sqlite3.Cursor):
    """
    Imports from the import/edges.csv file.
    """

    df = pandas.read_csv("import/edges.csv")
    df['Source'] = df['Source'].astype(int)
    df['Destination'] = df['Destination'].astype(int)
    print("Edge stats:")
    df.info()

    cur.execute("DELETE FROM EDGES")

    for (source, dest) in df.values:
        cur.execute(
            "INSERT INTO EDGES(SOURCE, DESTINATION) VALUES (?, ?)",
            (source, dest)
        )

def import_tags(cur: sqlite3.Cursor):
    df = pandas.read_csv("import/tags.csv")
    df['Tag'] = df['Tag'].astype(str)
    df['ID'] = df['ID'].astype(int)

    print("Tag stats:")
    df.info()

    cur.execute("DELETE FROM NODE_TAGS")

    for (n_id, tag) in df.values:
        cur.execute(
            "INSERT INTO NODE_TAGS(N_ID, TAG) VALUES (?, ?)",
            (n_id, tag)
        )

if __name__ == "__main__":
    db = open_db("data.sqlite")
    if db is None:
        sys.exit(1)

    cursor = db.cursor()
    import_nodes(cursor)
    import_edges(cursor)
    import_tags(cursor)

    db.commit()