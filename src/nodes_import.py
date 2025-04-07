from db import open_db

import sqlite3
import pandas

if __name__ == "__main__":
    df = pandas.read_csv("graph_nodes.csv")
    df.info()

    db = open_db("../data.sqlite")
    if db is None:
        exit(1)

    # Clear old data
    db.execute("DELETE FROM NODES")

    for (id, x, y, name, group, is_path) in df.values:
        db.execute("INSERT INTO NODES(N_ID, X, Y, NODE_NAME, NODE_GROUP, IS_PATH) VALUES(?, ?, ?, ?, ?, ?)", (id, x, y, name, group, is_path))

    db.commit()