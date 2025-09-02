import numpy as np

# 파일 경로
python_csv = "features_with_labels.csv"   # Python에서 만든 CSV
matlab_csv = "compare_fft.csv"           # MATLAB에서 만든 CSV

# 1. CSV 로드 (라벨이 문자열일 수 있으므로 dtype=str)
py_data = np.loadtxt(python_csv, delimiter=",", dtype=str)
mat_data = np.loadtxt(matlab_csv, delimiter=",", dtype=str)

py_data = np.loadtxt(python_csv, delimiter=",", dtype=str, skiprows=1)
mat_data = np.loadtxt(matlab_csv, delimiter=",", dtype=str, skiprows=1)

print("Python CSV shape:", py_data.shape)
print("MATLAB CSV shape:", mat_data.shape)

# 2. 라벨과 피처 분리
labels_py = py_data[:, 0]
labels_mat = mat_data[:, 0]

X_py = py_data[:, 1:].astype(float)
X_mat = mat_data[:, 1:].astype(float)

print("X_py shape:", X_py.shape)
print("X_mat shape:", X_mat.shape)

# 3. 라벨 비교
if np.array_equal(labels_py, labels_mat):
    print("✅ Labels are identical")
else:
    print("⚠️ Labels differ")
    # 차이가 나는 위치 출력
    diff_idx = np.where(labels_py != labels_mat)[0]
    print("Different labels at indices:", diff_idx)

# 4. 수치 비교
diff = np.abs(X_py - X_mat)
print("Mean abs diff:", diff.mean())
print("Max abs diff:", diff.max())

# 5. 허용 오차 내에서 동일한지 검사
if np.allclose(X_py, X_mat, atol=1e-6):
    print("✅ Features are equal within tolerance")
else:
    print("⚠️ Features differ beyond tolerance")

# 6. 특정 샘플 상세 비교 (예: 첫 번째 샘플)
sample_idx = 0
print("\n--- Sample comparison (index 0) ---")
print("Python feats (first 10):", X_py[sample_idx, :10])
print("MATLAB feats (first 10):", X_mat[sample_idx, :10])
print("Diff (first 10):", diff[sample_idx, :10])
