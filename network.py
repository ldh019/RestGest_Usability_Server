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
        print(f"기기 {device_num} ({addr}) 연결됨")
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
                    print(f"기기 {device_num} ({addr}): 데이터 수신 없이 연결 종료")
                    break

                with self.connection_lock:
                    message = data.decode('utf-8').strip()
                    if message == "ACCEL_TRIGGER":
                        # 기기 번호와 메시지를 함께 큐에 추가
                        self.message_queue.append(str(device_num))

                        # 게임 시작 대기 화면을 위한 데이터 수신 상태 업데이트
                        if device_num == 1:
                            self.device1_data_received = True
                        elif device_num == 2:
                            self.device2_data_received = True

                    print(f"기기 {device_num}로부터 데이터 수신: {message}")

        except (socket.error, ConnectionResetError):
            print(f"기기 {device_num} ({addr}) 연결 끊김.")
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
            print(f"서버가 {self.server_ip}:{PORT} 에서 연결을 기다리는 중입니다.")
            return True
        except socket.error as e:
            print(f"서버 소켓 생성 실패: {e}")
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
                                threading.Thread(target=self.handle_client, args=(conn, addr, 1), daemon=True).start()
                            elif not self.device2_connected:
                                self.connections[2] = conn
                                threading.Thread(target=self.handle_client, args=(conn, addr, 2), daemon=True).start()
                            else:
                                print("최대 연결 수를 초과했습니다. 연결을 거부합니다.")
                                conn.close()
                    except socket.error as e:
                        print(f"연결 수락 오류: {e}")

    def close_server(self):
        if self.server_socket:
            self.server_socket.close()