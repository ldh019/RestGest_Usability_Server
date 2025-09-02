import pygame
from game.sequence_game import SequenceGame
from gesture.gesture_server import GestureServer
import asyncio
import socket


async def run_game_loop(game, clock):
    """비동기 게임 루프"""
    running = True
    while running:
        dt = clock.get_time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)

        game.update(dt)
        game.draw()

        await asyncio.sleep(0)
        clock.tick(60)
    return running


async def main():
    """메인 비동기 실행 루프"""
    game = SequenceGame()
    gesture_server = None
    server_task = None

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)

        if game.game_state == "connecting_screen" and not game.is_connected and not gesture_server:
            try:
                # Port는 game/config.py에서 가져옵니다.
                model_path = f"assets/model/svm_model_user{game.user_number}.pkl"
                gesture_server = GestureServer(game, model_path)

                # 서버 시작 태스크 생성 및 실행
                server_task = asyncio.create_task(gesture_server.start_server())
                print(f"Server task created. Waiting for connection...")

            except FileNotFoundError:
                print(f"Error: Model file not found at {model_path}.")
                game.game_state = "start_screen"
                game.condition = None
            except Exception as e:
                print(f"Server start error: {e}")
                game.game_state = "start_screen"
                game.condition = None

        if game.game_state == "connecting_screen" and game.is_connected:
            # 연결이 성공하면 게임 루프를 시작하고 다음 상태로 전환
            await run_game_loop(game, clock)

        game.update(clock.get_time())
        game.draw()

        await asyncio.sleep(0)  # 다른 asyncio 작업에 제어권 양보
        clock.tick(60)

    if server_task:
        server_task.cancel()
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())