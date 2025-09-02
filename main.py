import socket
import numpy as np
import joblib
import os
import pandas as pd

HOST = '0.0.0.0'
PORT = 9091
fs = 400
N = 400
CHANNELS = 8

model_name = "svm_model_0628-user5-device1-table1.pkl"
svm_model = joblib.load(model_name) # 모델 경로 확인 필요
os.makedirs("received_window", exist_ok=True)
window_counter = 0

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as temp_socket:
            temp_socket.connect(("8.8.8.8", 80))
            return temp_socket.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def extract_fft_features(window, fs=400, N=400):
    features = []
    for i in range(6): # 가속도 3축, 자이로 3축
        segment = window[:, i]
        fft_vals = np.fft.rfft(segment)
        fft_mag = np.abs(fft_vals)
        freqs = np.fft.rfftfreq(N, d=1/fs)
        mask = (freqs >= 1) & (freqs <= 200)
        fft_selected = fft_mag[mask]
        fft_logged = np.log1p(fft_selected)
        features.extend(fft_logged)
    return np.array(features)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"Listening on {HOST}:{PORT}")
    print(f"Server IP: {get_local_ip()}:{PORT}")

    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        buffer = ""
        while True:
            data = conn.recv(4096).decode()
            if not data: break
            buffer += data

            while "[START]" in buffer and "[END]" in buffer:
                block = buffer.split("[START]", 1)[1].split("[END]", 1)[0]
                buffer = buffer.split("[END]", 1)[1]

                try:
                    rows = block.strip().split("\n")
                    window_data = np.array([r.split(",") for r in rows], dtype=object)

                    if window_data.shape[0] == N and window_data.shape[1] == CHANNELS:
                        accel_ts = window_data[:, 0].astype(np.int64)
                        ax, ay, az = window_data[:, 1:4].astype(float).T
                        gyro_ts = window_data[:, 4].astype(np.int64)
                        gx, gy, gz = window_data[:, 5:8].astype(float).T

                        selected_sensor_data = np.column_stack([ax, ay, az, gx, gy, gz])
                        feats = extract_fft_features(selected_sensor_data, fs, N).reshape(1, -1)

                        pred = svm_model.predict(feats)[0]
                        probs = svm_model.predict_proba(feats)[0]
                        classes = svm_model.classes_

                        print("Predicted gesture:", pred)
                        for cls, p in zip(classes, probs):
                            print(f"  {cls}: {p:.3f}")

                        df = pd.DataFrame({
                            "accel_ts": accel_ts, "ax": ax, "ay": ay, "az": az,
                            "gyro_ts": gyro_ts, "gx": gx, "gy": gy, "gz": gz
                        })
                        window_counter += 1
                        save_path = f"received_window/window_{window_counter}.csv"
                        df.to_csv(save_path, index=False)
                        print(f"Saved window to {save_path}")

                        # 샘플링 레이트 추정 (선택 사항)
                        # time_diffs = np.diff(accel_ts)
                        # mean_dt_sec = np.mean(time_diffs) / 1e9
                        # fs_est = 1.0 / mean_dt_sec
                        # print(f"Estimated sampling rate: {fs_est:.2f} Hz")

                    else:
                        print(f"Wrong window shape: {window_data.shape}")
                except Exception as e:
                    print("Parse error:", e)