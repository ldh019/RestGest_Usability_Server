import pygame
import random
import time
import queue
from datetime import datetime
from .config import *
from utils.data_logger import DataLogger


class SequenceGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("RestGest Sequence Game")

        # 폰트 설정
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)

        # 게임 상태
        self.reset_game()

        # 제스처 입력 처리
        self.gesture_queue = queue.Queue()

        # 데이터 로거
        self.data_logger = DataLogger()

        # 타이머
        self.sequence_timer = 0
        self.level_start_time = None

        # 깜빡임 효과를 위한 변수들
        self.blink_timer = 0
        self.blink_interval = 300  # 300ms마다 깜빡임
        self.show_arrow = True

    def reset_game(self):
        """게임 초기화"""
        self.current_level = 1
        self.sequence = []
        self.player_input = []
        self.showing_sequence = False
        self.waiting_for_input = False
        self.sequence_index = 0
        self.score = 0
        self.game_state = "ready"  # ready, playing, fatigue_check, finished
        self.fatigue_rating = 5  # 1-10 척도의 중간값으로 초기화
        self.levels_completed = 0

    def add_gesture(self, gesture):
        """외부에서 제스처 입력 추가"""
        self.gesture_queue.put(gesture)

    def generate_sequence(self, length):
        """지정된 길이의 랜덤 시퀀스 생성"""
        return [random.choice(['LEFT', 'RIGHT']) for _ in range(length)]

    def start_level(self):
        """새 레벨 시작"""
        sequence_length = self.current_level + 1  # Level 1 = 2개, Level 9 = 10개
        self.sequence = self.generate_sequence(sequence_length)
        self.player_input = []
        self.sequence_index = 0
        self.showing_sequence = True
        self.waiting_for_input = False
        self.game_state = "playing"
        self.level_start_time = time.time()

        # 로깅
        self.data_logger.log_game_event("level_start", {
            "level": self.current_level,
            "sequence": self.sequence,
            "sequence_length": len(self.sequence)
        })

    def process_gesture(self, gesture):
        """제스처 입력 처리"""
        if self.game_state == "playing" and self.waiting_for_input:
            if gesture in ['LEFT', 'RIGHT']:
                reaction_time = time.time() - self.level_start_time
                self.player_input.append(gesture)

                # 정확도 확인
                correct = (gesture == self.sequence[len(self.player_input) - 1])

                # 로깅
                self.data_logger.log_game_event("gesture_input", {
                    "gesture": gesture,
                    "expected": self.sequence[len(self.player_input) - 1],
                    "correct": correct,
                    "reaction_time": reaction_time,
                    "input_position": len(self.player_input),
                    "sequence_length": len(self.sequence)
                })

                if not correct:
                    # 틀렸을 때 - 같은 레벨 재시작
                    self.data_logger.log_game_event("level_failed", {
                        "level": self.current_level,
                        "failed_at_position": len(self.player_input)
                    })
                    time.sleep(1)
                    self.start_level()
                    return

                # 시퀀스 완성 확인
                if len(self.player_input) == len(self.sequence):
                    # 성공!
                    level_completion_time = time.time() - self.level_start_time
                    self.score += self.current_level * 10
                    self.levels_completed += 1

                    # 로깅
                    self.data_logger.log_game_event("level_completed", {
                        "level": self.current_level,
                        "completion_time": level_completion_time,
                        "score_gained": self.current_level * 10,
                        "total_score": self.score
                    })

                    if self.current_level == 9:  # 모든 레벨 완료
                        self.game_state = "fatigue_check"
                        self.data_logger.log_game_event("all_levels_completed", {
                            "final_score": self.score,
                            "total_levels": self.levels_completed
                        })
                    else:
                        self.current_level += 1
                        time.sleep(1)  # 잠시 대기
                        self.start_level()

        elif self.game_state == "fatigue_check":
            if gesture == "LEFT" and self.fatigue_rating > 1:
                self.fatigue_rating -= 1
            elif gesture == "RIGHT" and self.fatigue_rating < 10:
                self.fatigue_rating += 1

    def update(self, dt):
        """게임 상태 업데이트"""
        # 제스처 큐 처리
        try:
            while not self.gesture_queue.empty():
                gesture = self.gesture_queue.get_nowait()
                self.process_gesture(gesture)
        except queue.Empty:
            pass

        # 시퀀스 표시 타이머
        if self.showing_sequence:
            self.sequence_timer += dt
            if self.sequence_timer >= 1500:  # 1.5초
                self.sequence_timer = 0
                self.sequence_index += 1
                if self.sequence_index >= len(self.sequence):
                    self.showing_sequence = False
                    self.waiting_for_input = True

        # 시퀀스 표시 타이밍 관리
        if self.showing_sequence:
            self.sequence_timer += dt

            # 각 화살표를 1초 표시, 0.5초 공백으로 구분
            cycle_time = 1500  # 1초 표시 + 0.5초 공백
            current_cycle = int(self.sequence_timer / cycle_time)
            time_in_cycle = self.sequence_timer % cycle_time

            if current_cycle < len(self.sequence):
                self.sequence_index = current_cycle
                # 처음 1초는 표시, 나머지 0.5초는 숨김
                self.show_arrow = time_in_cycle < 1000
            else:
                # 모든 시퀀스 표시 완료
                self.showing_sequence = False
                self.waiting_for_input = True
                self.sequence_timer = 0

    def draw(self):
        """화면 그리기"""
        self.screen.fill(WHITE)

        if self.game_state == "ready":
            self.draw_ready_screen()
        elif self.game_state == "playing":
            self.draw_game_screen()
        elif self.game_state == "fatigue_check":
            self.draw_fatigue_check()
        elif self.game_state == "finished":
            self.draw_finished_screen()

        pygame.display.flip()

    def draw_ready_screen(self):
        """준비 화면"""
        text = self.font_large.render("Press SPACE to Start", True, BLACK)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(text, text_rect)

    def draw_game_screen(self):
        """게임 플레이 화면"""
        # 상태 표시
        level_text = self.font_medium.render(f"Level: {self.current_level}", True, BLACK)
        score_text = self.font_medium.render(f"Score: {self.score}", True, BLACK)
        self.screen.blit(level_text, (20, 20))
        self.screen.blit(score_text, (20, 70))

        if self.showing_sequence:
            # 시퀀스 표시
            sequence_text = self.font_medium.render("Watch the sequence:", True, BLACK)
            self.screen.blit(sequence_text, (WINDOW_WIDTH // 2 - 150, 100))

            # 전체 시퀀스 미리보기
            preview_text = self.font_small.render("Full sequence:", True, GRAY)
            self.screen.blit(preview_text, (50, 130))

            for i, direction in enumerate(self.sequence):
                x_pos = 50 + (i * 40)
                # 현재 진행중인 화살표는 다른 색상으로 표시
                if i == self.sequence_index:
                    color = GREEN
                elif i < self.sequence_index:
                    color = GRAY  # 이미 지나간 것들
                else:
                    color = BLUE if direction == 'LEFT' else RED

                # 작은 화살표 미리보기
                if direction == 'LEFT':
                    pygame.draw.polygon(self.screen, color, [
                        (x_pos, 160), (x_pos - 10, 155), (x_pos - 10, 165)
                    ])
                else:
                    pygame.draw.polygon(self.screen, color, [
                        (x_pos, 160), (x_pos + 10, 155), (x_pos + 10, 165)
                    ])

                # 순서 번호
                num_text = self.font_small.render(str(i + 1), True, BLACK)
                num_rect = num_text.get_rect(center=(x_pos, 175))
                self.screen.blit(num_text, num_rect)

            # 현재 화살표 표시 (show_arrow가 True일 때만)
            if (self.sequence_index < len(self.sequence) and
                    self.show_arrow):
                direction = self.sequence[self.sequence_index]
                self.draw_sequence_arrow(direction, self.sequence_index + 1)

        elif self.waiting_for_input:
            # 입력 대기
            input_text = self.font_medium.render("Your turn! Use gestures:", True, BLACK)
            self.screen.blit(input_text, (WINDOW_WIDTH // 2 - 150, 150))

            # 진행상황 표시
            progress_text = self.font_small.render(
                f"Progress: {len(self.player_input)}/{len(self.sequence)}",
                True, BLACK
            )
            self.screen.blit(progress_text, (WINDOW_WIDTH // 2 - 80, 200))

    def draw_sequence_arrow(self, direction, sequence_number):
        """시퀀스용 화살표 그리기 (명확한 온/오프)"""
        center_y = WINDOW_HEIGHT // 2 + 50

        # 순서에 따른 색상 강도 조절
        base_intensity = 200
        color_boost = min(50, sequence_number * 8)

        if direction == 'LEFT':
            center_x = WINDOW_WIDTH // 4
            arrow_color = (0, 0, base_intensity + color_boost)

            # 왼쪽 방향 화살표
            pygame.draw.polygon(self.screen, arrow_color, [
                (center_x - 50, center_y),
                (center_x + 10, center_y - 40),
                (center_x + 10, center_y - 15),
                (center_x + 50, center_y - 15),
                (center_x + 50, center_y + 15),
                (center_x + 10, center_y + 15),
                (center_x + 10, center_y + 40)
            ])

            # 테두리
            pygame.draw.polygon(self.screen, BLACK, [
                (center_x - 50, center_y),
                (center_x + 10, center_y - 40),
                (center_x + 10, center_y - 15),
                (center_x + 50, center_y - 15),
                (center_x + 50, center_y + 15),
                (center_x + 10, center_y + 15),
                (center_x + 10, center_y + 40)
            ], 3)

        else:  # RIGHT
            center_x = WINDOW_WIDTH * 3 // 4
            arrow_color = (base_intensity + color_boost, 0, 0)

            # 오른쪽 방향 화살표
            pygame.draw.polygon(self.screen, arrow_color, [
                (center_x + 50, center_y),
                (center_x - 10, center_y - 40),
                (center_x - 10, center_y - 15),
                (center_x - 50, center_y - 15),
                (center_x - 50, center_y + 15),
                (center_x - 10, center_y + 15),
                (center_x - 10, center_y + 40)
            ])

            # 테두리
            pygame.draw.polygon(self.screen, BLACK, [
                (center_x + 50, center_y),
                (center_x - 10, center_y - 40),
                (center_x - 10, center_y - 15),
                (center_x - 50, center_y - 15),
                (center_x - 50, center_y + 15),
                (center_x - 10, center_y + 15),
                (center_x - 10, center_y + 40)
            ], 3)

    def draw_fatigue_check(self):
        """피로도 체크 화면"""
        title_text = self.font_medium.render("Fatigue Rating (1-10)", True, BLACK)
        instruction_text = self.font_small.render(
            "Use LEFT gesture to decrease, RIGHT to increase", True, BLACK
        )
        rating_text = self.font_large.render(str(self.fatigue_rating), True, BLACK)
        confirm_text = self.font_small.render("Press SPACE when done", True, BLACK)

        self.screen.blit(title_text, (WINDOW_WIDTH // 2 - 150, 200))
        self.screen.blit(instruction_text, (WINDOW_WIDTH // 2 - 200, 250))
        self.screen.blit(rating_text, (WINDOW_WIDTH // 2 - 20, 350))
        self.screen.blit(confirm_text, (WINDOW_WIDTH // 2 - 100, 450))

    def draw_finished_screen(self):
        """완료 화면"""
        finished_text = self.font_large.render("Game Finished!", True, BLACK)
        final_score_text = self.font_medium.render(f"Final Score: {self.score}", True, BLACK)

        text_rect = finished_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))

        self.screen.blit(finished_text, text_rect)
        self.screen.blit(final_score_text, score_rect)

    def handle_keydown(self, key):
        """키보드 입력 처리"""
        if key == pygame.K_SPACE:
            if self.game_state == "ready":
                self.start_level()
            elif self.game_state == "fatigue_check":
                self.finish_game()
        # 테스트용
        elif key == pygame.K_LEFT:
            self.add_gesture('LEFT')
        elif key == pygame.K_RIGHT:
            self.add_gesture('RIGHT')

    def finish_game(self):
        """게임 종료"""
        self.data_logger.log_game_event("fatigue_rating", {
            "rating": self.fatigue_rating
        })
        self.game_state = "finished"

    def save_results(self, condition):
        """결과 저장"""
        return self.data_logger.save_experiment_results(condition)