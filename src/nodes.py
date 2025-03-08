import sqlite3
from enum import Enum

from typing import Self

class NodeKind(Enum):
    Access = 0
    Path = 1
    Room = 2
    Area = 3

class Node:
    def __init__(self, n_id: int, x: float, y: float, z: int, name: str | None, group: str, kind: NodeKind, tags: list[str] = []):
        self.n_id = n_id
        self.x = x
        self.y = y
        self.z = z
        self.name = name
        self.group = group
        self.kind = kind
        self.tags = tags

    def sql_pack(self, id: bool) -> tuple[int | float | str]:
        """
        Creates a tuple that can be used for sqlite writing values. The order is:
        [n_id], x, y, z, name, group, kind
        """
        if id:
            return (
                self.n_id,
                self.x, 
                self.y,
                self.z, 
                self.name,
                self.group,
                self.kind.value
            )
        else:
            return (
                self.x, 
                self.y,
                self.z, 
                self.name,
                self.group,
                self.kind.value
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
            "kind": self.kind.value,
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
            kind = NodeKind(val["kind"])
            tags = val.get("tags", [])
        except: 
            return None
        
        # Note that Group is allowed to be none.
        if n_id is None or x is None or y is None or z is None or name is None or kind is None:
            return None
        
        if not isinstance(n_id, int) or not isinstance(x, float) or not isinstance(y, float) or not isinstance(z, int) or not isinstance(name, str):
            return None
        
        return Node(n_id, x, y, z, name, group, kind, tags)
    
class NodeTag:
    def init(self, n_id: int, tag: str):
        self.n_id = n_id
        self.tag = tag

    def sql_pack(self):
        return (
            self.n_id,
            self.tag
        )
    
    def to_dict(self) -> dict[str: str | int]:
        return {
            "n_id": self.n_id,
            "tag": self.tag
        }
    
    @staticmethod
    def from_dict(val: dict) -> Self | None: 
        try:
            n_id = val["n_id"]
            tag = val["tag"]
        except:
            return None
        
        if n_id is None or tag is None or not isinstance(n_id, int) or not isinstance(tag, str):
            return None
        
        return NodeTag(n_id, tag)
    

class Edge:
    def __init__(self, source: int, destination: int, weight: float = 0.0):
        self.source = source
        self.destination = destination
        self.weight = weight

    def __str__(self):
        return f"{self.source} -> {self.destination} (w: {self.weight})"
    def __eq__(self, other: Self) -> bool:
        return isinstance(other, Edge) and self.source == other.source and self.destination == other.destination and self.weight == other.weight

    def sql_pack(self) -> tuple[int]:
        return (
            self.source,
            self.destination
        )
    
    def to_dict(self) -> dict[str: int | float]: 
        return {
            "source": self.source,
            "destination": self.destination,
            "weight": self.weight
        }

    @staticmethod
    def from_dict(val: dict[str: int | float]) -> Self | None:
        try:
            source = val["source"]
            destination = val["destination"]
            weight = val.get("weight", 0.0)
        except:
            return None
        
        if source is None or destination is None or not isinstance(source, int) or not isinstance(destination, int):
            return None
        
        return Edge(source, destination, weight)
    
