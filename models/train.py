import joblib
import numpy as np
import pandas as pd
from sklearn.svm import SVC

# 1. 데이터 로드
df = pd.read_csv("train_data_200_user2_center_grab.csv")

# 2. 라벨과 피처 분리
y = df.iloc[0:, 0].values
X_raw = df.iloc[0:, 1:].values.astype(float)

print("X shape:", X_raw.shape)  # (20, 1200)
print("y shape:", y.shape)  # (20,)

# 3. FFT 변환 함수
def extract_fft_features(raw_row, fs=400, N=400):
    features = []
    # 6축 (400포인트씩)
    for i in range(6):
        segment = raw_row[i*N:(i+1)*N]  # 400길이
        fft_vals = np.fft.fft(segment)  # half spectrum
        fft_mag = np.abs(fft_vals)

        freqs = np.fft.fftfreq(N, d=1/fs)  # 주파수 벡터
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

# y를 (20,1) 로 reshape
y_col = y.reshape(-1, 1)

# y와 feature를 열 기준으로 합치기
data_with_label = np.hstack([y_col, X_feat])

print("Final shape:", data_with_label.shape)

# (20, 1 + feature_dim)

# CSV 저장
# np.savetxt("features_with_labels.csv", data_with_label, delimiter=",", fmt="%s")

# 4. SVM 학습
svm_model = SVC(kernel="linear", decision_function_shape="ovo", probability=True)
svm_model.fit(X_raw[:, :200], y)

# 6. 모델 저장
joblib.dump(svm_model, "svm_model_200_user2_center_grab_accel_x.pkl")
print("Saved svm_model.pkl")
