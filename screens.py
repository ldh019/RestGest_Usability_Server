# screens.py

import pygame
import sys


class ScreenManager:
    def __init__(self, screen, screen_width, screen_height, fonts):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.fonts = fonts
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (200, 200, 200)
        self.BLUE = (0, 0, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)

        self.back_button_rect = pygame.Rect(30, 30, 150, 50)
        self.stop_button_rect = pygame.Rect(self.screen_width - 180, 30, 150, 50)
        self.restart_button_rect = pygame.Rect(self.screen_width // 2 - 200, 550, 150, 50)
        self.main_menu_button_rect = pygame.Rect(self.screen_width // 2 + 50, 550, 250, 50)

    def is_back_button_clicked(self, mouse_pos):
        return self.back_button_rect.collidepoint(mouse_pos)

    def draw_back_button(self):
        pygame.draw.rect(self.screen, self.GRAY, self.back_button_rect, border_radius=10)
        text_surface = self.fonts['small'].render("뒤로가기", True, self.BLACK)
        text_rect = text_surface.get_rect(center=self.back_button_rect.center)
        self.screen.blit(text_surface, text_rect)

    def is_stop_button_clicked(self, mouse_pos):
        return self.stop_button_rect.collidepoint(mouse_pos)

    def draw_stop_button(self):
        pygame.draw.rect(self.screen, self.RED, self.stop_button_rect, border_radius=10)
        text_surface = self.fonts['small'].render("게임 중단하기", True, self.WHITE)
        text_rect = text_surface.get_rect(center=self.stop_button_rect.center)
        self.screen.blit(text_surface, text_rect)

    def is_restart_button_clicked(self, mouse_pos):
        return self.restart_button_rect.collidepoint(mouse_pos)

    def is_main_menu_button_clicked(self, mouse_pos):
        return self.main_menu_button_rect.collidepoint(mouse_pos)

    def draw_user_number_input(self, user_number):
        self.screen.fill(self.WHITE)
        title_text = self.fonts['large'].render("사용자 번호를 키보드로 입력하세요", True, self.BLACK)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 200))
        self.screen.blit(title_text, title_rect)
        input_rect = pygame.Rect(self.screen_width // 2 - 250, 400, 500, 80)
        pygame.draw.rect(self.screen, self.GRAY, input_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.BLACK, input_rect, 2, border_radius=10)
        input_text = self.fonts['medium'].render(user_number, True, self.BLACK)
        input_text_rect = input_text.get_rect(center=input_rect.center)
        self.screen.blit(input_text, input_text_rect)
        guide_text = self.fonts['small'].render("입력 후 스페이스 바를 누르세요.", True, self.BLACK)
        guide_rect = guide_text.get_rect(center=(self.screen_width // 2, 520))
        self.screen.blit(guide_text, guide_rect)

    def draw_condition_selection(self, condition_input):
        self.screen.fill(self.WHITE)
        self.draw_back_button()
        title_text = self.fonts['large'].render("조건을 선택하세요", True, self.BLACK)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 250))
        self.screen.blit(title_text, title_rect)
        cond1_text = self.fonts['medium'].render("1. Condition 1", True, self.BLACK)
        cond1_rect = cond1_text.get_rect(center=(self.screen_width // 2, 400))
        self.screen.blit(cond1_text, cond1_rect)
        cond2_text = self.fonts['medium'].render("2. Condition 2", True, self.BLACK)
        cond2_rect = cond2_text.get_rect(center=(self.screen_width // 2, 500))
        self.screen.blit(cond2_text, cond2_rect)
        input_display = self.fonts['large'].render(condition_input, True, self.BLUE)
        input_display_rect = input_display.get_rect(center=(self.screen_width // 2, 320))
        self.screen.blit(input_display, input_display_rect)
        guide_text = self.fonts['small'].render("선택 후 스페이스 바를 누르세요.", True, self.BLACK)
        guide_rect = guide_text.get_rect(center=(self.screen_width // 2, 600))
        self.screen.blit(guide_text, guide_rect)

    def draw_device_connection(self, server_ip, server_port, device1_connected, device2_connected):
        self.screen.fill(self.WHITE)
        self.draw_back_button()
        title_text = self.fonts['large'].render("기기 연결", True, self.BLACK)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(title_text, title_rect)
        info_text = self.fonts['medium'].render(f"서버 IP: {server_ip} / 포트: {server_port}", True, self.BLACK)
        info_rect = info_text.get_rect(center=(self.screen_width // 2, 300))
        self.screen.blit(info_text, info_rect)
        device1_status_text = f"기기 1: {'연결됨' if device1_connected else '연결 안됨'}"
        device1_status_color = self.GREEN if device1_connected else self.RED
        device1_text = self.fonts['medium'].render(device1_status_text, True, device1_status_color)
        device1_rect = device1_text.get_rect(center=(self.screen_width // 2, 450))
        self.screen.blit(device1_text, device1_rect)
        device2_status_text = f"기기 2: {'연결됨' if device2_connected else '연결 안됨'}"
        device2_status_color = self.GREEN if device2_connected else self.RED
        device2_text = self.fonts['medium'].render(device2_status_text, True, device2_status_color)
        device2_rect = device2_text.get_rect(center=(self.screen_width // 2, 550))
        self.screen.blit(device2_text, device2_rect)
        if device1_connected and device2_connected:
            message_text = self.fonts['medium'].render("두 기기 모두 연결되었습니다. 스페이스 바를 눌러 진행하세요.", True, self.BLUE)
            message_rect = message_text.get_rect(center=(self.screen_width // 2, 750))
            self.screen.blit(message_text, message_rect)
        else:
            message_text = self.fonts['medium'].render("기기 연결 중...", True, self.BLACK)
            message_rect = message_text.get_rect(center=(self.screen_width // 2, 750))
            self.screen.blit(message_text, message_rect)

    def draw_waiting_for_data(self, device1_data_received, device2_data_received):
        self.screen.fill(self.WHITE)
        self.draw_back_button()
        title_text = self.fonts['large'].render("게임 시작 전 대기", True, self.BLACK)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 250))
        self.screen.blit(title_text, title_rect)

        status_text1 = f"기기 1: {'데이터 수신됨' if device1_data_received else '데이터 대기 중'}"
        status_color1 = self.GREEN if device1_data_received else self.RED
        status_surface1 = self.fonts['medium'].render(status_text1, True, status_color1)
        status_rect1 = status_surface1.get_rect(center=(self.screen_width // 2, 400))
        self.screen.blit(status_surface1, status_rect1)

        status_text2 = f"기기 2: {'데이터 수신됨' if device2_data_received else '데이터 대기 중'}"
        status_color2 = self.GREEN if device2_data_received else self.RED
        status_surface2 = self.fonts['medium'].render(status_text2, True, status_color2)
        status_rect2 = status_surface2.get_rect(center=(self.screen_width // 2, 500))
        self.screen.blit(status_surface2, status_rect2)

        if device1_data_received and device2_data_received:
            ready_text = self.fonts['medium'].render("모든 기기에서 데이터가 수신되었습니다. 잠시 후 게임이 시작됩니다.", True, self.BLUE)
            ready_rect = ready_text.get_rect(center=(self.screen_width // 2, 650))
            self.screen.blit(ready_text, ready_rect)

    def draw_countdown(self, countdown_time):
        self.screen.fill(self.WHITE)
        countdown_text = self.fonts['large'].render(str(countdown_time), True, self.BLUE)
        countdown_rect = countdown_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(countdown_text, countdown_rect)

    def draw_in_progress(self, snake_list, snake_block_size, food_x, food_y):
        self.screen.fill(self.BLACK)
        self.draw_stop_button()
        for block in snake_list:
            pygame.draw.rect(self.screen, self.GREEN,
                             pygame.Rect(block[0], block[1], snake_block_size, snake_block_size))
        pygame.draw.rect(self.screen, self.RED, pygame.Rect(food_x, food_y, snake_block_size, snake_block_size))

    def draw_results(self, game_duration, game_score):
        self.screen.fill(self.WHITE)
        title_text = self.fonts['large'].render("게임 종료", True, self.BLACK)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(title_text, title_rect)
        duration_text = self.fonts['medium'].render(f"생존 시간: {int(game_duration)}초", True, self.BLACK)
        duration_rect = duration_text.get_rect(center=(self.screen_width // 2, 350))
        self.screen.blit(duration_text, duration_rect)
        score_text = self.fonts['medium'].render(f"최종 점수: {game_score}점", True, self.BLACK)
        score_rect = score_text.get_rect(center=(self.screen_width // 2, 450))
        self.screen.blit(score_text, score_rect)

        pygame.draw.rect(self.screen, self.GREEN, self.restart_button_rect, border_radius=10)
        restart_text = self.fonts['medium'].render("다시하기", True, self.WHITE)
        restart_rect = restart_text.get_rect(center=self.restart_button_rect.center)
        self.screen.blit(restart_text, restart_rect)

        pygame.draw.rect(self.screen, self.BLUE, self.main_menu_button_rect, border_radius=10)
        main_text = self.fonts['medium'].render("메인으로 돌아가기", True, self.WHITE)
        main_rect = main_text.get_rect(center=self.main_menu_button_rect.center)
        self.screen.blit(main_text, main_rect)