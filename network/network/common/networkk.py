from typing import List
from networkx import Graph, dijkstra_path, NetworkXNoPath

from network.common.data import DataRoute, DataNode, NodeRoutes


class Network:

    def __init__(self):
        """" Initialize the network Graph """
        self.graph: Graph = Graph()

    def add_edge(self, u: str, v: str, w: int) -> None:
        """ Add an edge to the graph with a specified weight if the nodes and weight are valid. """
        if isinstance(w, int) and w > 0:
            self.graph.add_edge(u, v, weight=w)
        else:
            print(f"Invalid weight {w}; must be a positive integer.")

    def add_node(self, node: DataNode) -> None:
        """" Add nodes to the graph """
        self.graph.add_node(
            node.name,
            ip=node.ip,
            port=node.port,
            public_key=node.public_key
        )

    def remove_node(self, node: DataNode) -> None:
        """Remove a node from the graph if it exists."""
        if node.name in self.graph:
            self.graph.remove_node(node.name)
        else:
            print(f"Node {node} not found in the graph.")

    def get_all_nodes(self) -> List[str]:
        return self.graph.nodes()

    def shortest_path(self, start: str, end: str) -> list[str]:
        """Find the shortest path from start to end using Dijkstra's algorithm."""
        try:
            return dijkstra_path(self.graph, start, end)
        except NetworkXNoPath:
            print(f"No path found from {start} to {end}.")
            return []
        except Exception as ex:
            print(f"Error calculating path from {start} to {end}: {ex}")
            return []

    def node_to_datanode(self, node: str) -> DataNode:
        """"  """
        node_data = self.graph.nodes[node]

        return DataNode(
            name=node,
            ip=node_data.get("ip"),
            port=node_data.get("port"),
            public_key=node_data.get('public_key')
        )

    def _generate_data_route(self, source: str, target: str, path: List[str]) -> DataRoute:
        """"  """
        paths_data = [self.node_to_datanode(node) for node in path]
        source_data: DataNode = self.node_to_datanode(source)
        destination_data: DataNode = self.node_to_datanode(target)

        route_data: DataRoute = DataRoute(
            source=source_data,
            destination=destination_data,
            paths=paths_data
        )

        return route_data

    def get_routes_all(self) -> List[NodeRoutes]:
        """ Calculate all possible routes between all pairs of nodes. """
        all_routes = []
        for source in self.graph.nodes():
            data: NodeRoutes = self.get_routes_for(source)
            all_routes.append(data)

        return all_routes

    def get_routes_for(self, node: str) -> NodeRoutes:
        all_routes = []
        data_node: DataNode = self.node_to_datanode(node)
        for target in self.graph.nodes():
            if node != target:
                path: List[str] = self.shortest_path(node, target)
                route_data: DataRoute = self._generate_data_route(node, target, path)

                all_routes.append(route_data)

        node_routes: NodeRoutes = NodeRoutes(
            node=data_node,
            routes=all_routes
        )
        return node_routes
