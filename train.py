import joblib
import numpy as np
import pandas as pd
from sklearn.svm import SVC

# 1. 데이터 로드
df = pd.read_csv("train_data.csv")

# 2. 라벨과 피처 분리
y = df.iloc[0:, 0].values
X_raw = df.iloc[0:, 1:].values.astype(float)

print("X shape:", X_raw.shape)  # (20, 2400)
print("y shape:", y.shape)  # (20,)

# 3. FFT 변환 함수
def extract_fft_features(raw_row, fs=400, N=400):
    features = []
    # 6축 (400포인트씩)
    for i in range(6):
        segment = raw_row[i*N:(i+1)*N]  # 400길이
        fft_vals = np.fft.rfft(segment)  # half spectrum
        fft_mag = np.abs(fft_vals)

        freqs = np.fft.rfftfreq(N, d=1/fs)  # 주파수 벡터
        # 1~200Hz 구간만 선택
        mask = (freqs >= 1) & (freqs <= 200)
        fft_selected = fft_mag[mask]
        fft_logged = np.log1p(fft_selected)

        features.extend(fft_logged)
    return np.array(features)

# 4. 모든 샘플에 대해 feature 추출
X_feat = np.array([extract_fft_features(row) for row in X_raw])

print("Raw shape:", X_raw.shape)   # (20, 2400)
print("FFT feature shape:", X_feat.shape)  # (20, something)

# 4. SVM 학습
svm_model = SVC(kernel="linear", decision_function_shape="ovo")
svm_model.fit(X_feat, y)

# 6. 모델 저장
joblib.dump(svm_model, "svm_model.pkl")
print("Saved svm_model.pkl")
