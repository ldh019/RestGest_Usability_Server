import pygame
import threading
from game.sequence_game import SequenceGame
from gesture.gesture_server import GestureServer
import time
import socket


def main():
    game = SequenceGame()
    gesture_server = None
    server_thread = None

    # 게임 루프
    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.get_time()

        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)

        # 서버 연결 끊김 감지 및 정리
        if game.server_lost_connection:
            if gesture_server:
                gesture_server.stop_server()
            gesture_server = None
            game.server_lost_connection = False

        # 연결 화면 상태에서 서버 시작 로직
        if game.game_state == "connecting_screen" and not game.is_connected and not gesture_server:
            game.server_ip = socket.gethostbyname(socket.gethostname())

            if game.condition == 'condition2':
                ports = [9090, 9091]
                server_started = False
                for port in ports:
                    try:
                        model_path = f"assets/model/svm_model_user{game.user_number}.pkl"
                        gesture_server = GestureServer(game, model_path)
                        gesture_server.PORT = port
                        server_thread = threading.Thread(target=gesture_server.start_server, daemon=True)
                        server_thread.start()
                        game.server_port = port
                        server_started = True
                        print(f"Server started on port {port} with model: {model_path}")
                        break
                    except OSError as e:
                        if e.errno == 98:  # 98은 "Address already in use" 에러 코드
                            print(f"Port {port} is already in use. Trying next port...")
                            continue
                        else:
                            print(f"Server start error: {e}")
                            game.game_state = "start_screen"
                            game.condition = None
                            break
                    except FileNotFoundError:
                        print(f"Error: Model file not found at {model_path}. Please check the file path.")
                        game.game_state = "start_screen"
                        game.condition = None
                        break
                if not server_started:
                    print("Failed to start server on both ports.")
                    game.game_state = "start_screen"
                    game.condition = None
            else:  # Condition 1
                game.server_port = None
                game.is_connected = True
                print("Condition 1 selected. Skipping server connection.")

        # 게임 업데이트
        game.update(dt)

        # 화면 그리기
        game.draw()

        # FPS 제한
        clock.tick(60)

    # 정리
    if gesture_server:
        gesture_server.stop_server()
    pygame.quit()


if __name__ == "__main__":
    main()