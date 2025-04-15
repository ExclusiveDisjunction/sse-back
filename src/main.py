"""
Stores the initial server interface using FLASK.
"""

import sys

# import sqlite3

import matplotlib.pyplot as plt
from nodes import NetworkNode, get_db_nodes, get_db_node_tags
from nodes import zip_nodes_and_tags
from graph import Graph
from db import open_db

# The graph data structure used for lookups
graph: Graph
# All nodes to send to the client
nodes: dict[int: NetworkNode] = {}

if __name__ == "__main__":
    print("Starting server...\n")

    db = open_db("data.sqlite")
    if db is None:
        print("Unable to open database. Exiting")
        sys.exit(1)

    # load up all DB information
    cursor = db.cursor()
    db_nodes = get_db_nodes(cursor)
    db_tags = get_db_node_tags(cursor)

    if db_nodes is None or db_tags is None:
        print("Unable to get database information. Exiting")
        sys.exit(2)

    # load graph data
    graph = Graph(db_nodes, "dijkstra.json")
    nodes = zip_nodes_and_tags(db_nodes, db_tags)

    start = int(input("start node? "))
    end = int(input("end node? "))

    path = graph.shortest_node_path(start, end)

    xs = []
    ys = []
    c = []
    for node in db_nodes.values():
        xs.append(node.x)
        ys.append(-node.y)
        c.append('b' if node.attr.is_path else 'r')

    if path is not None:
        print(f"The shortest distance is {path.data.dist}")
        try:
            last_node = nodes[path.data.points[0]]
            for i in range(1, len(path.data.points)):
                new_node = nodes[path.data.points[i]]
                plt.plot([last_node.x, new_node.x], [-last_node.y, -new_node.y], linewidth=5, c='k')
                last_node = new_node
        except KeyError as e:
            print(f"Unable to show map. {e}")

    plt.scatter(xs, ys, c=c)
    plt.grid(True)
    plt.show()
