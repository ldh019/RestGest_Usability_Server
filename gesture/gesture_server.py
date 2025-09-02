import asyncio
import numpy as np
import joblib
from .feature_extractor import FeatureExtractor
from utils.data_logger import DataLogger
from game.config import HOST, PORT, N, CHANNELS
import socket


class GestureServer:
    def __init__(self, game, model_path):
        self.game = game
        self.svm_model = joblib.load(model_path)
        self.feature_extractor = FeatureExtractor()
        self.data_logger = DataLogger()
        self.window_counter = 0
        self.PORT = PORT
        self.HOST = self.get_local_ip()  # HOST 변수에는 실제 로컬 IP가 저장됨

    def get_local_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as temp_socket:
                temp_socket.connect(("8.8.8.8", 80))
                return temp_socket.getsockname()[0]
        except Exception:
            return "127.0.0.1"

    def process_gesture(self, prediction):
        left_gestures = ['pinchL']
        right_gestures = ['pinchR']

        if prediction in left_gestures:
            return 'LEFT'
        elif prediction in right_gestures:
            return 'RIGHT'
        return None

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print(f"Connected by {addr}")
        self.game.is_connected = True
        self.game.client_ip = addr[0]
        self.game.client_port = addr[1]

        buffer = b""

        while self.game.is_connected:
            try:
                data = await reader.read(4096)
                if not data:
                    print("Client disconnected.")
                    break
                buffer += data

                while b"[START]\n" in buffer and b"[END]\n" in buffer:
                    start_idx = buffer.find(b"[START]\n")
                    end_idx = buffer.find(b"[END]\n")

                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        block = buffer[start_idx + len(b"[START]\n"):end_idx]
                        buffer = buffer[end_idx + len(b"[END]\n"):]

                        try:
                            rows = block.decode().strip().split("\n")
                            window_data = np.array([r.split(",") for r in rows], dtype=object)

                            if window_data.shape[0] == N and window_data.shape[1] == CHANNELS:
                                self.window_counter += 1

                                if self.data_logger.experiment_name is None:
                                    experiment_name = f"user{self.game.user_number}_{self.game.condition}"
                                    self.data_logger.create_experiment_directories(experiment_name)
                                save_path = self.data_logger.save_sensor_window(window_data, self.window_counter)

                                ax, ay, az = window_data[:, 1:4].astype(float).T
                                gx, gy, gz = window_data[:, 5:8].astype(float).T
                                sensor_data = np.column_stack([ax, ay, az, gx, gy, gz])

                                features = self.feature_extractor.extract_fft_features(sensor_data)
                                prediction = self.svm_model.predict(features.reshape(1, -1))[0]

                                print(f"Predicted gesture: {prediction}")

                                gesture = self.process_gesture(prediction)
                                if gesture:
                                    self.game.add_gesture(gesture, self.window_counter)

                        except Exception as e:
                            print(f"Parse error or processing error: {e}")
                    else:
                        break

            except asyncio.IncompleteReadError:
                print("Client disconnected unexpectedly.")
                break
            except Exception as e:
                print(f"Connection error: {e}")
                break

        print(f"Connection closed with {addr}")
        self.game.on_connection_lost()
        writer.close()
        await writer.wait_closed()

    async def start_server(self):
        try:
            server = await asyncio.start_server(
                self.handle_client, '0.0.0.0', self.PORT)

            # 여기서 게임 객체의 IP를 실제 로컬 IP로 설정합니다.
            self.game.server_ip = self.HOST
            self.game.server_port = self.PORT

            addr = server.sockets[0].getsockname()
            print(f"Serving on {addr}")

            async with server:
                await server.serve_forever()

        except Exception as e:
            print(f"Server start error: {e}")
            self.game.on_connection_lost()