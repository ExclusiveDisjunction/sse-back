import sqlite3
from enum import Enum

from typing import Self

class GraphNode:
    def __init__(self, x:float, y: float):
        self.x = x
        self.y = y

    def __str__(self):
        return f"({self.x}, {self.y})"
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y 
    
class GraphEdge:
    def __init__(self, src: int, dest: int, weight: float = 0):
        self.src = src
        self.dest = dest
        self.weight = weight

    def __str__(self):
        return f"{self.src} -({self.weight})-> {self.dest}"
    
    def __eq__(self, other):
        return self.src == other.src and self.dest == other.dest and self.weight == other.weight
    
    def reverse(self) -> Self:
        return GraphEdge(self.dest, self.src, self.weight)

class NodeAttributes:
    def __init__(self, name: str, group: str | None, is_path: bool):
        self.name = name
        self.group = group
        self.is_path = is_path

class DBNode:
    def __init__(self, n_id: int, loc: GraphNode, attr: NodeAttributes):
        self.n_id = n_id 
        self.loc = loc
        self.attr = attr

    def __sql_pack(self, include_id: bool) -> tuple:
        if include_id:
            return (
                self.n_id,
                self.loc.x,
                self.loc.y,
                self.attr.name,
                self.attr.group,
                1 if self.attr.is_path else 0
            )
        else:
            return (
                self.loc.x,
                self.loc.y,
                self.attr.name,
                self.attr.group,
                1 if self.attr.is_path else 0
            )

    def insert_db(self, cur: sqlite3.Cursor) -> bool:
        try:
            cur.execute("INSERT INTO NODES(X, Y, NODE_NAME, NODE_GROUP, IS_PATH) VALUES (?, ?, ?, ?, ?)", self.__sql_pack(False))
            return True 
        except Exception as e:
            print(f"[ERROR] Unable to insert node because '{e}'")
            return False

    def update_db(self, cur: sqlite3.Cursor) -> bool:
        try:
            cur.execute("UPDATE NODES SET X=?, Y=?, NODE_NAME=?, NODE_GROUP=?, IS_PATH=? WHERE N_ID=?", self.__sql_pack(False) + self.n_id)
            return True 
        except Exception as e:
            print(f"[ERROR] Unable to update node because '{e}'")
            return False

    def delete_db(self, cur: sqlite3.Cursor) -> bool:
        try:
            cur.execute("DELETE FROM NODES WHERE N_ID=?", (self.n_id))
            return True
        except Exception as e:
            print(f"[ERROR] Unable to delete node because '{e}'")
            return False

class NodeTags:
    def __init__(self, n_id: int, tags: list[str]):
        self.n_id = n_id
        self.inner = tags

    def to_list(self) -> list[str]:
        self.inner

class NetworkNode:
    def __init__(self, loc: GraphNode, attr: NodeAttributes, tags: NodeTags):
        self.loc = loc
        self.attr = attr
        self.tags = tags

    def to_dict(self) -> dict:
        return {
            "x": self.loc.x, # float
            "y": self.loc.y, # float
            "name": self.attr.name, # str
            "group": self.attr.group, # str?
            "is_path": self.attr.is_path, # bool
            "tags": self.tags.to_list() # [str]
        }

def get_db_nodes(cur: sqlite3.Cursor) -> dict[int: DBNode] | None:
    pass

def strip_nodes(vals: dict[int, NetworkNode]) -> dict[int: GraphNode]:
    result = {}
    for (key, val) in vals.items():
        result[key] = val.loc

    return result 

def get_db_edges(cur: sqlite3.Cursor) -> list[GraphEdge] | None:
    pass

def get_db_node_tags(cur: sqlite3.Cursor) -> dict[int: str] | None:
    pass

def zip_nodes_and_tags(nodes: dict[int: DBNode], tags: dict[int: str]) -> dict[int: NetworkNode]:
    result: dict[int: NetworkNode] = {}
    for (id, node) in nodes.items():
        result[id] = NetworkNode(node.loc, node.attr, NodeTags(id, []))

    for (id, tag) in tags.items():
        if id not in result:
            raise ValueError(f"The node id referenced by tag '{tag}', id: '{id}' was not found in the nodes.")
        
        result[id].tags.inner.append(tag)

    return result 

"""
class Node:
    def __init__(self, n_id: int, x: float, y: float, z: int, name: str, group: str | None, is_path: bool, tags: list[str] = []):
        self.n_id = n_id
        self.x = x
        self.y = y
        self.z = z
        self.name = name
        self.group = group
        self.is_path = is_path 
        self.tags = tags

    def sql_pack(self, id: bool) -> tuple[int | float | str]:
        
        Creates a tuple that can be used for sqlite writing values. The order is:
        [n_id], x, y, z, name, group, kind
        
        if id:
            return (
                self.n_id,
                self.x, 
                self.y,
                self.z, 
                self.name,
                self.group,
                1 if self.is_path else 0
            )
        else:
            return (
                self.x, 
                self.y,
                self.z, 
                self.name,
                self.group,
                1 if self.is_path else 0 
            )
        
    def __str__(self):
        return f"Node: (x: {self.x}, y: {self.y}, floor: {self.z}) \"{self.name}\""
    
    def __eq__(self, other: Self) -> bool:
        return isinstance(other, Node) and self.n_id == other.n_id and self.x == other.x and self.y == other.y and self.z == other.z and self.name == other.name and self.group == other.group and self.kind == other.kind 
    
    def to_dict(self) -> dict:
        return {
            "n_id": self.n_id,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "name": self.name,
            "group": self.group,
            "is_path": self.is_path,
            "tags": self.tags
        }
    
    @staticmethod
    def from_dict(val: dict):
        try:
            n_id = val["n_id"]
            x = val["x"]
            y = val["y"]
            z = val["z"]
            name = val["name"]
            group = val["group"]
            kind = val["kind"] == 1
            tags = val.get("tags", [])
        except: 
            return None
        
        # Note that Group is allowed to be none.
        if n_id is None or x is None or y is None or z is None or name is None or kind is None:
            return None
        
        if not isinstance(n_id, int) or not isinstance(x, float) or not isinstance(y, float) or not isinstance(z, int) or not isinstance(name, str):
            return None
        
        return Node(n_id, x, y, z, name, group, kind, tags)
    
"""