import csv
import os
from datetime import datetime


class ExperimentLogger:
    def __init__(self):
        self.data_folder = "experiment_data"
        self.session_data = {}
        self.game_events = []
        
        # Create data folder if it doesn't exist
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
    
    def start_session(self, user_number, condition):
        """Start a new experiment session"""
        self.session_data = {
            'user_number': user_number,
            'condition': condition,
            'session_start_time': datetime.now().isoformat(),
            'session_id': self.generate_session_id(user_number),
            'games': []
        }
        self.game_events = []
        print(f"Started experiment session: User {user_number}, Condition {condition}")
    
    def generate_session_id(self, user_number):
        """Generate unique session ID to avoid file conflicts"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"user{user_number}_{timestamp}"
    
    def start_game(self):
        """Start recording a new game"""
        game_data = {
            'game_start_time': datetime.now().isoformat(),
            'game_end_time': None,
            'duration_seconds': 0,
            'final_score': 0,
            'device1_input_count': 0,
            'device2_input_count': 0,
            'device_inputs': [],
            'game_events': []
        }
        self.current_game = game_data
        self.session_data['games'].append(game_data)
        self.game_number = len(self.session_data['games'])
        print(f"Game {self.game_number} started - logging enabled")
    
    def log_device_input(self, device_number, timestamp=None):
        """Log input from smartwatch device"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        input_data = {
            'device': device_number,
            'timestamp': timestamp,
            'game_time': self.get_game_elapsed_time()
        }
        
        if hasattr(self, 'current_game'):
            self.current_game['device_inputs'].append(input_data)
            
            # Increment device-specific counter
            if device_number == 1:
                self.current_game['device1_input_count'] += 1
            elif device_number == 2:
                self.current_game['device2_input_count'] += 1
                
            print(f"Logged device {device_number} input at game time {input_data['game_time']:.2f}s (Device {device_number} total: {self.current_game[f'device{device_number}_input_count']})")
    
    def log_game_event(self, event_type, details=None):
        """Log game events (fruit eaten, collision, etc.)"""
        if not hasattr(self, 'current_game'):
            return
            
        event_data = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'game_time': self.get_game_elapsed_time(),
            'details': details or {}
        }
        
        self.current_game['game_events'].append(event_data)
        print(f"Logged game event: {event_type}")
    
    def end_game(self, final_score, duration_seconds):
        """End the current game and save final data"""
        if not hasattr(self, 'current_game'):
            return
            
        self.current_game['game_end_time'] = datetime.now().isoformat()
        self.current_game['duration_seconds'] = duration_seconds
        self.current_game['final_score'] = final_score
        
        # Save individual game data immediately
        self.save_individual_game_data()
        
        print(f"Game {self.game_number} ended - Duration: {duration_seconds:.2f}s, Score: {final_score}")
        print(f"Device inputs: Device1={self.current_game['device1_input_count']}, Device2={self.current_game['device2_input_count']}")
    
    def get_game_elapsed_time(self):
        """Get elapsed time since game start"""
        if not hasattr(self, 'current_game') or not self.current_game['game_start_time']:
            return 0
        
        start_time = datetime.fromisoformat(self.current_game['game_start_time'])
        return (datetime.now() - start_time).total_seconds()
    
    def save_individual_game_data(self):
        """Save individual game data to CSV immediately after game ends"""
        if not self.session_data or not hasattr(self, 'current_game'):
            return
        
        session_id = self.session_data['session_id']
        game_csv_filename = os.path.join(self.data_folder, f"{session_id}_game{self.game_number}.csv")
        
        # Save individual game CSV
        with open(game_csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header with game info
            writer.writerow(['Game Information'])
            writer.writerow(['User_Number', self.session_data['user_number']])
            writer.writerow(['Condition', self.session_data['condition']])
            writer.writerow(['Session_ID', session_id])
            writer.writerow(['Game_Number', self.game_number])
            writer.writerow(['Game_Start', self.current_game['game_start_time']])
            writer.writerow(['Game_End', self.current_game['game_end_time']])
            writer.writerow(['Duration_Seconds', self.current_game['duration_seconds']])
            writer.writerow(['Final_Score', self.current_game['final_score']])
            writer.writerow(['Device1_Input_Count', self.current_game['device1_input_count']])
            writer.writerow(['Device2_Input_Count', self.current_game['device2_input_count']])
            writer.writerow([])  # Empty row
            
            # Device inputs section
            writer.writerow(['Device Inputs'])
            writer.writerow(['Device', 'Timestamp', 'Game_Time_Seconds'])
            for input_data in self.current_game['device_inputs']:
                writer.writerow([
                    input_data['device'],
                    input_data['timestamp'],
                    f"{input_data['game_time']:.3f}"
                ])
            writer.writerow([])  # Empty row
            
            # Game events section
            writer.writerow(['Game Events'])
            writer.writerow(['Event_Type', 'Game_Time_Seconds'])
            for event in self.current_game['game_events']:
                writer.writerow([
                    event['event_type'],
                    f"{event['game_time']:.3f}"
                ])
        
        # Also append to master game log
        master_game_csv = os.path.join(self.data_folder, "master_games.csv")
        self.append_game_to_master(master_game_csv)
        
        print(f"Individual game data saved: {game_csv_filename}")
    
    def append_game_to_master(self, filename):
        """Append game data to master games CSV"""
        file_exists = os.path.exists(filename)
        
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header if file is new
            if not file_exists:
                writer.writerow([
                    'User_Number', 'Condition', 'Session_ID', 'Game_Number',
                    'Game_Start', 'Game_End', 'Duration_Seconds', 'Final_Score',
                    'Device1_Input_Count', 'Device2_Input_Count', 'Total_Inputs',
                    'Fruit_Eaten_Count'
                ])
            
            # Calculate fruit eaten count
            fruit_eaten = len([e for e in self.current_game['game_events'] if e['event_type'] == 'fruit_eaten'])
            total_inputs = self.current_game['device1_input_count'] + self.current_game['device2_input_count']
            
            writer.writerow([
                self.session_data['user_number'],
                self.session_data['condition'],
                self.session_data['session_id'],
                self.game_number,
                self.current_game['game_start_time'],
                self.current_game['game_end_time'],
                self.current_game['duration_seconds'],
                self.current_game['final_score'],
                self.current_game['device1_input_count'],
                self.current_game['device2_input_count'],
                total_inputs,
                fruit_eaten
            ])
    
    def save_session_data(self):
        """Save session summary to CSV"""
        if not self.session_data:
            print("No session data to save")
            return
        
        session_id = self.session_data['session_id']
        
        # Save summary CSV file
        csv_filename = os.path.join(self.data_folder, f"{session_id}_summary.csv")
        self.save_summary_csv(csv_filename)
        
        # Append to master CSV file
        master_csv = os.path.join(self.data_folder, "experiment_master.csv")
        self.append_to_master_csv(master_csv)
        
        print(f"Session data saved:")
        print(f"  - Summary: {csv_filename}")
        print(f"  - Master log: {master_csv}")
    
    def save_summary_csv(self, filename):
        """Save game summary data to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'User_Number', 'Condition', 'Session_ID', 'Session_Start',
                'Game_Number', 'Game_Start', 'Game_End', 'Duration_Seconds',
                'Final_Score', 'Device_Inputs_Count', 'Fruit_Eaten_Count'
            ])
            
            # Data rows
            for i, game in enumerate(self.session_data['games'], 1):
                fruit_eaten = len([e for e in game['game_events'] if e['event_type'] == 'fruit_eaten'])
                
                writer.writerow([
                    self.session_data['user_number'],
                    self.session_data['condition'],
                    self.session_data['session_id'],
                    self.session_data['session_start_time'],
                    i,
                    game['game_start_time'],
                    game['game_end_time'],
                    game['duration_seconds'],
                    game['final_score'],
                    len(game['device_inputs']),
                    fruit_eaten
                ])
    
    def append_to_master_csv(self, filename):
        """Append session summary to master CSV file"""
        file_exists = os.path.exists(filename)
        
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header if file is new
            if not file_exists:
                writer.writerow([
                    'User_Number', 'Condition', 'Session_ID', 'Session_Start',
                    'Total_Games', 'Average_Duration', 'Average_Score',
                    'Total_Device_Inputs', 'Best_Score'
                ])
            
            # Calculate session statistics
            games = self.session_data['games']
            if games:
                avg_duration = sum(g['duration_seconds'] for g in games) / len(games)
                avg_score = sum(g['final_score'] for g in games) / len(games)
                total_inputs = sum(len(g['device_inputs']) for g in games)
                best_score = max(g['final_score'] for g in games)
                
                writer.writerow([
                    self.session_data['user_number'],
                    self.session_data['condition'],
                    self.session_data['session_id'],
                    self.session_data['session_start_time'],
                    len(games),
                    round(avg_duration, 2),
                    round(avg_score, 2),
                    total_inputs,
                    best_score
                ])