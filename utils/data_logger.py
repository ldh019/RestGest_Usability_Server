import json
import os
from datetime import datetime
import numpy as np


class DataLogger:
    def __init__(self):
        self.logs = []
        self.experiment_name = None
        self.log_file_path = None
        self.sensor_data_dir = None
        self.start_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    def create_experiment_directories(self, experiment_name):
        """실험 데이터를 저장할 디렉토리 생성"""
        self.experiment_name = experiment_name
        base_dir = "experiment_results"
        exp_dir = os.path.join(base_dir, f"{self.experiment_name}_{self.start_time}")
        self.sensor_data_dir = os.path.join(exp_dir, "sensor_data")
        os.makedirs(self.sensor_data_dir, exist_ok=True)
        self.log_file_path = os.path.join(exp_dir, "event_log.json")

    def log_game_event(self, event_type, data):
        """게임 이벤트를 로그에 추가"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        self.logs.append(log_entry)

    def save_sensor_window(self, window_data, window_id):
        """센서 데이터 윈도우를 CSV 파일로 저장"""
        if self.sensor_data_dir is None:
            # 실험 디렉토리가 생성되지 않았다면, 임시로 저장
            temp_dir = "temp_sensor_data"
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, f"window_{window_id}.csv")

        else:
            file_path = os.path.join(self.sensor_data_dir, f"window_{window_id}.csv")

        np.savetxt(file_path, window_data, delimiter=",", fmt="%s")
        return file_path

    def save_experiment_results(self, experiment_name, correct_count, incorrect_count):
        """실험 결과를 JSON 파일로 저장"""
        if self.log_file_path is None:
            self.create_experiment_directories(experiment_name)

        final_data = {
            "summary": {
                "experiment_name": experiment_name,
                "start_time": self.start_time,
                "total_correct_gestures": correct_count,
                "total_incorrect_gestures": incorrect_count
            },
            "logs": self.logs
        }

        with open(self.log_file_path, 'w') as f:
            json.dump(final_data, f, indent=4)
        print(f"Experiment results saved to {self.log_file_path}")