# main.py

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

# 전역 변수 (이제 대부분 클래스 인스턴스에 포함)
user_number = ""
condition_input = ""
current_state = "user_number_input"
selected_condition = None

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    server_ip = s.getsockname()[0]
    s.close()
except socket.error:
    server_ip = "127.0.0.1"

server_port = 8080

# 클래스 인스턴스 생성
screen_manager = ScreenManager(screen, SCREEN_WIDTH, SCREEN_HEIGHT, fonts)
network_manager = NetworkManager(server_ip, server_port)

# 메인 루프
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # 마우스 클릭 이벤트 처리 (뒤로가기 버튼용)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            back_button_rect = pygame.Rect(30, 30, 150, 50)
            if back_button_rect.collidepoint(mouse_pos):
                if current_state == "condition_selection":
                    current_state = "user_number_input"
                    user_number = ""  # 사용자 번호 초기화
                elif current_state == "device_connection":
                    current_state = "condition_selection"
                    condition_input = ""  # 조건 선택 초기화
                elif current_state == "snake_game":
                    current_state = "device_connection"

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

        elif current_state == "snake_game":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

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
        screen_manager.draw_snake_game()

    pygame.display.flip()

# 메인 루프 종료 시 서버 소켓 닫기
network_manager.close_server()
pygame.quit()
sys.exit()