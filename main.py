import socket
import numpy as np
import joblib
import matplotlib.pyplot as plt
import os
import pandas as pd

HOST = '192.168.0.7'
PORT = 9091
fs = 400           # 센서 샘플링 주파수 (Hz)
N = 400            # window 길이 (샘플 수)
CHANNELS = 8       # at, ax, ay, az, gt, gx, gy, gz

# SVM 모델 불러오기
svm_model = joblib.load("svm_model_grab.pkl")

os.makedirs("received_window", exist_ok=True)
window_counter = 0

def extract_fft_features(window, fs=400, N=400):
    features = []
    for i in range(6):
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

    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        buffer = ""

        while True:
            data = conn.recv(4096).decode()
            if not data:
                break
            buffer += data

            # START ~ END 블록 탐색
            while "[START]" in buffer and "[END]" in buffer:
                block = buffer.split("[START]", 1)[1].split("[END]", 1)[0]
                buffer = buffer.split("[END]", 1)[1]  # 남은 데이터

                try:
                    # CSV 파싱 → numpy 변환
                    rows = block.strip().split("\n")
                    window = np.array([r.split(",") for r in rows], dtype=object)

                    # 분리해서 사용
                    accel_ts = window[:, 0].astype(np.int64)  # Long 그대로
                    ax = window[:, 1].astype(float)
                    ay = window[:, 2].astype(float)
                    az = window[:, 3].astype(float)

                    gyro_ts = window[:, 4].astype(np.int64)
                    gx = window[:, 5].astype(float)
                    gy = window[:, 6].astype(float)
                    gz = window[:, 7].astype(float)

                    if window.shape[0] == N and window.shape[1] == CHANNELS:
                        # 특징 추출 (timestamps 제외하고 6축만 전달해야 한다면 window[:,1:] 사용)
                        # 분리한 채널들을 다시 합치기
                        selected = np.column_stack([ax, ay, az, gx, gy, gz])

                        # 특징 추출
                        feats = extract_fft_features(selected, fs, N).reshape(1, -1)

                        # 분류
                        pred = svm_model.predict(feats)[0]
                        print("Predicted gesture:", pred)

                        probs = svm_model.predict_proba(feats)[0]  # shape = (n_classes,)
                        classes = svm_model.classes_

                        # DataFrame 생성
                        df = pd.DataFrame({
                            "accel_ts": accel_ts,
                            "ax": ax,
                            "ay": ay,
                            "az": az,
                            "gyro_ts": gyro_ts,
                            "gx": gx,
                            "gy": gy,
                            "gz": gz
                        })

                        # 저장
                        window_counter += 1
                        os.makedirs("received_window", exist_ok=True)
                        save_path = f"received_window/window_{window_counter}.csv"
                        df.to_csv(save_path, index=False)
                        print(f"Saved window (with timestamps) to {save_path}")

                        # 확률 출력
                        for cls, p in zip(classes, probs):
                            print(f"  {cls}: {p:.3f}")

                        # 샘플링 레이트 계산
                        time_diffs = np.diff(accel_ts)  # 연속 샘플 간의 시간 차이
                        mean_dt = np.mean(time_diffs)

                        # 단위 변환 (ns인지 ms인지 확인 필요)
                        # 예: accel_ts가 ns 단위라면
                        mean_dt_sec = mean_dt / 1e9
                        fs_est = 1.0 / mean_dt_sec

                        print(f"Estimated sampling rate: {fs_est:.2f} Hz (mean Δt = {mean_dt_sec * 1000:.3f} ms)")

                        # 확인 플롯
                        plt.figure()
                        plt.plot(az, label="Accel Z")  # window[:,2] 대신 az
                        plt.xlabel("Sample")
                        plt.ylabel("Accel Z (m/s^2)")
                        plt.title(f"Gesture window (pred={pred})")
                        plt.legend()
                        plt.show()
                    else:
                        print(f"Wrong window shape: {window.shape}")
                except Exception as e:
                    print("Parse error:", e)
