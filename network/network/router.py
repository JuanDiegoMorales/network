import os
import base64
import json
import socket
import threading
import time
from typing import Dict, Tuple

from network.common.data import DataNode, DataRoute, NodeRoutes, store_route, DataMessage, read_route_for, ROOT_DIR
from network.common.security import generate_symmetric_key, encrypt_message, generate_keys, serialize_key_public, \
    encrypt_symmetric_key, decrypt_symmetric_key, decrypt_message, encrypt_file, decrypt_file
from network.common.utils import debug_log, debug_warning, debug_exception

BUFFER_SIZE = 1024 * 1024


class Router:
    def __init__(self,
                 controller_host: str,
                 controller_port: int,
                 local_host: str,
                 local_port: int,
                 name: str = "NONE"
                 ) -> None:
        # Name
        self.NAME = f"Router | {name}"

        # Host and network configuration
        self.controller_host: str = controller_host
        self.controller_port: int = controller_port
        self.local_host: str = local_host
        self.local_port: int = local_port
        self.name = name

        # Socket client/server configuration and clients
        self.controller_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: Dict[Tuple[str, int], socket.socket] = {}

        # Security Keys
        self.private_key, self.public_key = generate_keys()

        # Threading Lock and Events
        self.lock = threading.Lock()
        self.running = threading.Event()
        self.running.set()

    def connect_to_controller(self) -> None:
        try:
            self.controller_socket.connect((self.controller_host, self.controller_port))
            debug_log(self.NAME,
                      f"Connected to the controller {(self.controller_host, self.controller_port)}")

            # Auth the router
            public_key = serialize_key_public(self.public_key)
            message_auth = DataNode(
                name=self.name,
                ip=self.local_host,
                port=self.local_port,
                public_key=public_key
            )
            json_message = json.dumps(message_auth.__dict__())
            self.controller_socket.sendall(json_message.encode('utf-8'))

            routes_thread = threading.Thread(target=self.routes_checker)
            heartbeat_thread = threading.Thread(target=self.send_heartbeat)

            routes_thread.start()
            heartbeat_thread.start()

        except Exception as ex:
            debug_exception(self.NAME,
                            f"Failed to connect to controller: {ex}")

    def send_heartbeat(self):
        while self.running.is_set():
            try:
                heartbeat_message = {
                    "type": "ping",
                    "name": self.name
                }
                heartbeat_json = json.dumps(heartbeat_message)
                self.controller_socket.sendall(heartbeat_json.encode('utf-8'))
            except Exception as ex:
                debug_exception(self.NAME, f"Error sending heartbeat: {ex}")
            time.sleep(5)  # Send a ping every 5 seconds

    def routes_checker(self):
        buffer = ""

        while self.running.is_set():
            try:
                data = self.controller_socket.recv(BUFFER_SIZE)
                if data:
                    try:
                        buffer += data.decode('utf-8')

                        # Intenta cargar el JSON completo
                        while buffer:
                            try:
                                routes_json = json.loads(buffer)
                                store_route(self.name, NodeRoutes.from_json(routes_json))
                                buffer = ""  # Limpia el buffer si se procesa correctamente
                            except json.JSONDecodeError as json_err:
                                if "Unterminated string" in str(json_err):
                                    # Es probable que se deba a datos incompletos, espera más datos
                                    break
                                else:
                                    # Error inesperado de JSON, limpiamos el buffer para evitar un bucle infinito
                                    buffer = ""
                                    debug_warning(self.NAME, f"Received invalid JSON. Error: {json_err}")
                            except Exception as ex:
                                debug_warning(self.NAME, f"Received empty route update.\nError: {ex}")
                    except UnicodeDecodeError as uni_err:
                        debug_warning(self.NAME, f"Failed to decode UTF-8. Error: {uni_err}")
            except Exception as ex:
                debug_exception(self.NAME, f"Error processing received routes: {ex}")

    def send_message(self, destination: str, message: str, is_file: bool = False, filedata: bytes = None):
        # Find route to destination
        route: DataRoute = read_route_for(self.name, destination)
        if not route:
            debug_warning(self.NAME,
                          f"No route found to {destination}")
            return

        # Read and encode the file if it's a file
        binary: bytes = bytes()
        if is_file and filedata:
            binary = base64.b64encode(filedata)

        # Generate symmetric key and encrypt message
        sym_key = generate_symmetric_key()
        encrypted_message = encrypt_message(message, sym_key)

        # Encrypt the binary data if it's a file
        encrypted_binary = encrypt_file(binary, sym_key) if is_file else ""

        # Get public key of last router and store next_node
        next_node: DataNode = route.paths[1]
        last_node: DataNode = route.paths[-1]
        last_router_public_key: str = last_node.public_key

        if not last_router_public_key:
            debug_warning(self.NAME,
                          f"Last Router Public Key is empty for node {last_node.name}")

        encrypted_sym_key = encrypt_symmetric_key(sym_key, last_router_public_key)

        # Send encrypted message and encrypted symmetric key to next router
        data_message = DataMessage(
            message=encrypted_message,
            path=route.paths[1:],  # Remaining path
            key=encrypted_sym_key,
            is_file=is_file,
            binary=encrypted_binary
        )
        self.send_message_client(data_message, next_node)

    def start_server(self) -> None:
        try:
            # Start the binding and socket server.
            self.server_socket.bind((self.local_host, self.local_port))
            self.server_socket.listen(5)
            debug_log(self.NAME,
                      f"Router Server started.")

            accept_thread = threading.Thread(target=self.accept_clients)
            accept_thread.start()

        except Exception as ex:
            self.server_socket.close()
            debug_exception(self.NAME,
                            f"Router Server start error: {ex}")

    def accept_clients(self):
        while self.running.is_set():
            try:
                client_socket, address = self.server_socket.accept()
                with self.lock:
                    self.clients[address] = client_socket
                debug_log(self.NAME,
                          f"Accepted connection from {address}")
                client_thread = threading.Thread(target=self.read_messages, args=(client_socket, address))
                client_thread.start()

            except Exception as ex:
                if self.running.is_set():
                    debug_exception(self.NAME,
                                    f"Error accepting clients: {ex}")

    def read_messages(self, client_socket: socket.socket, address: Tuple[str, int]):
        try:
            buffer = ""
            while self.running.is_set():
                data: bytes = client_socket.recv(BUFFER_SIZE)
                if not data:
                    debug_log(self.NAME,
                              f"Connection closed by {address}")
                    break

                buffer += data.decode('utf-8')

                while True:
                    try:
                        # Try to parse the buffer as a JSON message
                        message_json, end_index = json.JSONDecoder().raw_decode(buffer)
                        buffer = buffer[end_index:].lstrip()
                        self.process_message(message_json)
                    except json.JSONDecodeError:
                        # Not enough data to decode a full message
                        break

        except Exception as ex:
            if self.running.is_set():
                debug_exception(self.NAME,
                                f"Error Reading Messages: {ex}")
        finally:
            self.close_client(client_socket, address)

    def process_message(self, message_json: Dict):

        if not DataMessage.is_message(message_json):
            client_destination = message_json.get('destination')
            if not client_destination:
                return
            client_message = message_json.get('message', "NONE")
            client_is_file = message_json.get('is_file', False)
            client_binary_encoded = message_json.get('binary', "")

            if client_is_file:
                try:
                    client_binary = base64.b64decode(client_binary_encoded)
                except Exception as e:
                    print(f"Failed to decode binary data: {e}")
                    return
            else:
                client_binary = bytes()

            self.send_message(
                destination=client_destination,
                message=client_message,
                is_file=client_is_file,
                filedata=client_binary
            )
            return

        data_message: DataMessage = DataMessage.from_json(message_json)

        # If there's no exist a rute to destination return
        if len(data_message.path) < 1:
            debug_warning(self.NAME,
                          f"No rute found! Forbidden Message {data_message.message}")
            return

        # Check if this router is the current node in the path
        if not data_message.is_current_node(self.name):
            debug_warning(self.NAME,
                          f"Forbidden Message {data_message.message}")
            return

        # Check if this router is the final destination
        if data_message.is_destine(self.name):
            enc_message = data_message.message
            enc_sym_key = data_message.key

            sym_key = decrypt_symmetric_key(enc_sym_key, self.private_key)
            message = decrypt_message(enc_message, sym_key)
            debug_log(self.NAME,
                      f"Decrypted message: {message}")

            # Handle file message if it is a file
            if data_message.is_file:
                enc_binary = data_message.binary
                binary = decrypt_file(enc_binary, sym_key)
                decoded_message = base64.b64decode(binary)
                file_path = os.path.join(ROOT_DIR, "received", self.name, f"received_file_{message}")
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'wb') as file:
                    file.write(decoded_message)
                    debug_log(self.NAME,
                              f"File saved as {file_path}")

            for client in self.clients.values():
                message_to_client = {
                    'message': message
                }
                message_json = json.dumps(message_to_client)
                client.sendall(message_json.encode('utf-8'))

        else:
            # Get the next node before popping the current node
            next_node: DataNode = data_message.path[1] if len(data_message.path) > 1 else None
            # Pop the current node from the path
            data_message.path.pop(0)

            if not next_node:
                debug_warning(self.NAME,
                              "No next node found in the path. Message cannot be forwarded.")
                return

            self.send_message_client(data_message, next_node)

    def close_client(self, client: socket.socket, address: Tuple[str, int]) -> None:
        with self.lock:
            if client in self.clients.values():
                client.close()
                del self.clients[address]
        debug_warning(self.NAME,
                      f"Connection closed with {address}")

    def send_message_client(self, data_message: DataMessage, next_node: DataNode) -> None:
        json_message = json.dumps(data_message.__dict__())
        try:
            next_node_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            next_node_client_socket.connect((next_node.ip, next_node.port))
            next_node_client_socket.sendall(json_message.encode('utf-8'))
            debug_log(self.NAME,
                      f"Message SENT to {next_node.name}: {json_message[:15]}")
            next_node_client_socket.close()
        except Exception as ex:
            debug_exception(self.NAME,
                            f"Failed to send message to {next_node.name}: {ex}")

    def stop(self) -> None:
        self.running.clear()
        self.server_socket.close()
        try:
            self.controller_socket.shutdown(socket.SHUT_RDWR)
            self.controller_socket.close()
        except Exception as ex:
            debug_exception(self.NAME,
                            f"Error closing controller socket: {ex}")

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
                      "Router Server Stopped.")
