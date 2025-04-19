"""
Includes network and database classes that work with Nodes.
"""

import sqlite3

class NodeAttributes:
    """
    Represents information about a specific node.
    """
    def __init__(self, name: str, group: str | None, is_path: bool):
        self.__name = name
        self.__group = group
        self.__is_path = is_path

    @property
    def name(self) -> str:
        """The name of the node"""
        return self.__name

    @property
    def group(self) -> str | None:
        """The group of the node"""
        return self.__group

    @property
    def is_path(self) -> bool:
        """When `True`, this node is a path, when `False`, it is a location."""
        return self.__is_path

class DBNode:
    """
    A database representation of a node. 
    """
    def __init__(self, n_id: int, x: float, y: float, attr: NodeAttributes):
        self.n_id = n_id
        self.x = x
        self.y = y
        self.attr = attr

    def __sql_pack(self, include_id: bool) -> tuple:
        """
        Returns the information stored in the node for database operations.
        """
        if include_id:
            return (
                self.n_id,
                self.x,
                self.y,
                self.attr.name,
                self.attr.group,
                1 if self.attr.is_path else 0
            )

        return (
            self.x,
            self.y,
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
                self.__sql_pack(False) + (self.n_id, )
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
                (self.n_id, )
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
        self.__n_id = n_id
        self.values = tags

    @property
    def n_id(self) -> int:
        """The bound node that this tag is for"""
        return self.__n_id

class NetworkNode:
    """
    Represents a network ready, JSON serializable node with extra information.
    """
    def __init__(self, x: float, y: float, attr: NodeAttributes, tags: NodeTags):
        self.x = x
        self.y = y
        self.attr = attr
        self.tags = tags

    def to_dict(self) -> dict:
        """
        Converts the node into a `dict` for JSON serialization.
        """
        return {
            "x": self.x, # float
            "y": self.y, # float
            "name": self.attr.name, # str
            "group": self.attr.group, # str?
            "is_path": self.attr.is_path, # bool
            "tags": self.tags.values #[str]
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
        n_id, x, y, name, group, is_path = val
        result[n_id] = DBNode(
            n_id,
            x,
            y,
            NodeAttributes(
                name,
                group,
                is_path == 1
            )
        )

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
    for (n_id, tag) in vals:
        current_list = result.get(n_id, [])
        current_list.append(tag)
        result[n_id] = current_list

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
        result[n_id] = NetworkNode(node.x, node.y, node.attr, NodeTags(n_id, []))

    for (n_id, tag) in tags.items():
        if n_id not in result:
            raise ValueError(
                f"The node id referenced by (tag '{tag}', id: '{n_id}') was not found in the nodes."
            )

        result[n_id].tags.values = tag

    return result
