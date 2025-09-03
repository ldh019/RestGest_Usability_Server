import pygame
import sys
import socket
import threading
import select
import time

# Pygame 초기화
pygame.init()

# 화면 설정
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Usability Study GUI")

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# 폰트 설정
font_large = pygame.font.SysFont('malgungothic', 60)
font_medium = pygame.font.SysFont('malgungothic', 40)
font_small = pygame.font.SysFont('malgungothic', 25)

# 전역 변수
user_number = ""
condition_input = ""
current_state = "user_number_input"
selected_condition = None
device1_connected = False
device2_connected = False

# 현재 컴퓨터의 IP 주소를 자동으로 가져옵니다.
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    server_ip = s.getsockname()[0]
    s.close()
except socket.error:
    server_ip = "127.0.0.1"

server_port = 8080

# TCP 서버 변수
server_socket = None
connections = {}
connection_lock = threading.Lock()
server_started = False


def draw_user_number_input():
    screen.fill(WHITE)
    title_text = font_large.render("사용자 번호를 키보드로 입력하세요", True, BLACK)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
    screen.blit(title_text, title_rect)
    input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, 400, 500, 80)
    pygame.draw.rect(screen, GRAY, input_rect, border_radius=10)
    pygame.draw.rect(screen, BLACK, input_rect, 2, border_radius=10)
    input_text = font_medium.render(user_number, True, BLACK)
    input_text_rect = input_text.get_rect(center=input_rect.center)
    screen.blit(input_text, input_text_rect)
    guide_text = font_small.render("입력 후 스페이스 바를 누르세요.", True, BLACK)
    guide_rect = guide_text.get_rect(center=(SCREEN_WIDTH // 2, 520))
    screen.blit(guide_text, guide_rect)


def draw_condition_selection():
    screen.fill(WHITE)
    title_text = font_large.render("조건을 선택하세요", True, BLACK)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
    screen.blit(title_text, title_rect)
    cond1_text = font_medium.render("1. Condition 1", True, BLACK)
    cond1_rect = cond1_text.get_rect(center=(SCREEN_WIDTH // 2, 400))
    screen.blit(cond1_text, cond1_rect)
    cond2_text = font_medium.render("2. Condition 2", True, BLACK)
    cond2_rect = cond2_text.get_rect(center=(SCREEN_WIDTH // 2, 500))
    screen.blit(cond2_text, cond2_rect)
    input_display = font_large.render(condition_input, True, BLUE)
    input_display_rect = input_display.get_rect(center=(SCREEN_WIDTH // 2, 320))
    screen.blit(input_display, input_display_rect)
    guide_text = font_small.render("선택 후 스페이스 바를 누르세요.", True, BLACK)
    guide_rect = guide_text.get_rect(center=(SCREEN_WIDTH // 2, 600))
    screen.blit(guide_text, guide_rect)


def draw_device_connection():
    screen.fill(WHITE)
    title_text = font_large.render("기기 연결", True, BLACK)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
    screen.blit(title_text, title_rect)
    info_text = font_medium.render(f"서버 IP: {server_ip} / 포트: {server_port}", True, BLACK)
    info_rect = info_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
    screen.blit(info_text, info_rect)
    with connection_lock:
        device1_status_text = f"기기 1: {'연결됨' if device1_connected else '연결 안됨'}"
        device1_status_color = GREEN if device1_connected else RED
        device1_text = font_medium.render(device1_status_text, True, device1_status_color)
        device1_rect = device1_text.get_rect(center=(SCREEN_WIDTH // 2, 450))
        screen.blit(device1_text, device1_rect)
        device2_status_text = f"기기 2: {'연결됨' if device2_connected else '연결 안됨'}"
        device2_status_color = GREEN if device2_connected else RED
        device2_text = font_medium.render(device2_status_text, True, device2_status_color)
        device2_rect = device2_text.get_rect(center=(SCREEN_WIDTH // 2, 550))
        screen.blit(device2_text, device2_rect)
    if device1_connected and device2_connected:
        message_text = font_medium.render("두 기기 모두 연결되었습니다. 스페이스 바를 눌러 진행하세요.", True, BLUE)
        message_rect = message_text.get_rect(center=(SCREEN_WIDTH // 2, 750))
        screen.blit(message_text, message_rect)
    else:
        message_text = font_medium.render("기기 연결 중...", True, BLACK)
        message_rect = message_text.get_rect(center=(SCREEN_WIDTH // 2, 750))
        screen.blit(message_text, message_rect)


def draw_snake_game():
    screen.fill(BLACK)
    game_title = font_large.render("뱀 게임", True, WHITE)
    game_title_rect = game_title.get_rect(center=(SCREEN_WIDTH // 2, 150))
    screen.blit(game_title, game_title_rect)
    message_text = font_medium.render("이곳에 뱀 게임 코드를 구현하면 됩니다.", True, GRAY)
    message_rect = message_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(message_text, message_rect)
    exit_text = font_small.render("게임을 종료하려면 'ESC'를 누르세요.", True, GRAY)
    exit_rect = exit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
    screen.blit(exit_text, exit_rect)


def handle_client(conn, addr, device_num):
    print(f"기기 {device_num} ({addr}) 연결됨")

    # 연결된 기기 상태를 True로 업데이트
    with connection_lock:
        global device1_connected, device2_connected
        if device_num == 1:
            device1_connected = True
        elif device_num == 2:
            device2_connected = True

    try:
        while True:
            # 타임아웃을 설정하여 1초마다 연결 상태를 확인
            ready_to_read, _, _ = select.select([conn], [], [], 1.0)
            if not ready_to_read:
                # 데이터가 없으면 다시 루프 시작
                continue

            data = conn.recv(1024)
            if not data:
                print(f"기기 {device_num} ({addr}): 데이터 수신 없이 연결 종료")
                break
            # 데이터 처리 로직...
            print(f"기기 {device_num}로부터 데이터 수신: {data.decode('utf-8')}")
    except (socket.error, ConnectionResetError):
        print(f"기기 {device_num} ({addr}) 연결 끊김.")
    finally:
        with connection_lock:
            if device_num == 1:
                device1_connected = False
            elif device_num == 2:
                device2_connected = False
            if conn in connections.values():
                for key, value in list(connections.items()):
                    if value == conn:
                        del connections[key]
                        break
            conn.close()


def start_server():
    global server_socket
    HOST = ''
    PORT = server_port
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setblocking(False)
        server_socket.bind((HOST, PORT))
        server_socket.listen(2)
        print(f"서버가 {server_ip}:{PORT} 에서 연결을 기다리는 중입니다.")
        return True
    except socket.error as e:
        print(f"서버 소켓 생성 실패: {e}")
        return False


def accept_connections():
    global server_socket, device1_connected, device2_connected
    if server_socket:
        input_sockets = [server_socket]
        readable, _, _ = select.select(input_sockets, [], [], 0.0)
        for sock in readable:
            if sock == server_socket:
                try:
                    conn, addr = server_socket.accept()
                    with connection_lock:
                        if not device1_connected:
                            connections[1] = conn
                            threading.Thread(target=handle_client, args=(conn, addr, 1), daemon=True).start()
                        elif not device2_connected:
                            connections[2] = conn
                            threading.Thread(target=handle_client, args=(conn, addr, 2), daemon=True).start()
                        else:
                            print("최대 연결 수를 초과했습니다. 연결을 거부합니다.")
                            conn.close()
                except socket.error as e:
                    print(f"연결 수락 오류: {e}")


# 메인 루프
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

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
                    if not server_started:
                        start_server()
                        server_started = True

        elif current_state == "device_connection":
            if device1_connected and device2_connected and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    current_state = "snake_game"

        elif current_state == "snake_game":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

    if current_state == "user_number_input":
        draw_user_number_input()
    elif current_state == "condition_selection":
        draw_condition_selection()
    elif current_state == "device_connection":
        draw_device_connection()
        if server_started:
            accept_connections()
    elif current_state == "snake_game":
        draw_snake_game()

    pygame.display.flip()

if server_socket:
    server_socket.close()

pygame.quit()
sys.exit()