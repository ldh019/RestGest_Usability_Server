import queue
import random
import time
import pygame
from utils.data_logger import DataLogger
from .config import *


class SequenceGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("RestGest Sequence Game")

        # 폰트 설정 (기본 폰트 사용)
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.back_button_rect = pygame.Rect(20, 20, 150, 60)

        # 게임 상태
        self.reset_game()
        self.game_state = "start_screen"

        # 사용자 입력 변수
        self.user_number = ""
        self.condition = None

        # 기기 연결 상태
        self.is_connected = False
        self.server_ip = None
        self.server_port = None
        self.client_ip = None
        self.client_port = None
        self.server_lost_connection = False  # 서버 연결 끊김 상태 플래그

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

        # 입력 피드백 상태
        self.feedback_message = None
        self.feedback_end_time = 0

        # 맞은 개수와 틀린 개수 추적
        self.correct_gestures = 0
        self.incorrect_gestures = 0

    def reset_game(self):
        """게임 초기화"""
        self.current_level = 1
        self.sequence = []
        self.player_input = []
        self.showing_sequence = False
        self.waiting_for_input = False
        self.sequence_index = 0
        self.score = 0
        self.fatigue_rating = 5
        self.levels_completed = 0
        self.correct_gestures = 0  # 맞은 개수 초기화
        self.incorrect_gestures = 0  # 틀린 개수 초기화
        # self.game_state는 외부에서 설정하므로 초기화하지 않음

    def add_gesture(self, gesture, window_id=None):
        """외부에서 제스처 입력 추가"""
        self.gesture_queue.put((gesture, window_id))

    def generate_sequence(self, length):
        """지정된 길이의 랜덤 시퀀스 생성"""
        return [random.choice(['LEFT', 'RIGHT']) for _ in range(length)]

    def start_level(self):
        """새 레벨 시작"""
        sequence_length = self.current_level + 1
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

    def process_gesture(self, gesture, window_id):
        """제스처 입력 처리"""
        if self.game_state == "playing" and self.waiting_for_input:
            if gesture in ['LEFT', 'RIGHT']:
                self.player_input.append(gesture)

                # 정확도 확인
                correct = (gesture == self.sequence[len(self.player_input) - 1])

                if correct:
                    self.correct_gestures += 1
                else:
                    self.incorrect_gestures += 1

                # 로깅
                reaction_time = time.time() - self.level_start_time
                self.data_logger.log_game_event("gesture_input", {
                    "gesture": gesture,
                    "expected": self.sequence[len(self.player_input) - 1],
                    "correct": correct,
                    "reaction_time": reaction_time,
                    "input_position": len(self.player_input),
                    "sequence_length": len(self.sequence),
                    "window_id": window_id
                })

                if not correct:
                    self.feedback_message = "Incorrect!"
                    self.feedback_end_time = time.time() + 1
                    self.data_logger.log_game_event("level_failed", {
                        "level": self.current_level,
                        "failed_at_position": len(self.player_input)
                    })
                    return

                self.feedback_message = "Correct!"
                self.feedback_end_time = time.time() + 0.5

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
                gesture, window_id = self.gesture_queue.get_nowait()
                self.process_gesture(gesture, window_id)
        except queue.Empty:
            pass

        # 입력 피드백 및 상태 전환 처리
        if self.feedback_message and time.time() >= self.feedback_end_time:
            if self.feedback_message == "Incorrect!":
                self.start_level()
            elif self.feedback_message == "Correct!":
                if len(self.player_input) == len(self.sequence):
                    level_completion_time = time.time() - self.level_start_time
                    self.score += self.current_level * 10
                    self.levels_completed += 1

                    self.data_logger.log_game_event("level_completed", {
                        "level": self.current_level,
                        "completion_time": level_completion_time,
                        "score_gained": self.current_level * 10,
                        "total_score": self.score
                    })

                    if self.current_level == 9:
                        self.game_state = "fatigue_check"
                        self.data_logger.log_game_event("all_levels_completed", {
                            "final_score": self.score,
                            "total_levels": self.levels_completed
                        })
                    else:
                        self.current_level += 1
                        self.start_level()
            self.feedback_message = None

        # 시퀀스 표시 타이머
        if self.showing_sequence:
            self.sequence_timer += dt

            cycle_time = 1500
            current_cycle = int(self.sequence_timer / cycle_time)
            time_in_cycle = self.sequence_timer % cycle_time

            if current_cycle < len(self.sequence):
                self.sequence_index = current_cycle
                self.show_arrow = time_in_cycle < 1000
            else:
                self.showing_sequence = False
                self.waiting_for_input = True
                self.sequence_timer = 0

    def draw(self):
        """화면 그리기"""
        self.screen.fill(WHITE)

        if self.game_state == "start_screen":
            self.draw_start_screen()
        elif self.game_state == "connecting_screen":
            self.draw_connecting_screen()
            self.draw_back_button()
        elif self.game_state == "ready":
            self.draw_ready_screen()
            self.draw_back_button()
        elif self.game_state == "playing":
            self.draw_game_screen()
            self.draw_back_button()
        elif self.game_state == "fatigue_check":
            self.draw_fatigue_check()
            self.draw_back_button()
        elif self.game_state == "post_game":
            self.draw_post_game_screen()
        elif self.game_state == "finished":
            self.draw_finished_screen()

        pygame.display.flip()

    def draw_back_button(self):
        """뒤로가기 버튼 그리기"""
        pygame.draw.rect(self.screen, GRAY, self.back_button_rect, border_radius=5)
        text = self.font_small.render("Back", True, BLACK)
        text_rect = text.get_rect(center=self.back_button_rect.center)
        self.screen.blit(text, text_rect)

    def draw_start_screen(self):
        """사용자 번호 및 조건 선택 화면"""
        title_text = self.font_medium.render("Enter User Number & Select Condition", True, BLACK)
        self.screen.blit(title_text, (WINDOW_WIDTH // 2 - 250, 300))

        # 텍스트 상자 그리기
        input_box = pygame.Rect(WINDOW_WIDTH // 2 - 150, 450, 300, 70)
        pygame.draw.rect(self.screen, BLACK, input_box, 2)

        # 텍스트 그리기
        user_text_surface = self.font_medium.render(self.user_number, True, BLACK)
        self.screen.blit(user_text_surface, (input_box.x + 15, input_box.y + 15))

        # 안내 문구
        instruction_text = self.font_small.render("User Number (0-9)", True, GRAY)
        self.screen.blit(instruction_text, (input_box.x, input_box.y - 40))

        # Condition 1 버튼
        cond1_color = BLUE if self.condition == "condition1" else GRAY
        cond1_rect = pygame.Rect(WINDOW_WIDTH // 4, WINDOW_HEIGHT // 2 + 100, 300, 100)
        pygame.draw.rect(self.screen, cond1_color, cond1_rect, border_radius=10)
        cond1_text = self.font_medium.render("Condition 1", True, WHITE)
        cond1_text_rect = cond1_text.get_rect(center=cond1_rect.center)
        self.screen.blit(cond1_text, cond1_text_rect)

        # Condition 2 버튼
        cond2_color = RED if self.condition == "condition2" else GRAY
        cond2_rect = pygame.Rect(WINDOW_WIDTH * 3 // 4 - 300, WINDOW_HEIGHT // 2 + 100, 300, 100)
        pygame.draw.rect(self.screen, cond2_color, cond2_rect, border_radius=10)
        cond2_text = self.font_medium.render("Condition 2", True, WHITE)
        cond2_text_rect = cond2_text.get_rect(center=cond2_rect.center)
        self.screen.blit(cond2_text, cond2_text_rect)

        if self.condition:
            start_prompt = self.font_medium.render("Press SPACE to Start", True, BLACK)
            prompt_rect = start_prompt.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 250))
            self.screen.blit(start_prompt, prompt_rect)

    def draw_connecting_screen(self):
        """기기 연결 화면"""
        title_text = self.font_medium.render("Device Connection", True, BLACK)
        self.screen.blit(title_text, (WINDOW_WIDTH // 2 - 200, 350))

        if self.is_connected:
            status_text = self.font_medium.render("Connected!", True, GREEN)
            self.screen.blit(status_text, (WINDOW_WIDTH // 2 - 120, 500))

            info_text = self.font_small.render(
                f"Client IP: {self.client_ip}, Port: {self.client_port}", True, BLACK
            )
            self.screen.blit(info_text, (WINDOW_WIDTH // 2 - 200, 600))

            start_text = self.font_medium.render("Press SPACE to Continue", True, BLACK)
            self.screen.blit(start_text, (WINDOW_WIDTH // 2 - 250, 750))

        else:
            status_text = self.font_medium.render("Waiting for connection...", True, RED)
            self.screen.blit(status_text, (WINDOW_WIDTH // 2 - 220, 500))

            info_text = self.font_small.render(
                f"Server IP: {self.server_ip}, Port: {self.server_port}", True, BLACK
            )
            self.screen.blit(info_text, (WINDOW_WIDTH // 2 - 200, 600))

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
        self.screen.blit(level_text, (50, 100))  # 점수 위치 아래로 이동
        self.screen.blit(score_text, (50, 150))  # 점수 위치 아래로 이동

        if self.showing_sequence:
            # 시퀀스 표시
            sequence_text = self.font_medium.render("Watch the sequence:", True, BLACK)
            self.screen.blit(sequence_text, (WINDOW_WIDTH // 2 - 200, 200))

            # 현재 화살표 표시 (show_arrow가 True일 때만)
            if (self.sequence_index < len(self.sequence) and
                    self.show_arrow):
                direction = self.sequence[self.sequence_index]
                self.draw_sequence_arrow(direction, self.sequence_index + 1)
        elif self.waiting_for_input:
            # 입력 대기
            input_text = self.font_medium.render("Your turn! Use gestures:", True, BLACK)
            self.screen.blit(input_text, (WINDOW_WIDTH // 2 - 200, 250))

            # 진행상황 표시
            progress_text = self.font_small.render(
                f"Progress: {len(self.player_input)}/{len(self.sequence)}",
                True, BLACK
            )
            self.screen.blit(progress_text, (WINDOW_WIDTH // 2 - 100, 300))

            # 피드백 메시지 표시
            if self.feedback_message:
                feedback_color = GREEN if self.feedback_message == "Correct!" else RED
                feedback_text = self.font_medium.render(self.feedback_message, True, feedback_color)
                feedback_rect = feedback_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
                self.screen.blit(feedback_text, feedback_rect)

    def draw_sequence_arrow(self, direction, sequence_number):
        """시퀀스용 화살표 그리기 (명확한 온/오프)"""
        center_y = WINDOW_HEIGHT // 2 + 100
        base_intensity = 200
        color_boost = min(50, sequence_number * 8)

        if direction == 'LEFT':
            center_x = WINDOW_WIDTH // 4
            arrow_color = (0, 0, base_intensity + color_boost)

            pygame.draw.polygon(self.screen, arrow_color, [
                (center_x - 75, center_y), (center_x + 15, center_y - 60),
                (center_x + 15, center_y - 25), (center_x + 75, center_y - 25),
                (center_x + 75, center_y + 25), (center_x + 15, center_y + 25),
                (center_x + 15, center_y + 60)
            ])
            pygame.draw.polygon(self.screen, BLACK, [
                (center_x - 75, center_y), (center_x + 15, center_y - 60),
                (center_x + 15, center_y - 25), (center_x + 75, center_y - 25),
                (center_x + 75, center_y + 25), (center_x + 15, center_y + 25),
                (center_x + 15, center_y + 60)
            ], 3)
        else:
            center_x = WINDOW_WIDTH * 3 // 4
            arrow_color = (base_intensity + color_boost, 0, 0)

            pygame.draw.polygon(self.screen, arrow_color, [
                (center_x + 75, center_y), (center_x - 15, center_y - 60),
                (center_x - 15, center_y - 25), (center_x - 75, center_y - 25),
                (center_x - 75, center_y + 25), (center_x - 15, center_y + 25),
                (center_x - 15, center_y + 60)
            ])
            pygame.draw.polygon(self.screen, BLACK, [
                (center_x + 75, center_y), (center_x - 15, center_y - 60),
                (center_x - 15, center_y - 25), (center_x - 75, center_y - 25),
                (center_x - 75, center_y + 25), (center_x - 15, center_y + 25),
                (center_x - 15, center_y + 60)
            ], 3)

    def draw_fatigue_check(self):
        """피로도 체크 화면"""
        title_text = self.font_medium.render("Fatigue Rating (1-10)", True, BLACK)
        instruction_text = self.font_small.render(
            "Use LEFT gesture to decrease, RIGHT to increase", True, BLACK
        )
        rating_text = self.font_large.render(str(self.fatigue_rating), True, BLACK)
        confirm_text = self.font_small.render("Press SPACE when done", True, BLACK)

        self.screen.blit(title_text, (WINDOW_WIDTH // 2 - 200, 300))
        self.screen.blit(instruction_text, (WINDOW_WIDTH // 2 - 250, 400))
        self.screen.blit(rating_text, (WINDOW_WIDTH // 2 - 40, 550))
        self.screen.blit(confirm_text, (WINDOW_WIDTH // 2 - 150, 700))

    def draw_post_game_screen(self):
        """게임 종료 후 옵션 화면"""
        title_text = self.font_large.render("Game Completed!", True, BLACK)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 200))
        self.screen.blit(title_text, title_rect)

        # Play Again 버튼
        play_again_rect = pygame.Rect(WINDOW_WIDTH // 4, WINDOW_HEIGHT // 2, 300, 100)
        pygame.draw.rect(self.screen, BLUE, play_again_rect, border_radius=10)
        play_again_text = self.font_medium.render("Play Again", True, WHITE)
        play_again_text_rect = play_again_text.get_rect(center=play_again_rect.center)
        self.screen.blit(play_again_text, play_again_text_rect)

        # Home 버튼
        home_rect = pygame.Rect(WINDOW_WIDTH * 3 // 4 - 300, WINDOW_HEIGHT // 2, 300, 100)
        pygame.draw.rect(self.screen, RED, home_rect, border_radius=10)
        home_text = self.font_medium.render("Home", True, WHITE)
        home_text_rect = home_text.get_rect(center=home_rect.center)
        self.screen.blit(home_text, home_text_rect)

    def draw_finished_screen(self):
        """최종 종료 화면"""
        finished_text = self.font_large.render("Game Finished!", True, BLACK)
        final_score_text = self.font_medium.render(f"Final Score: {self.score}", True, BLACK)
        info_text = self.font_small.render("Results saved. You can close the window.", True, BLACK)

        text_rect = finished_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100))
        score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        info_rect = info_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 100))

        self.screen.blit(finished_text, text_rect)
        self.screen.blit(final_score_text, score_rect)
        self.screen.blit(info_text, info_rect)

    def handle_event(self, event):
        """이벤트 처리"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button_rect.collidepoint(event.pos) and self.game_state not in ["start_screen", "finished",
                                                                                         "post_game"]:
                if self.game_state == "connecting_screen":
                    self.server_lost_connection = True
                    self.game_state = "start_screen"
                elif self.game_state == "ready":
                    self.is_connected = False
                    self.client_ip = None
                    self.client_port = None
                    self.server_lost_connection = True  # 서버 연결 종료 신호
                    self.game_state = "connecting_screen"
                elif self.game_state == "playing":
                    self.game_state = "ready"
                    self.reset_game_state()
                elif self.game_state == "fatigue_check":
                    self.game_state = "playing"
                    self.reset_game_state()

            # 게임 후 옵션 버튼 클릭 처리
            if self.game_state == "post_game":
                play_again_rect = pygame.Rect(WINDOW_WIDTH // 4, WINDOW_HEIGHT // 2, 300, 100)
                home_rect = pygame.Rect(WINDOW_WIDTH * 3 // 4 - 300, WINDOW_HEIGHT // 2, 300, 100)
                if play_again_rect.collidepoint(event.pos):
                    self.reset_game_for_new_session()
                elif home_rect.collidepoint(event.pos):
                    self.server_lost_connection = True
                    self.reset_game()
                    self.game_state = "start_screen"

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and self.game_state not in ["start_screen", "finished", "post_game"]:
                if self.game_state == "connecting_screen":
                    self.server_lost_connection = True
                    self.game_state = "start_screen"
                elif self.game_state == "ready":
                    self.is_connected = False
                    self.client_ip = None
                    self.client_port = None
                    self.server_lost_connection = True  # 서버 연결 종료 신호
                    self.game_state = "connecting_screen"
                elif self.game_state == "playing":
                    self.game_state = "ready"
                    self.reset_game_state()
                elif self.game_state == "fatigue_check":
                    self.game_state = "playing"
                    self.reset_game_state()

            if self.game_state == "start_screen":
                if event.key == pygame.K_BACKSPACE:
                    self.user_number = self.user_number[:-1]
                elif event.key == pygame.K_LEFT:
                    self.condition = "condition1"
                elif event.key == pygame.K_RIGHT:
                    self.condition = "condition2"
                elif event.key >= pygame.K_0 and event.key <= pygame.K_9:
                    self.user_number += pygame.key.name(event.key)
                elif event.key == pygame.K_SPACE:
                    if self.user_number and self.condition:
                        self.game_state = "connecting_screen"
            elif self.game_state == "connecting_screen":
                if event.key == pygame.K_SPACE and self.is_connected:
                    self.game_state = "ready"
            elif self.game_state == "ready":
                if event.key == pygame.K_SPACE:
                    self.start_level()
            elif self.game_state == "fatigue_check":
                if event.key == pygame.K_SPACE:
                    self.finish_game()
                elif event.key == pygame.K_LEFT:
                    self.process_gesture('LEFT', None)
                elif event.key == pygame.K_RIGHT:
                    self.process_gesture('RIGHT', None)
            elif self.game_state == "playing" and self.waiting_for_input:
                if event.key == pygame.K_LEFT:
                    self.process_gesture('LEFT', None)
                elif event.key == pygame.K_RIGHT:
                    self.process_gesture('RIGHT', None)
            elif self.game_state == "post_game":
                if event.key == pygame.K_LEFT:
                    self.reset_game_for_new_session()
                elif event.key == pygame.K_RIGHT:
                    self.server_lost_connection = True
                    self.reset_game()
                    self.game_state = "start_screen"

    def reset_game_state(self):
        """게임을 초기 상태로 돌리는 도우미 함수"""
        self.current_level = 1
        self.sequence = []
        self.player_input = []
        self.showing_sequence = False
        self.waiting_for_input = False
        self.sequence_index = 0

    def reset_game_for_new_session(self):
        """현재 조건과 유저 번호를 유지하고 게임을 리셋"""
        self.current_level = 1
        self.sequence = []
        self.player_input = []
        self.showing_sequence = False
        self.waiting_for_input = False
        self.sequence_index = 0
        self.score = 0
        self.fatigue_rating = 5
        self.levels_completed = 0
        self.correct_gestures = 0
        self.incorrect_gestures = 0
        self.game_state = "ready"

    def on_connection_lost(self):
        """서버 연결 끊김 시 호출되는 메서드"""
        print("Connection lost. Resetting game state...")
        self.is_connected = False
        self.client_ip = None
        self.client_port = None
        self.game_state = "start_screen"
        self.server_lost_connection = True
        self.data_logger.log_game_event("connection_lost", {})

    def finish_game(self):
        """게임 종료"""
        self.data_logger.log_game_event("fatigue_rating", {
            "rating": self.fatigue_rating
        })
        self.data_logger.save_experiment_results(f"user{self.user_number}_{self.condition}", self.correct_gestures, self.incorrect_gestures)
        self.game_state = "post_game"