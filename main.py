import pygame
import sys
import socket
import threading
import select
import time
from screens import ScreenManager
from network import NetworkManager

# Pygame 초기화
pygame.init()

# 화면 설정
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Usability Study GUI")

# 폰트 설정
fonts = {
    'large': pygame.font.SysFont('malgungothic', 60),
    'medium': pygame.font.SysFont('malgungothic', 40),
    'small': pygame.font.SysFont('malgungothic', 25)
}

# 전역 변수
user_number = ""
condition_input = ""
current_state = "user_number_input"
selected_condition = None

# 게임 관련 전역 변수
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

# 클래스 인스턴스 생성
screen_manager = ScreenManager(screen, SCREEN_WIDTH, SCREEN_HEIGHT, fonts)
network_manager = NetworkManager(server_ip, server_port)

# 메인 루프
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # 마우스 클릭 이벤트 처리 (뒤로가기, 게임 중단/다시하기/메인으로 버튼용)
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
                    game_score = int(game_end_time - game_start_time)
                    print("Game Stopped. Score:", game_score)
            elif current_state == "snake_game" and game_state == "results":
                if screen_manager.is_restart_button_clicked(mouse_pos):
                    current_state = "snake_game"
                    game_state = "countdown"
                    countdown_start_time = time.time()
                    print("Restarting game. Countdown started.")
                elif screen_manager.is_main_menu_button_clicked(mouse_pos):
                    current_state = "user_number_input"
                    user_number = ""
                    condition_input = ""
                    game_state = "waiting_for_data"
                    network_manager.device1_data_received = False
                    network_manager.device2_data_received = False
                    print("Returning to main menu.")

        if current_state == "user_number_input":
            if event.type == pygame.KEYDOWN:
                if event.unicode.isdigit():
                    user_number += event.unicode
                elif event.key >= pygame.K_KP0 and event.key <= pygame.K_KP9:
                    num_char = str(event.key - pygame.K_KP0)
                    user_number += num_char
                elif event.key == pygame.K_BACKSPACE:
                    user_number = user_number[:-1]
                elif event.key == pygame.K_SPACE and user_number:
                    print(f"사용자 번호: {user_number}")
                    current_state = "condition_selection"

        elif current_state == "condition_selection":
            if event.type == pygame.KEYDOWN:
                if event.unicode in ('1', '2'):
                    condition_input = event.unicode
                elif event.key == pygame.K_BACKSPACE:
                    condition_input = ""
                elif event.key == pygame.K_SPACE and condition_input:
                    if condition_input == '1':
                        selected_condition = "Condition 1"
                    elif condition_input == '2':
                        selected_condition = "Condition 2"
                    print(f"선택된 조건: {selected_condition}")
                    current_state = "device_connection"
                    if network_manager.server_socket is None:
                        network_manager.start_server()

        elif current_state == "device_connection":
            if network_manager.device1_connected and network_manager.device2_connected and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    current_state = "snake_game"
                    game_state = "waiting_for_data"
                    network_manager.device1_data_received = False
                    network_manager.device2_data_received = False
                    print("Game pre-start phase initiated. Waiting for data from devices.")

        elif current_state == "snake_game":
            if game_state == "waiting_for_data":
                if network_manager.device1_data_received and network_manager.device2_data_received:
                    game_state = "countdown"
                    countdown_start_time = time.time()
                    print("Data received from both devices. Countdown started.")

            elif game_state == "countdown":
                countdown_time = int(3 - (time.time() - countdown_start_time) + 0.5)
                if countdown_time <= 0:
                    game_state = "in_progress"
                    game_start_time = time.time()
                    print("Game started!")

            elif game_state == "in_progress":
                pass

            elif game_state == "results":
                pass

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
        elif game_state == "countdown":
            # 1 아래로 내려가지 않도록 수정
            countdown_time = max(1, int(3 - (time.time() - countdown_start_time) + 0.5))
            screen_manager.draw_countdown(countdown_time)
            # 0이 되었을 때 바로 시작
            if countdown_time <= 0:
                game_state = "in_progress"
                game_start_time = time.time()
        elif game_state == "in_progress":
            screen_manager.draw_in_progress()
        elif game_state == "results":
            game_duration = game_end_time - game_start_time
            screen_manager.draw_results(game_duration, game_score)

    pygame.display.flip()

network_manager.close_server()
pygame.quit()
sys.exit()