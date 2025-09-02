import json
import pandas as pd
from datetime import datetime
import os


class DataLogger:
    def __init__(self):
        self.experiment_data = []
        os.makedirs("experiment_results", exist_ok=True)
        os.makedirs("received_window", exist_ok=True)

    def log_game_event(self, event_type, data):
        """게임 이벤트 로그"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "data": data
        }
        self.experiment_data.append(log_entry)

    def save_sensor_window(self, window_data, window_counter):
        """센서 데이터 윈도우 저장"""
        accel_ts = window_data[:, 0].astype(int)
        ax, ay, az = window_data[:, 1:4].astype(float).T
        gyro_ts = window_data[:, 4].astype(int)
        gx, gy, gz = window_data[:, 5:8].astype(float).T

        df = pd.DataFrame({
            "accel_ts": accel_ts, "ax": ax, "ay": ay, "az": az,
            "gyro_ts": gyro_ts, "gx": gx, "gy": gy, "gz": gz
        })

        save_path = f"received_window/window_{window_counter}.csv"
        df.to_csv(save_path, index=False)
        return save_path

    def save_experiment_results(self, condition):
        """실험 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"experiment_results/experiment_{condition}_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(self.experiment_data, f, indent=2)

        print(f"Experiment data saved to {filename}")
        return filename