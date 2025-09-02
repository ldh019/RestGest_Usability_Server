import numpy as np
import pandas as pd
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# 1. CSV 불러오기
df = pd.read_csv("features_with_labels.csv")

y = df.iloc[:, 0].values           # 첫 번째 열: 라벨
X = df.iloc[:, 1:].values.astype(float)  # 나머지: 특징

print("X shape:", X.shape)  # (샘플 수, feature_dim)
print("y shape:", y.shape)

# 2. Train / Test 분할
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

# 3. SVM 모델 학습
svm_model = SVC(
    kernel="linear",
    decision_function_shape="ovo",
    C=1.0,
    probability=True
)
svm_model.fit(X_train, y_train)

# 4. 예측
y_pred = svm_model.predict(X_test)

# 5. 정확도 출력
acc = accuracy_score(y_test, y_pred)
print("Test Accuracy:", acc)

# 클래스별 리포트
print("\nClassification Report:\n", classification_report(y_test, y_pred))
