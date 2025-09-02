import socket
import threading
import numpy as np
import joblib
from .feature_extractor import FeatureExtractor
from utils.data_logger import DataLogger
from game.config import HOST, PORT, N, CHANNELS


class GestureServer:
    def __init__(self, game, model_path):
        self.game = game
        self.svm_model = joblib.load(model_path)
        self.feature_extractor = FeatureExtractor()
        self.data_logger = DataLogger()
        self.window_counter = 0
        self.running = False
        self.server_socket = None
        self.PORT = PORT  # config의 기본 포트 사용

    def get_local_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as temp_socket:
                temp_socket.connect(("8.8.8.8", 80))
                return temp_socket.getsockname()[0]
        except Exception:
            return "127.0.0.1"

    def process_gesture(self, prediction):
        """제스처 예측 결과를 게임 입력으로 변환"""
        left_gestures = ['FL', 'GL', 'PL', 'TL']
        right_gestures = ['FR', 'GR', 'PR', 'TR']

        if prediction in left_gestures:
            return 'LEFT'
        elif prediction in right_gestures:
            return 'RIGHT'
        return None

    def start_server(self):
        """서버 시작"""
        self.running = True
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # get_local_ip() 함수를 사용하여 실제 로컬 IP로 바인딩
            local_ip = self.get_local_ip()
            self.server_socket.bind((local_ip, self.PORT))

            # 서버가 성공적으로 바인딩되었음을 로그에 출력
            print(f"Server bound to {local_ip}:{self.PORT}")

            self.server_socket.listen(1)

            # 메인 게임 객체에 서버 정보 업데이트
            self.game.server_ip = local_ip
            self.game.server_port = self.PORT

            self.server_socket.settimeout(1)

            # 서버 스레드가 종료되지 않고 계속해서 연결을 기다리도록 루프 추가
            while self.running:
                try:
                    conn, addr = self.server_socket.accept()
                    with conn:
                        print(f"Connected by {addr}")
                        self.game.is_connected = True
                        self.game.client_ip = addr[0]
                        self.game.client_port = addr[1]

                        buffer = ""
                        while self.running:
                            try:
                                data = conn.recv(4096).decode()
                                if not data:
                                    self.game.on_connection_lost()
                                    break
                                buffer += data

                                while "[START]" in buffer and "[END]" in buffer:
                                    block = buffer.split("[START]", 1)[1].split("[END]", 1)[0]
                                    buffer = buffer.split("[END]", 1)[1]

                                    try:
                                        rows = block.strip().split("\n")
                                        window_data = np.array([r.split(",") for r in rows], dtype=object)

                                        if window_data.shape[0] == N and window_data.shape[1] == CHANNELS:
                                            save_path = self.data_logger.save_sensor_window(
                                                window_data, self.window_counter
                                            )

                                            ax, ay, az = window_data[:, 1:4].astype(float).T
                                            gx, gy, gz = window_data[:, 5:8].astype(float).T
                                            sensor_data = np.column_stack([ax, ay, az, gx, gy, gz])

                                            features = self.feature_extractor.extract_fft_features(sensor_data)
                                            prediction = self.svm_model.predict(features.reshape(1, -1))[0]

                                            print(f"Predicted gesture: {prediction}")

                                            gesture = self.process_gesture(prediction)
                                            if gesture:
                                                self.game.add_gesture(gesture)

                                                self.data_logger.log_game_event("gesture_detected", {
                                                    "prediction": prediction,
                                                    "mapped_gesture": gesture,
                                                    "window_file": save_path
                                                })

                                    except Exception as e:
                                        print(f"Parse error: {e}")
                            except Exception as e:
                                print(f"Connection error: {e}")
                                self.game.on_connection_lost()
                                break
                except socket.timeout:
                    pass

        except Exception as e:
            if self.running:
                print(f"Server error: {e}")
            else:
                print("Server stopped cleanly.")
        finally:
            if self.server_socket:
                self.server_socket.close()

    def stop_server(self):
        """서버 중지"""
        self.running = False
        if self.server_socket:
            print("Shutting down server socket...")
            self.server_socket.close()