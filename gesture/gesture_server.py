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
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen(1)
            print(f"Gesture server listening on {self.get_local_ip()}:{PORT}")

            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                buffer = ""

                while self.running:
                    try:
                        data = conn.recv(4096).decode()
                        if not data:
                            break
                        buffer += data

                        while "[START]" in buffer and "[END]" in buffer:
                            block = buffer.split("[START]", 1)[1].split("[END]", 1)[0]
                            buffer = buffer.split("[END]", 1)[1]

                            try:
                                rows = block.strip().split("\n")
                                window_data = np.array([r.split(",") for r in rows], dtype=object)

                                if window_data.shape[0] == N and window_data.shape[1] == CHANNELS:
                                    # 센서 데이터 저장
                                    self.window_counter += 1
                                    save_path = self.data_logger.save_sensor_window(
                                        window_data, self.window_counter
                                    )

                                    # 특징 추출 및 예측
                                    ax, ay, az = window_data[:, 1:4].astype(float).T
                                    gx, gy, gz = window_data[:, 5:8].astype(float).T
                                    sensor_data = np.column_stack([ax, ay, az, gx, gy, gz])

                                    features = self.feature_extractor.extract_fft_features(sensor_data)
                                    prediction = self.svm_model.predict(features.reshape(1, -1))[0]

                                    print(f"Predicted gesture: {prediction}")

                                    # 게임에 제스처 전달
                                    gesture = self.process_gesture(prediction)
                                    if gesture:
                                        self.game.add_gesture(gesture)

                                        # 로깅
                                        self.data_logger.log_game_event("gesture_detected", {
                                            "prediction": prediction,
                                            "mapped_gesture": gesture,
                                            "window_file": save_path
                                        })

                            except Exception as e:
                                print(f"Parse error: {e}")

                    except Exception as e:
                        print(f"Connection error: {e}")
                        break

    def stop_server(self):
        """서버 중지"""
        self.running = False