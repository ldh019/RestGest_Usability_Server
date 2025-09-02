import pygame
import threading
from game.sequence_game import SequenceGame
from gesture.gesture_server import GestureServer


def main():
    # 모델 파일 경로 설정
    model_path = "assets/model/svm_model_0723-user2-device1-table1.pkl"

    # 게임 및 서버 초기화
    game = SequenceGame()
    gesture_server = GestureServer(game, model_path)

    # 서버를 별도 스레드에서 실행
    server_thread = threading.Thread(target=gesture_server.start_server, daemon=True)
    server_thread.start()

    # 게임 루프
    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.get_time()

        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                game.handle_keydown(event.key)

        # 게임 업데이트
        game.update(dt)

        # 화면 그리기
        game.draw()

        # FPS 제한
        clock.tick(60)

    # 정리
    gesture_server.stop_server()
    pygame.quit()

    # 결과 저장
    condition = input("Enter condition name (condition1/condition2): ")
    results_file = game.save_results(condition)
    print(f"Results saved to: {results_file}")


if __name__ == "__main__":
    main()