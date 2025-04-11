"""
Includes network and database classes that work with Nodes.
"""

import sqlite3
from typing import Self

class GraphNode:
    """
    Represents a specific location on the map.
    """
    def __init__(self, x:float, y: float):
        self.x = x
        self.y = y

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

class GraphEdge:
    """
    Represents a connection between two different nodes, via their ID.
    """
    def __init__(self, src: int, dest: int, weight: float = 0):
        self.src = src
        self.dest = dest
        self.weight = weight

    def __str__(self):
        return f"{self.src} -({self.weight})-> {self.dest}"

    def __eq__(self, other):
        return self.src == other.src and self.dest == other.dest and self.weight == other.weight

    def reverse(self) -> Self:
        """
        Returns the same edge, with the same weight, but swaps the `src` and `dest`.
        """
        return GraphEdge(self.dest, self.src, self.weight)

class NodeAttributes:
    """
    Represents information about a specific node.
    """
    def __init__(self, name: str, group: str | None, is_path: bool):
        self.name = name
        self.group = group
        self.is_path = is_path

class DBNode:
    """
    A database representation of a node. 
    """
    def __init__(self, n_id: int, loc: GraphNode, attr: NodeAttributes):
        self.n_id = n_id
        self.loc = loc
        self.attr = attr

    def __sql_pack(self, include_id: bool) -> tuple:
        """
        Returns the information stored in the node for database operations.
        """
        if include_id:
            return (
                self.n_id,
                self.loc.x,
                self.loc.y,
                self.attr.name,
                self.attr.group,
                1 if self.attr.is_path else 0
            )

        return (
            self.loc.x,
            self.loc.y,
            self.attr.name,
            self.attr.group,
            1 if self.attr.is_path else 0
        )

    def insert_db(self, cur: sqlite3.Cursor) -> bool:
        """
        Attempts to insert the node into the database.
        """
        try:
            cur.execute(
                "INSERT INTO NODES(X, Y, NODE_NAME, NODE_GROUP, IS_PATH) VALUES (?, ?, ?, ?, ?)", 
                self.__sql_pack(False)
            )

            return True
        except sqlite3.Error as e:
            print(f"[ERROR] Unable to insert node because '{e}'")
            return False

    def update_db(self, cur: sqlite3.Cursor) -> bool:
        """
        Attempts to update the node in the database using the `N_ID`.
        """
        try:
            cur.execute(
                "UPDATE NODES SET X=?, Y=?, NODE_NAME=?, NODE_GROUP=?, IS_PATH=? WHERE N_ID=?", 
                self.__sql_pack(False) + self.n_id
            )
            return True
        except sqlite3.Error as e:
            print(f"[ERROR] Unable to update node because '{e}'")
            return False

    def delete_db(self, cur: sqlite3.Cursor) -> bool:
        """
        Attempts to remove the node from the database using the `N_ID`.
        """
        try:
            cur.execute(
                "DELETE FROM NODES WHERE N_ID=?", 
                (self.n_id)
            )

            return True
        except sqlite3.Error as e:
            print(f"[ERROR] Unable to delete node because '{e}'")
            return False

class NodeTags:
    """
    Simple information added onto a node for UI filtering. 
    """
    def __init__(self, n_id: int, tags: list[str]):
        self.n_id = n_id
        self.inner = tags

class NetworkNode:
    """
    Represents a network ready, JSON serializable node with extra information.
    """
    def __init__(self, loc: GraphNode, attr: NodeAttributes, tags: NodeTags):
        self.loc = loc
        self.attr = attr
        self.tags = tags

    def to_dict(self) -> dict:
        """
        Converts the node into a `dict` for JSON serialization.
        """
        return {
            "x": self.loc.x, # float
            "y": self.loc.y, # float
            "name": self.attr.name, # str
            "group": self.attr.group, # str?
            "is_path": self.attr.is_path, # bool
            "tags": self.tags.inner #[str]
        }

def get_db_nodes(cur: sqlite3.Cursor) -> dict[int: DBNode] | None:
    """
    Retrieves the nodes from the database.
    """
    result = cur.execute("SELECT N_ID, X, Y, NODE_NAME, NODE_GROUP, IS_PATH FROM NODES")
    vals = result.fetchall()
    if vals is None:
        return None

    result = {}
    for val in vals:
        result[val[0]] = DBNode(
            val[0],
            GraphNode(
                val[1],
                val[2]
            ),
            NodeAttributes(
                val[3],
                val[4],
                val[5] == 1
            )
        )

    return result

def strip_nodes(vals: dict[int, DBNode]) -> dict[int: GraphNode]:
    """
    Takes only the location data out of `DBNode`, making it ready for graph storage.
    """
    result = {}
    for (key, val) in vals.items():
        result[key] = val.loc

    return result

def get_db_edges(cur: sqlite3.Cursor) -> list[GraphEdge] | None:
    """
    Gets all node connections from the database.
    """
    result = cur.execute("SELECT SOURCE, DESTINATION FROM EDGES")
    vals = result.fetchall()
    if vals is None:
        return None

    result = []
    for val in vals:
        result.append(GraphEdge(val[0], val[1]))

    return result

def get_db_node_tags(cur: sqlite3.Cursor) -> dict[int: list[str]] | None:
    """
    Get all node tags from the database.
    """
    result = cur.execute("SELECT N_ID, TAG FROM NODE_TAGS")
    vals = result.fetchall()
    if vals is None:
        return None

    result: dict[int: list[str]] = {}
    for val in vals:
        current_list = result.get(val[0], [])
        current_list.append(val[1])
        result[val[0]] = current_list

    return result

def zip_nodes_and_tags(
        nodes: dict[int: DBNode],
        tags: dict[int: list[str]]
    ) -> dict[int: NetworkNode]:
    """
    Combines DBNodes and the retrieved tags to create `NetworkNode` instances.
    """
    result: dict[int: NetworkNode] = {}
    for (n_id, node) in nodes.items():
        result[n_id] = NetworkNode(node.loc, node.attr, NodeTags(n_id, []))

    for (n_id, tag) in tags.items():
        if n_id not in result:
            raise ValueError(
                f"The node id referenced by tag '{tag}', id: '{n_id}' was not found in the nodes."
            )

        result[n_id].tags.inner.append(tag)

    return result
