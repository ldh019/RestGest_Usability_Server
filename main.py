import socket
import numpy as np
import joblib  # 저장된 SVM 로드용 (scikit-learn)

HOST = '192.168.0.7'
PORT = 9090
fs = 400           # 센서 샘플링 주파수 (Hz)
N = 400            # window 길이 (샘플 수)
CHANNELS = 6       # ax, ay, az, gx, gy, gz

# SVM 모델 불러오기
svm_model = joblib.load("svm_model.pkl")

def extract_fft_features(window, fs=400, N=400):
    features = []
    for i in range(CHANNELS):
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
                    window = np.array([list(map(float, r.split(","))) for r in rows])

                    if window.shape[0] == N and window.shape[1] == CHANNELS:
                        # 특징 추출
                        feats = extract_fft_features(window, fs, N).reshape(1, -1)

                        # 분류
                        pred = svm_model.predict(feats)[0]
                        print("Predicted gesture:", pred)
                    else:
                        print(f"Wrong window shape: {window.shape}")
                except Exception as e:
                    print("Parse error:", e)
