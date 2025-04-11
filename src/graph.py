"""
Provides data structures for graphs, specifically path finding.
"""

from math import sqrt
import heapq
from typing import Optional

from nodes import GraphNode, GraphEdge

class Graph:
    """
    A central graph data structure used for least path finding.
    """
    def __init__(self, nodes: dict[int: GraphNode], edges: list[GraphEdge]):
        self.nodes = nodes
        self.edges = edges

        self.__compute_distances()
        self.__fill_edges()

    def shortest_path(self, source: int, dest: int) -> tuple[list[int], float] | None:
        """
        Computes the shortest distance between `source` and `dest` using Dijkstra's algorithm.
        This returns the path taken, as well as the distance. 
        If an error occurs, this returns `None`.
        """
        if source == dest:
            return (0, [])

        # Dist is the distances table, pred is who came before,
        # and visited is used to ensure that the same node is not viewed twice.
        dist: dict[int, float] = {node_id: float('inf') for node_id in self.nodes}
        pred: dict[int, Optional[int]] = {node_id: None for node_id in self.nodes}
        visited: dict[int, bool] = {node_id: False for node_id in self.nodes}

        # Kick start with source
        dist[source] = 0

        # Optimal Dijkstra's uses a hash map.
        # The heapq library provides this functionality.
        # The tuple's first element is the current distance, the int is the NodeID.
        pq: list[tuple[float, int]] = []
        heapq.heappush(pq, (0, source))

        while len(pq) != 0:
            # Get the least distance node
            (_, u) = heapq.heappop(pq)

            if u == dest:
                # We finished! Yay
                return (dist.get(u, 0), self.__path_reconstruct(source, dest, pred))

            if visited.get(u, False):
                continue

            visited[u] = True

            for edge in self.edges:
                # Only care about nodes that have a start of our current node, optimzation
                if edge.start != u:
                    continue

                v = edge.dest
                weight = edge.weight

                if visited[v]:
                    continue

                # Update distances
                if dist[u] != float('inf') and dist[u] + weight < dist[v]:
                    dist[v] = dist[u] + weight
                    pred[v] = u
                    heapq.heappush(pq, (dist[v], v))

        return None

    def __path_reconstruct(self, src: int, dest: int, pred: dict[int: int]) -> list[int] | None:
        """
        Computes the path taken between `src` and `dest`. 
        """
        path = []
        v = dest
        # Follow the path in reverse, and then reverse it.
        while v != src and v is not None:
            path.append(v)
            v = pred.get(v, None)

        if v is None:
            return None

        path.append(src)
        path.reverse()
        return path

    def __fill_edges(self):
        """
        Since the graph is initially directed, 
        we call `GraphEdge.reverse()` to make the graph undirected.
        """
        new_edges = []
        for edge in self.edges:
            new_edges.append(edge)
            new_edges.append(edge.reverse())

        self.edges = new_edges

    def __compute_distances(self):
        """
        Computes the distances between all nodes, using their connections. 
        Stores these in the `GraphEdge.weight`.
        """
        try:
            for edge in self.edges:
                source = self.nodes[edge.src]
                dest = self.nodes[edge.dest]

                dist = sqrt(pow(source.x - dest.x, 2) + pow(source.y - dest.y, 2))
                edge.weight = dist

        except KeyError as e:
            raise e
