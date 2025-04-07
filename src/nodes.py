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
    result = cur.execute("SELECT N_ID, X, Y, NODE_NAME, NODE_GROUP, IS_PATH FROM NODES")
    vals = result.fetchall()
    if vals is None:
        return None
    
    result = {}
    for val in vals:
        result[val[0]] = DBNode(val[0], GraphNode(val[1], val[2]), NodeAttributes(val[3], val[4], val[5] == 1))

    return result 

def strip_nodes(vals: dict[int, DBNode]) -> dict[int: GraphNode]:
    result = {}
    for (key, val) in vals.items():
        result[key] = val.loc

    return result 

def get_db_edges(cur: sqlite3.Cursor) -> list[GraphEdge] | None:
    result = cur.execute("SELECT SOURCE, DESTINATION FROM EDGES")
    vals = result.fetchall()
    if vals is None:
        return None
    
    result = []
    for val in vals:
        result.append(GraphEdge(val[0], val[1]))

    return result 

def get_db_node_tags(cur: sqlite3.Cursor) -> dict[int: list[str]] | None:
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

def zip_nodes_and_tags(nodes: dict[int: DBNode], tags: dict[int: list[str]]) -> dict[int: NetworkNode]:
    result: dict[int: NetworkNode] = {}
    for (id, node) in nodes.items():
        result[id] = NetworkNode(node.loc, node.attr, NodeTags(id, []))

    for (id, tag) in tags.items():
        if id not in result:
            raise ValueError(f"The node id referenced by tag '{tag}', id: '{id}' was not found in the nodes.")
        
        result[id].tags.inner.append(tag)

    return result 