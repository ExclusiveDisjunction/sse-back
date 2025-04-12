"""
Uses the CSV file `graph_nodes.csv` to import into the database storage.
"""

import sys
import pandas
from db import open_db

if __name__ == "__main__":
    df = pandas.read_csv("graph_nodes.csv")
    df.info()

    db = open_db("data.sqlite")
    if db is None:
        sys.exit(1)

    # Clear old data
    db.execute("DELETE FROM NODES")

    for (n_id, x, y, name, group, is_path) in df.values:
        db.execute(
            """
            INSERT INTO NODES(N_ID, X, Y, NODE_NAME, NODE_GROUP, IS_PATH) 
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (n_id, x, y, name, group, is_path)
        )

    db.commit()
