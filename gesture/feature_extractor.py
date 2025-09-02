import numpy as np


class FeatureExtractor:
    def __init__(self, fs=400, N=400):
        self.fs = fs
        self.N = N

    def extract_fft_features(self, window):
        """FFT 특징 추출"""
        features = []
        for i in range(6):  # 가속도 3축, 자이로 3축
            segment = window[:, i]
            fft_vals = np.fft.rfft(segment)
            fft_mag = np.abs(fft_vals)
            freqs = np.fft.rfftfreq(self.N, d=1 / self.fs)
            mask = (freqs >= 1) & (freqs <= 200)
            fft_selected = fft_mag[mask]
            fft_logged = np.log1p(fft_selected)
            features.extend(fft_logged)
        return np.array(features)