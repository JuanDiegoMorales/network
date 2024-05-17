import json
import os
from typing import List, Dict

from network.common.utils import debug_warning

ROOT_DIR: str = (
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__)
        )
    )
)


class DataNode:
    def __init__(self, name: str, ip: str, port: int, public_key: str = ""):
        self.name: str = name
        self.ip: str = ip
        self.port: int = port
        self.public_key: str = public_key

    def __dict__(self):
        return {
            "name": self.name,
            "ip": self.ip,
            "port": self.port,
            "public_key": self.public_key,
        }

    @classmethod
    def from_json(cls, data: dict):
        return cls(
            name=data["name"],
            ip=data["ip"],
            port=data["port"],
            public_key=data.get("public_key", "")
        )


class DataRoute:
    def __init__(self, source: DataNode, destination: DataNode, paths: List[DataNode]):
        self.source: DataNode = source
        self.destination: DataNode = destination
        self.paths: List[DataNode] = paths

    def __dict__(self):
        return {
            "source": self.source.__dict__(),
            "destination": self.destination.__dict__(),
            "path": [node.__dict__() for node in self.paths]
        }

    @classmethod
    def from_json(cls, json_data: Dict):
        source: DataNode = DataNode.from_json(json_data['source'])
        destination: DataNode = DataNode.from_json(json_data['destination'])
        paths: List[DataNode] = [DataNode.from_json(data) for data in json_data['path']]
        return cls(
            source=source,
            destination=destination,
            paths=paths
        )


class NodeRoutes:
    def __init__(self, node: DataNode, routes: List[DataRoute]):
        self.node: DataNode = node
        self.routes: List[DataRoute] = routes

    def __dict__(self):
        return {
            "node": self.node.__dict__(),
            "routes": [route.__dict__() for route in self.routes]
        }

    @classmethod
    def from_json(cls, json_data: Dict):
        node: DataNode = DataNode.from_json(json_data['node'])
        routes: List[DataRoute] = [DataRoute.from_json(data) for data in json_data['routes']]
        return cls(
            node=node,
            routes=routes
        )

    @classmethod
    def default(cls):
        default_node: DataNode = DataNode("Default", "None", 0, "None")
        default_routes: List[DataRoute] = []
        return cls(
            node=default_node,
            routes=default_routes
        )


class DataMessage:
    def __init__(self, message: str, path: List[DataNode], key: str = "", is_file: bool = False, binary: str = ""):
        self.message: str = message
        self.path: List[DataNode] = path
        self.key: str = key
        self.is_file: bool = is_file
        self.binary: str = binary

    def __dict__(self):
        return {
            "message": self.message,
            "path": [path.__dict__() for path in self.path],
            "key": self.key,
            "is_file": self.is_file,
            "binary": self.binary
        }

    def is_current_node(self, node: str) -> bool:
        return self.path and self.path[0].name == node

    def is_destine(self, node: str) -> bool:
        return self.path and self.path[-1].name == node

    @classmethod
    def is_message(cls, message: Dict) -> bool:
        try:
            DataMessage.from_json(message)
            return True
        except Exception:
            return False

    @classmethod
    def from_json(cls, json_data: Dict):
        message: str = json_data['message']
        path: List[DataNode] = [DataNode.from_json(data) for data in json_data['path']]
        key: str = json_data.get('key', '')
        is_file: bool = json_data.get('is_file', False)
        binary: str = json_data.get('binary', "")
        return cls(
            message=message,
            path=path,
            key=key,
            is_file=is_file,
            binary=binary
        )


def store_route(name: str, routes: NodeRoutes):
    filename: str = f"routes_{name}.json"
    file_path: str = os.path.join(ROOT_DIR, "routes", filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(routes.__dict__(), f, indent=4)


def read_route_for(name: str, destination: str):
    filename: str = f"routes_{name}.json"
    file_path: str = os.path.join(ROOT_DIR, "routes", filename)

    # Check if the file exists
    if not os.path.exists(file_path):
        debug_warning(f"DATA.PY for node: {name}",
                      f"Route file not found for {name}")
        return None

    # Read and parse the JSON file
    with open(file_path, "r") as f:
        data = json.load(f)
        node_routes: NodeRoutes = NodeRoutes.from_json(data)

    # Find the specific route to the given destination
    route: DataRoute = next((route for route in node_routes.routes if route.destination.name == destination), None)
    return route
