import socket
import threading
import select
import time
import queue


class NetworkManager:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_socket = None
        self.connections = {}
        self.connection_lock = threading.Lock()
        self.device1_connected = False
        self.device2_connected = False
        self.device1_data_received = False
        self.device2_data_received = False
        self.message_queue = []

    def handle_client(self, conn, addr, device_num):
        print(f"Device {device_num} ({addr}) connected")
        with self.connection_lock:
            if device_num == 1:
                self.device1_connected = True
            elif device_num == 2:
                self.device2_connected = True
        try:
            while True:
                ready_to_read, _, _ = select.select([conn], [], [], 1.0)
                if not ready_to_read:
                    continue
                data = conn.recv(1024)
                if not data:
                    print(f"Device {device_num} ({addr}): Connection closed without data reception")
                    break

                with self.connection_lock:
                    message = data.decode('utf-8').strip()
                    if message == "[TOUCH]":
                        self.message_queue.append(str(device_num))
                        print(f"Added device {device_num} to message queue")  # Debug output

                        if device_num == 1:
                            self.device1_data_received = True
                        elif device_num == 2:
                            self.device2_data_received = True

                    print(f"Data received from device {device_num}: {message}")

        except (socket.error, ConnectionResetError):
            print(f"Device {device_num} ({addr}) connection lost.")
        finally:
            with self.connection_lock:
                if device_num == 1:
                    self.device1_connected = False
                elif device_num == 2:
                    self.device2_connected = False
                if conn in self.connections.values():
                    for key, value in list(self.connections.items()):
                        if value == conn:
                            del self.connections[key]
                            break
                conn.close()

    def start_server(self):
        HOST = ''
        PORT = self.server_port
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setblocking(False)
            self.server_socket.bind((HOST, PORT))
            self.server_socket.listen(2)
            print(f"Server waiting for connections at {self.server_ip}:{PORT}.")
            return True
        except socket.error as e:
            print(f"Server socket creation failed: {e}")
            return False

    def accept_connections(self):
        if self.server_socket:
            input_sockets = [self.server_socket]
            readable, _, _ = select.select(input_sockets, [], [], 0.0)
            for sock in readable:
                if sock == self.server_socket:
                    try:
                        conn, addr = self.server_socket.accept()
                        with self.connection_lock:
                            if not self.device1_connected:
                                self.connections[1] = conn
                                print(f"Assigning {addr} as DEVICE 1")  # Debug output
                                threading.Thread(target=self.handle_client, args=(conn, addr, 1), daemon=True).start()
                            elif not self.device2_connected:
                                self.connections[2] = conn
                                print(f"Assigning {addr} as DEVICE 2")  # Debug output
                                threading.Thread(target=self.handle_client, args=(conn, addr, 2), daemon=True).start()
                            else:
                                print("Maximum connections exceeded. Connection refused.")
                                conn.close()
                    except socket.error as e:
                        print(f"Connection accept error: {e}")

    def close_server(self):
        if self.server_socket:
            self.server_socket.close()
