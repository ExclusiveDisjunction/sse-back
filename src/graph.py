"""
Provides data structures for graphs, specifically path finding.
"""

import json
from typing import Optional
import numpy as np

from nodes import DBNode

class ShortestPath:
    """Represents a specific shortest path between two nodes"""
    def __init__(self, points: list[int], dist: float):
        self.__points = points
        self.__dist = dist

    @property
    def points(self) -> list[int]:
        """Retrieves the shortest path"""
        return self.__points

    @property
    def dist(self) -> float:
        """Retrieves the total distance"""
        return self.__dist

    @staticmethod
    def from_dict(values: dict) -> Optional["ShortestPath"]:
        """Attempts to convert a dictionary into a specific class instance"""
        try:
            points = values["points"]
            dist = values["dist"]
        except KeyError:
            return None

        return ShortestPath(points, dist)

    def __lt__(self, other):
        return self.dist < other.dist
    def __eq__(self, other):
        return self.dist == other.dist
    def __repr__(self):
        return f"{self.dist} for points {self.points}"

class TableEntry:
    """Represents a specific result of the Dijkstra's table."""
    def __init__(self, n_id: int, data: ShortestPath):
        self.__n_id = n_id
        self.__data = data

    @property
    def n_id(self) -> int:
        """Gets the destination node's ID"""
        return self.__n_id

    @property
    def data(self) -> ShortestPath:
        """Gets the result of the Dijkstra's table"""
        return self.__data

    @staticmethod
    def from_list(val: list) -> "TableEntry":
        """Attempts to convert the list into an instance of TableEntry."""
        n_id = val[0]
        result = ShortestPath.from_dict(val[1])

        return TableEntry(n_id, result)

class Graph:
    """
    A central graph data structure used for least path finding.
    """
    def __init__(self, nodes: dict[int: DBNode], path: str):
        self.nodes = nodes

        self.__load_json(path)
        self.__fill_groups(nodes)

    def __fill_groups(self, nodes: dict[int: DBNode]):
        """Fills in an internal table used for quick group lookup"""
        self.groups: dict[str: list[int]] = {}
        for n_id, node in nodes.items():
            old_list = self.groups.get(node.attr.group, [])
            old_list.append(n_id)
            self.groups[node.attr.group] = old_list

    def __load_json(self, path: str):
        """Using the JSON cache created, convert the JSON into a shortest distances table."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

            self.rows = len(data)
            self.cols = len(data[0]) if self.rows != 0 else 0

            self.table = np.full((self.rows, self.cols), None, dtype=object)
            for i, row in enumerate(data):
                for j, col in enumerate(row):
                    if col is not None:
                        self.table[i, j] = TableEntry.from_list(col)

            self.col_map: dict[int: int] = {}
            if self.rows != 0:
                for (i, col) in enumerate(self.table[0]):
                    if col is not None:
                        self.col_map[col.n_id] = i

    def shortest_node_path(self, source: int, dest: int) -> Optional[TableEntry]:
        """Determines the shortest path between the `source` and `dest`, if one exists."""
        print(self.col_map)
        print(type(dest))
        try:
            # Convert from the destination to the column index.
            t_dest = self.col_map[dest]
        except KeyError:
            print(f"Key {dest} not found")
            return None

        # Out of bounds
        if source >= self.rows or t_dest >= self.cols:
            print("out of bounds")
            return None

        return self.table[source, t_dest]

    def shortest_group_path(self, source: int, dest: str) -> Optional[TableEntry]:
        """Determines the path between the `source`, and the closest node in the group `dest`."""
        try:
            # First, we need to get all nodes out of that group.
            group_ids = self.groups[dest]

            # Then we convert these node ids to column indexes
            t_node_ids = []
            for node_id in group_ids:
                mapped = self.col_map[node_id]
                if mapped > self.cols:
                    continue

                t_node_ids.append(self.col_map[node_id])
        except KeyError:
            return None

        # out of bounds
        if source >= self.rows:
            return None

        # Determines the closest node out of this table.
        min_entry: Optional[TableEntry] = None
        for dest_node in t_node_ids:
            result = self.shortest_node_path(source, dest_node)
            if result is None:
                continue

            if min_entry is None:
                min_entry = result
            else:
                if result.data.dist < min_entry.data.dist:
                    min_entry = result

        return min_entry

class TraverseRequest:
    """Represents a request to lookup shortest path"""
    def __init__(self, token: str, src: int, dest: str | int, is_group: bool):
        self.__token = token
        self.__source = src
        self.__dest = dest
        self.__is_group = is_group

    @property
    def token(self) -> str:
        """The JWT associated with the request"""
        return self.__token

    @property
    def source(self) -> int:
        """The source node"""
        return self.__source

    @property
    def dest(self) -> int | str:
        """The destination node"""
        return self.__dest

    @property
    def is_group(self) -> bool:
        """If this is false, the destination is an integer, and if this true, `dest` is a string"""
        return self.__is_group

    @staticmethod
    def from_dict(data: dict) -> Optional["TraverseRequest"]:
        """
        Attempts to extract data from a dictionary to create an instance of this class.
        If information is missing, this will return None.
        """
        try:
            token = data["token"] # string, JWT
            source = data["start"] # integer
            dest = data["end"] # str, number if is_group == "false", group name otherwise
            is_group = data["is_group"] # str "true" or "false"
        except KeyError:
            return None

        source = int(source)
        is_group = is_group == "true"
        dest = int(dest) if not is_group else str(dest)

        return TraverseRequest(token, source, dest, is_group)
