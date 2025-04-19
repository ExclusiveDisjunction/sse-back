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

class GraphError(Exception):
    """An error that can be made with loading the graph."""
    def __init__(self, message, inner_error):
        super().__init__(message)

        self.inner = inner_error

    def __repr__(self):
        return f"The graph could not be loaded because of '{self.inner}'"

    def __str__(self):
        return self.__repr__()

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
        try:
            f = open(path, "r", encoding="utf-8")
        except FileNotFoundError as e:
            print(f"The file at path '{path}' could not be found. '{e}'")
            raise GraphError("file not found", e) from e
        except PermissionError as e:
            print(f"The program lacks the proper permissions to open this file. '{e}'")
            raise GraphError("permission error", e) from e
        except OSError as e:
            print(f"Unable to open the file at path '{path}', with error '{e}'")
            raise GraphError("OS error", e) from e

        data = json.load(f)

        self.rows = len(data)
        self.cols = len(data[0]) if self.rows != 0 else 0

        self.table = np.full((self.rows, self.cols), None, dtype=object)
        for i, row in enumerate(data):
            for j, col in enumerate(row):
                if col is not None:
                    self.table[i, j] = ShortestPath.from_dict(col)

    def shortest_node_path(self, source: int, dest: int) -> Optional[ShortestPath]:
        """Determines the shortest path between the `source` and `dest`, if one exists."""
        # Out of bounds
        if source >= self.rows or dest >= self.cols:
            print(f"The index {source} greater than rows, or {dest} is greater than columns.")
            return None

        return self.table[source, dest]

    def shortest_group_path(self, source: int, dest: str) -> Optional[ShortestPath]:
        """Determines the path between the `source`, and the closest node in the group `dest`."""
        try:
            # First, we need to get all nodes out of that group.
            group_ids = self.groups[dest]
        except KeyError:
            print(f"The destination group {dest} could not be resolved.")
            return None

        # out of bounds
        if source >= self.rows:
            print(f"The source index {source} is invalid.")
            return None

        # Determines the closest node out of this table.
        min_entry: Optional[ShortestPath] = None
        for dest_node in group_ids:
            result = self.shortest_node_path(source, dest_node)
            if result is None:
                continue

            if min_entry is None:
                min_entry = result
            else:
                if result.dist < min_entry.dist:
                    min_entry = result

        return min_entry

class TraverseRequest:
    """Represents a request to lookup shortest path"""
    def __init__(self, token: str, src: int, dest: str | int, is_group: bool):
        self.__token = token
        self.__source = src
        self.__dest = dest
        self.__is_group = is_group

    def __repr__(self) -> str:
        return f"{self.source} to {self.dest} (is_group? {self.is_group})"

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
            print("Key error")
            return None

        source = int(source)
        try:
            if not is_group:
                dest = int(dest)
        except ValueError as e:
            print(f"Value convert error '{e}'")
            return None

        return TraverseRequest(token, source, dest, is_group)
