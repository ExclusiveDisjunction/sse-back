"""
Provides data structures for graphs, specifically path finding.
"""

import json
from typing import Optional
import numpy as np

from nodes import DBNode

class DijkstraResult:
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
    def from_dict(values: dict) -> Optional["DijkstraResult"]:
        """Attempts to convert a dictionary into a specific class instance"""
        try:
            points = values["points"]
            dist = values["dist"]
        except KeyError:
            return None

        return DijkstraResult(points, dist)

    def __lt__(self, other):
        return self.dist < other.dist
    def __eq__(self, other):
        return self.dist == other.dist
    def __repr__(self):
        return f"{self.dist} for points {self.points}"

class TableEntry:
    """Represents a specific result of the Dijkstra's table."""
    def __init__(self, n_id: int, data: DijkstraResult):
        self.__n_id = n_id
        self.__data = data

    @property
    def n_id(self) -> int:
        """Gets the destination node's ID"""
        return self.__n_id

    @property
    def data(self) -> DijkstraResult:
        """Gets the result of the Dijkstra's table"""
        return self.__data

    @staticmethod
    def from_list(val: list) -> "TableEntry":
        n_id = val[0]
        result = DijkstraResult.from_dict(val[1])

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
                        self.col_map[col.n_id] = col

            print(self.table.shape)

    def shortest_node_path(self, source: int, dest: int) -> Optional[TableEntry]:
        try:
            t_dest = self.col_map[dest]
        except KeyError:
            return None

        if source >= self.rows or t_dest >= self.cols:
            return None

        return self.table[source, t_dest]

    def shortest_group_path(self, source: int, dest: str) -> Optional[TableEntry]:
        try:
            group_ids = self.groups[dest]

            t_node_ids = []
            for node_id in group_ids:
                mapped = self.col_map[node_id]
                if mapped > self.cols:
                    continue

                t_node_ids.append(self.col_map[node_id])
        except KeyError:
            return None

        if source > self.rows:
            return None

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
