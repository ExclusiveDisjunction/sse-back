from nodes import GraphNode, GraphEdge

from math import pow, sqrt

class Graph:
    def __init__(self, nodes: dict[int: GraphNode], edges: list[GraphEdge]):
        self.nodes = nodes
        self.edges = edges

        self.__compute_distances()
        self.__fill_edges()

    def shortest_path(self, src: int, dest: int) -> tuple[list[int], float] | None:
        pass

    def __path_reconstruct(self, src: int, dest: int, pred: dict[int: int]) -> list[int] | None:
        pass

    def __fill_edges(self):
        new_edges = []
        for edge in self.edges:
            new_edges.append(edge)
            new_edges.append(edge.reverse())

        self.edges = new_edges

    def __compute_distances(self):
        try:
            for edge in self.edges:
                source = self.nodes[edge.src]
                dest = self.nodes[edge.dest]

                dist = sqrt(pow(source.x - dest.x, 2) + pow(source.y - dest.y, 2))
                edge.weight = dist

        except Exception as e:
            raise e