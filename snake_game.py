import pygame
import random


class SnakeGame:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.speed = 8
        self.block_size = 20
        self.logger = None  # Will be set by main.py
        self.reset_game()

    def reset_game(self):
        self.snake_list = []
        self.snake_length = 1
        # Align snake starting position to grid
        grid_x = (self.screen_width // self.block_size) // 2
        grid_y = (self.screen_height // self.block_size) // 2
        self.x = grid_x * self.block_size
        self.y = grid_y * self.block_size
        self.direction = "RIGHT"
        self.change_to = self.direction
        self.score = 0
        # Simplified food positioning - align to block grid  
        self.food_x = random.randint(0, (self.screen_width // self.block_size) - 1) * self.block_size
        self.food_y = random.randint(0, (self.screen_height // self.block_size) - 1) * self.block_size
        self.game_over = False

    def update_direction_from_message(self, message):
        """Update direction based on watch message"""
        current_direction = self.direction
        if message == "1":  # Device 1: Counter-clockwise
            if current_direction == "UP":
                self.change_to = "LEFT"
            elif current_direction == "LEFT":
                self.change_to = "DOWN"
            elif current_direction == "DOWN":
                self.change_to = "RIGHT"
            elif current_direction == "RIGHT":
                self.change_to = "UP"
        elif message == "2":  # Device 2: Clockwise
            if current_direction == "UP":
                self.change_to = "RIGHT"
            elif current_direction == "RIGHT":
                self.change_to = "DOWN"
            elif current_direction == "DOWN":
                self.change_to = "LEFT"
            elif current_direction == "LEFT":
                self.change_to = "UP"

    def update_direction_from_keyboard(self, key):
        """Update direction based on keyboard input"""
        if key == pygame.K_UP and not self.direction == "DOWN":
            self.change_to = "UP"
        elif key == pygame.K_DOWN and not self.direction == "UP":
            self.change_to = "DOWN"
        elif key == pygame.K_LEFT and not self.direction == "RIGHT":
            self.change_to = "LEFT"
        elif key == pygame.K_RIGHT and not self.direction == "LEFT":
            self.change_to = "RIGHT"

    def update_game_state(self):
        """Update game state (movement, collision, score)"""
        if self.change_to == "UP" and not self.direction == "DOWN":
            self.direction = "UP"
        elif self.change_to == "DOWN" and not self.direction == "UP":
            self.direction = "DOWN"
        elif self.change_to == "LEFT" and not self.direction == "RIGHT":
            self.direction = "LEFT"
        elif self.change_to == "RIGHT" and not self.direction == "LEFT":
            self.direction = "RIGHT"

        if self.direction == "UP":
            self.y -= self.block_size
        elif self.direction == "DOWN":
            self.y += self.block_size
        elif self.direction == "LEFT":
            self.x -= self.block_size
        elif self.direction == "RIGHT":
            self.x += self.block_size

        self.snake_list.append([self.x, self.y])
        if len(self.snake_list) > self.snake_length:
            del self.snake_list[0]
        
        # Debug: Show positions when snake is near fruit
        distance_to_fruit = abs(self.x - self.food_x) + abs(self.y - self.food_y)
        if distance_to_fruit <= self.block_size:
            print(f"DEBUG - Snake head: ({self.x}, {self.y}), Fruit: ({self.food_x}, {self.food_y}), Distance: {distance_to_fruit}")

        if self.x < 0 or self.x >= self.screen_width or self.y < 0 or self.y >= self.screen_height:
            self.game_over = True
        for block in self.snake_list[:-1]:
            if block == [self.x, self.y]:
                self.game_over = True

        if self.x == self.food_x and self.y == self.food_y:
            print(f"FRUIT EATEN! Score: {self.score + 1}")
            self.snake_length += 1
            self.score += 1
            # Log fruit eating event
            if self.logger:
                self.logger.log_game_event('fruit_eaten', {
                    'score': self.score,
                    'snake_length': self.snake_length,
                    'fruit_position': (self.food_x, self.food_y)
                })
            # Simplified food positioning - align to block grid
            self.food_x = random.randint(0, (self.screen_width // self.block_size) - 1) * self.block_size
            self.food_y = random.randint(0, (self.screen_height // self.block_size) - 1) * self.block_size
            print(f"New fruit position: ({self.food_x}, {self.food_y})")

        return self.game_over

    def draw_debug_grid(self, screen, screen_manager):
        """Draw grid lines for debugging alignment"""
        for x in range(0, self.screen_width, self.block_size):
            pygame.draw.line(screen, (40, 40, 40), (x, 0), (x, self.screen_height))
        for y in range(0, self.screen_height, self.block_size):
            pygame.draw.line(screen, (40, 40, 40), (0, y), (self.screen_width, y))

    def draw_game(self, screen, screen_manager):
        """Function to draw snake and food on screen"""
        screen.fill(screen_manager.BLACK)
        screen_manager.draw_stop_button()
        
        # Optional: Draw grid lines for debugging (comment out for production)
        # self.draw_debug_grid(screen, screen_manager)

        # Draw snake body
        for i, block in enumerate(self.snake_list):
            if i == len(self.snake_list) - 1:  # Head (last element)
                # Draw head
                pygame.draw.rect(screen, screen_manager.BLUE,
                                 pygame.Rect(block[0], block[1], self.block_size, self.block_size))
                
                # Draw eyes based on direction
                eye_size = 3
                head_x, head_y = block[0], block[1]
                
                if self.direction == "RIGHT":
                    # Eyes on the right side
                    eye1_pos = (head_x + self.block_size - 6, head_y + 4)
                    eye2_pos = (head_x + self.block_size - 6, head_y + self.block_size - 8)
                elif self.direction == "LEFT":
                    # Eyes on the left side
                    eye1_pos = (head_x + 3, head_y + 4)
                    eye2_pos = (head_x + 3, head_y + self.block_size - 8)
                elif self.direction == "UP":
                    # Eyes on the top
                    eye1_pos = (head_x + 4, head_y + 3)
                    eye2_pos = (head_x + self.block_size - 8, head_y + 3)
                elif self.direction == "DOWN":
                    # Eyes on the bottom
                    eye1_pos = (head_x + 4, head_y + self.block_size - 6)
                    eye2_pos = (head_x + self.block_size - 8, head_y + self.block_size - 6)
                
                # Draw white eyes
                pygame.draw.circle(screen, screen_manager.WHITE, eye1_pos, eye_size)
                pygame.draw.circle(screen, screen_manager.WHITE, eye2_pos, eye_size)
                
            else:  # Body
                pygame.draw.rect(screen, screen_manager.GREEN,
                                 pygame.Rect(block[0], block[1], self.block_size, self.block_size))

        pygame.draw.rect(screen, screen_manager.RED,
                         pygame.Rect(self.food_x, self.food_y, self.block_size, self.block_size))

        score_text = screen_manager.fonts['medium'].render(f"Score: {self.score}", True, screen_manager.WHITE)
        score_rect = score_text.get_rect(topleft=(20, 20))
        screen.blit(score_text, score_rect)
