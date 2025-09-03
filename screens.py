# screens.py

import pygame

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

    def draw_back_button(self):
        button_rect = pygame.Rect(30, 30, 150, 50)
        pygame.draw.rect(self.screen, self.GRAY, button_rect, border_radius=10)
        text_surface = self.fonts['small'].render("뒤로가기", True, self.BLACK)
        text_rect = text_surface.get_rect(center=button_rect.center)
        self.screen.blit(text_surface, text_rect)
        return button_rect

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
        self.draw_back_button()  # 뒤로가기 버튼 추가
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
        self.draw_back_button()  # 뒤로가기 버튼 추가
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

    def draw_snake_game(self):
        self.screen.fill(self.BLACK)
        self.draw_back_button()  # 뒤로가기 버튼 추가
        game_title = self.fonts['large'].render("뱀 게임", True, self.WHITE)
        game_title_rect = game_title.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(game_title, game_title_rect)
        message_text = self.fonts['medium'].render("이곳에 뱀 게임 코드를 구현하면 됩니다.", True, self.GRAY)
        message_rect = message_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(message_text, message_rect)
        exit_text = self.fonts['small'].render("게임을 종료하려면 'ESC'를 누르세요.", True, self.GRAY)
        exit_rect = exit_text.get_rect(center=(self.screen_width // 2, self.screen_height - 100))
        self.screen.blit(exit_text, exit_rect)