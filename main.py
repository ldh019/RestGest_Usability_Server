import pygame
import sys
import socket
import threading
import select
import time
import random
from screens import ScreenManager
from network import NetworkManager
from snake_game import SnakeGame
from experiment_logger import ExperimentLogger

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Usability Study GUI")

# Font settings
fonts = {
    'large': pygame.font.SysFont('malgungothic', 60),
    'medium': pygame.font.SysFont('malgungothic', 40),
    'small': pygame.font.SysFont('malgungothic', 25)
}

# Global variables
user_number = ""
condition_input = ""
current_state = "user_number_input"
selected_condition = None

# Game-related global variables
game_state = "waiting_for_data"
countdown_start_time = 0
game_start_time = 0
game_end_time = 0
game_score = 0

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    server_ip = s.getsockname()[0]
    s.close()
except socket.error:
    server_ip = "127.0.0.1"

server_port = 9090

# Create class instances
screen_manager = ScreenManager(screen, SCREEN_WIDTH, SCREEN_HEIGHT, fonts)
network_manager = NetworkManager(server_ip, server_port)
snake_game = SnakeGame(SCREEN_WIDTH, SCREEN_HEIGHT)
experiment_logger = ExperimentLogger()

# Connect logger to snake game
snake_game.logger = experiment_logger


def reset_game():
    """Function to reset game state"""
    global game_state, game_score, game_start_time, game_end_time
    snake_game.reset_game()
    game_state = "waiting_for_data"
    game_score = 0
    game_start_time = 0
    game_end_time = 0
    network_manager.device1_data_received = False
    network_manager.device2_data_received = False
    print("Game state reset.")


# Main loop
running = True
while running:
    # Snake game logic runs every frame outside the event loop
    if current_state == "snake_game" and game_state == "in_progress":
        if network_manager.message_queue:
            message = network_manager.message_queue.pop(0)
            device_num = int(message)
            print(f"Processing message from device {device_num}")  # Debug output
            # Log device input
            experiment_logger.log_device_input(device_num)
            snake_game.update_direction_from_message(message)

        # Update game state and detect collisions
        game_over = snake_game.update_game_state()
        if game_over:
            game_state = "results"
            game_end_time = time.time()
            game_score = snake_game.score
            game_duration = game_end_time - game_start_time
            # Log game end
            experiment_logger.end_game(game_score, game_duration)
            print("Game Over. Score:", game_score)

    # 이벤트 루프
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Handle mouse click events (for back, stop/restart/main menu buttons)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if screen_manager.is_back_button_clicked(mouse_pos):
                if current_state == "condition_selection":
                    current_state = "user_number_input"
                    user_number = ""
                elif current_state == "device_connection":
                    current_state = "condition_selection"
                    condition_input = ""
                elif current_state == "snake_game" and game_state == "waiting_for_data":
                    current_state = "device_connection"
                elif current_state == "snake_game" and game_state in ("in_progress", "results"):
                    current_state = "device_connection"
                    game_state = "waiting_for_data"
            elif current_state == "snake_game" and game_state == "in_progress":
                if screen_manager.is_stop_button_clicked(mouse_pos):
                    game_state = "results"
                    game_end_time = time.time()
                    game_score = snake_game.score
                    game_duration = game_end_time - game_start_time
                    # Log manual game stop
                    experiment_logger.end_game(game_score, game_duration)
                    print("Game Stopped. Score:", game_score)
            elif current_state == "snake_game" and game_state == "results":
                if screen_manager.is_restart_button_clicked(mouse_pos):
                    snake_game.reset_game()
                    current_state = "snake_game"
                    game_state = "countdown"
                    countdown_start_time = time.time()
                    # Start logging new game after restart
                    experiment_logger.start_game()
                    print("Restarting game. Countdown started.")
                elif screen_manager.is_main_menu_button_clicked(mouse_pos):
                    # Save experiment data before returning to main menu
                    experiment_logger.save_session_data()
                    current_state = "user_number_input"
                    user_number = ""
                    condition_input = ""
                    game_state = "waiting_for_data"
                    network_manager.device1_data_received = False
                    network_manager.device2_data_received = False
                    print("Returning to main menu.")

        # Handle keyboard input events
        if event.type == pygame.KEYDOWN:
            if current_state == "user_number_input":
                if event.unicode.isdigit():
                    user_number += event.unicode
                elif event.key >= pygame.K_KP0 and event.key <= pygame.K_KP9:
                    num_char = str(event.key - pygame.K_KP0)
                    user_number += num_char
                elif event.key == pygame.K_BACKSPACE:
                    user_number = user_number[:-1]
                elif event.key == pygame.K_SPACE and user_number:
                    print(f"User number: {user_number}")
                    current_state = "condition_selection"

            elif current_state == "condition_selection":
                if event.unicode in ('1', '2'):
                    condition_input = event.unicode
                elif event.key == pygame.K_BACKSPACE:
                    condition_input = ""
                elif event.key == pygame.K_SPACE and condition_input:
                    if condition_input == '1':
                        selected_condition = "Condition 1"
                    elif condition_input == '2':
                        selected_condition = "Condition 2"
                    print(f"Selected condition: {selected_condition}")
                    current_state = "device_connection"
                    # Start experiment session
                    experiment_logger.start_session(user_number, selected_condition)
                    if network_manager.server_socket is None:
                        network_manager.start_server()

            elif current_state == "device_connection":
                if network_manager.device1_connected and network_manager.device2_connected and event.key == pygame.K_SPACE:
                    current_state = "snake_game"
                    game_state = "waiting_for_data"
                    network_manager.device1_data_received = False
                    network_manager.device2_data_received = False
                    print("Game pre-start phase initiated. Waiting for data from devices.")

            elif current_state == "snake_game" and game_state == "in_progress":
                snake_game.update_direction_from_keyboard(event.key)

            elif current_state == "snake_game" and game_state == "results":
                if event.key == pygame.K_ESCAPE:
                    running = False

    # Draw screens
    if current_state == "user_number_input":
        screen_manager.draw_user_number_input(user_number)
    elif current_state == "condition_selection":
        screen_manager.draw_condition_selection(condition_input)
    elif current_state == "device_connection":
        screen_manager.draw_device_connection(
            network_manager.server_ip,
            network_manager.server_port,
            network_manager.device1_connected,
            network_manager.device2_connected
        )
        if network_manager.server_socket is not None:
            network_manager.accept_connections()
    elif current_state == "snake_game":
        if game_state == "waiting_for_data":
            screen_manager.draw_waiting_for_data(
                network_manager.device1_data_received,
                network_manager.device2_data_received
            )
            # Check if both devices have sent data, then start countdown
            if network_manager.device1_data_received and network_manager.device2_data_received:
                game_state = "countdown"
                countdown_start_time = time.time()
                # Start logging new game
                experiment_logger.start_game()
                print("Both devices sent data. Starting countdown.")
        elif game_state == "countdown":
            countdown_time = max(0, int(3 - (time.time() - countdown_start_time) + 0.5))
            screen_manager.draw_countdown(countdown_time)
            if countdown_time <= 0:
                game_state = "in_progress"
                game_start_time = time.time()
                snake_game.reset_game()
        elif game_state == "in_progress":
            snake_game.draw_game(screen, screen_manager)
        elif game_state == "results":
            game_duration = game_end_time - game_start_time
            screen_manager.draw_results(game_duration, game_score)

    pygame.display.flip()
    pygame.time.Clock().tick(snake_game.speed)

network_manager.close_server()
pygame.quit()
sys.exit()