import json
import socket
import threading
import time
from typing import Dict

from network.common.data import DataNode, NodeRoutes
from network.common.networkk import Network
from network.common.utils import debug_log, debug_exception, debug_warning

BUFFER_SIZE = 1024 * 1024


class Controller:
    NAME = "Controller"

    def __init__(self,
                 host: str,
                 port: int,
                 network: Network
                 ) -> None:
        # Host and network configuration
        self.host: str = host
        self.port: int = port
        self.network: Network = network

        # Socket configuration & clients
        self.server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: Dict[DataNode, socket.socket] = {}
        self.last_ping_times: Dict[str, float] = {}

        # Threading Lock and Event
        self.lock = threading.Lock()
        self.running = threading.Event()
        self.running.set()

    def start_server(self) -> None:
        try:
            # Start the binding and socket server.
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            debug_log(self.NAME,
                      f"Controller started.")

            accept_thread = threading.Thread(target=self.accept_connections)
            heartbeat_thread = threading.Thread(target=self.check_heartbeats)

            accept_thread.start()
            heartbeat_thread.start()

        except Exception as ex:
            self.server_socket.close()
            debug_exception(self.NAME,
                            f"Controller start error: {ex}")

    def accept_connections(self) -> None:
        try:
            while self.running.is_set():
                # Accept connections
                client, address = self.server_socket.accept()
                auth: bytes = client.recv(BUFFER_SIZE)
                data_decoded: str = auth.decode("utf-8")
                data_auth: Dict = json.loads(data_decoded)
                node: DataNode = DataNode.from_json(data_auth)

                with self.lock:
                    self.clients[node] = client
                    self.last_ping_times[node.name] = time.time()

                self.add_node(node)

                debug_log(self.NAME,
                          f"Connection established with {address}")

                client_thread = threading.Thread(target=self.handle_client, args=(client, node))
                client_thread.start()

        except Exception as e:
            if self.running.is_set():
                debug_exception(self.NAME,
                                f"Error accepting connections: {e}")

    def handle_client(self, client: socket.socket, node: DataNode) -> None:
        try:
            buffer = ""
            while self.running.is_set():
                data: bytes = client.recv(BUFFER_SIZE)
                if not data:
                    break

                buffer += data.decode('utf-8')

                while True:
                    try:
                        # Try to parse the buffer as a JSON message
                        message_json, end_index = json.JSONDecoder().raw_decode(buffer)
                        buffer = buffer[end_index:].lstrip()
                        self.process_message(message_json, node)
                    except json.JSONDecodeError:
                        # Not enough data to decode a full message
                        break
        except Exception as ex:
            if self.running.is_set():
                debug_exception(self.NAME,
                                f"Error handling client {node.name}: {ex}")
        finally:
            self.close_client(client, node)

    def process_message(self, message_json: Dict, node: DataNode):
        message_type = message_json.get("type")
        if message_type == "ping":
            with self.lock:
                self.last_ping_times[node.name] = time.time()
        else:
            debug_log(self.NAME,
                      f"{node.name} sends: {message_json}")

    def check_heartbeats(self):
        while self.running.is_set():
            current_time = time.time()
            with self.lock:
                for node, last_ping in list(self.last_ping_times.items()):
                    if current_time - last_ping > 10:
                        debug_warning(self.NAME,
                                      f"Router {node} is considered disconnected.")
                        self.remove_client_by_name(node)
            time.sleep(5)

    def send_routes(self, node: DataNode) -> None:
        try:
            routes: NodeRoutes = self.network.get_routes_for(node.name)
            routes_json: str = json.dumps(routes.__dict__())
            client: socket.socket = self.clients[node]
            client.sendall(routes_json.encode('utf-8'))
        except Exception as ex:
            debug_exception(self.NAME,
                            f"Failed to send routes to {node.name}: {ex}")

    def update_routes(self):
        for node in self.clients.keys():
            self.send_routes(node)

    def close_client(self, client: socket.socket, node: DataNode) -> None:
        with self.lock:
            if client in self.clients.values():
                client.close()
                del self.clients[node]
                del self.last_ping_times[node.name]
                self.close_node(node)
            debug_warning(self.NAME,
                          f"Connection closed with {node.name}")

    def remove_client_by_name(self, node_name: str) -> None:
        with self.lock:
            for node, client in list(self.clients.items()):
                if node.name == node_name:
                    self.close_client(client, node)
                    break

    def add_node(self, node: DataNode) -> None:
        self.network.add_node(node)

    def close_node(self, node: DataNode) -> None:
        self.network.remove_node(node)
        self.update_routes()

    def add_edge(self, u, v, w):
        self.network.add_edge(u, v, w)

    def add_all_edges(self, edges):
        for (u, v, w) in edges:
            self.network.add_edge(u, v, w)

    def stop(self) -> None:
        self.running.clear()
        self.server_socket.close()
        with self.lock:
            for client in self.clients.values():
                try:
                    client.shutdown(socket.SHUT_RDWR)
                    client.close()
                except Exception as ex:
                    debug_exception(self.NAME,
                                    f"Error closing client socket: {ex}")
            self.clients.clear()

        debug_warning(self.NAME,
                      "Controller Server Stopped.")
