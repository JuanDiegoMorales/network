import base64
import socket
import json

from network.common.data import DataMessage


class Client:
    def __init__(self,
                 router_host: str,
                 router_port: int
                 ) -> None:
        # Client network configuration
        self.router_host: str = router_host
        self.router_port: int = router_port
        self.client: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self) -> None:
        try:
            self.client.connect((self.router_host, self.router_port))
            print(f"Connected to the Router {self.router_host}:{self.router_port}")
        except Exception as ex:
            print(f"Failed to connect to the router: {ex}")
            if self.client:
                self.client.close()

    def send_message(self, destination: str, message: str, is_file: bool = False, binary: bytes = bytes()) -> None:
        try:
            if is_file:
                binary_data_encoded = base64.b64encode(binary).decode('utf-8')
            else:
                binary_data_encoded = ""

            client_message = {
                'destination': destination,
                'message': message,
                'is_file': is_file,
                'binary': binary_data_encoded
            }

            json_data = json.dumps(client_message)
            self.client.sendall(json_data.encode('utf-8'))
            print(f"Message sent to {destination} -> {message}")
        except Exception as ex:
            print(f"Failed to send message: {ex}")

    def receive_message(self):
        try:
            data = self.client.recv(1024).decode('utf-8')
            data_loaded = json.loads(data)
            print(data_loaded)
        except Exception as e:
            print(f"Failed to receive message: {e}")

    def stop(self):
        if self.client:
            self.client.close()
            print("Client Stopped.")
