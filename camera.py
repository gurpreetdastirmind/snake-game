import cv2
import mediapipe as mp
import pygame
import numpy as np
import sys
import random
from collections import deque

# --- CONFIGURATION ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
CELL_SIZE = 32  # Size of one square
GRID_WIDTH = SCREEN_WIDTH // CELL_SIZE  # 25 columns
GRID_HEIGHT = SCREEN_HEIGHT // CELL_SIZE  # 18 rows (THIS WAS THE BUG!)
FPS = 10

# Colors
BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
SNAKE_HEAD = (0, 255, 150)
SNAKE_BODY = (0, 180, 100)
FOOD_COLOR = (255, 0, 0)
UI_COLOR = (255, 255, 0)

# Initialize MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils


class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AI Snake - Fixed Grid Version")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Verdana", 28, bold=True)
        self.reset_game()

    def reset_game(self):
        self.snake = deque([[GRID_WIDTH // 2, GRID_HEIGHT // 2]])
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.food = self.generate_food()

    def generate_food(self):
        while True:
            # Pick coordinates within the NEW grid boundaries
            x = random.randint(1, GRID_WIDTH - 2)
            y = random.randint(2, GRID_HEIGHT - 2)
            new_food = [x, y]
            if new_food not in list(self.snake):
                return new_food

    def update_direction(self, finger_pos):
        if not finger_pos: return
        fx, fy = finger_pos
        hx, hy = self.snake[0][0] * CELL_SIZE + CELL_SIZE // 2, self.snake[0][1] * CELL_SIZE + CELL_SIZE // 2
        dx, dy = fx - hx, fy - hy

        if abs(dx) > 20 or abs(dy) > 20:
            if abs(dx) > abs(dy):
                new_dir = (1, 0) if dx > 0 else (-1, 0)
            else:
                new_dir = (0, 1) if dy > 0 else (0, -1)
            if (new_dir[0] * -1, new_dir[1] * -1) != self.direction:
                self.next_direction = new_dir

    def step(self):
        self.direction = self.next_direction
        head = self.snake[0]
        # Screen wrap using correct Width and Height
        new_head = [(head[0] + self.direction[0]) % GRID_WIDTH,
                    (head[1] + self.direction[1]) % GRID_HEIGHT]

        self.snake.appendleft(new_head)
        if new_head[0] == self.food[0] and new_head[1] == self.food[1]:
            self.score += 10
            self.food = self.generate_food()
        else:
            self.snake.pop()

    def draw(self, finger_pos):
        self.screen.fill(BLACK)

        # 1. DRAW FOOD (With visible white border)
        fx, fy = self.food[0] * CELL_SIZE + CELL_SIZE // 2, self.food[1] * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(self.screen, WHITE, (fx, fy), CELL_SIZE // 2)
        pygame.draw.circle(self.screen, FOOD_COLOR, (fx, fy), CELL_SIZE // 2 - 2)

        # 2. DRAW SNAKE
        for i, (sx, sy) in enumerate(self.snake):
            color = SNAKE_HEAD if i == 0 else SNAKE_BODY
            pygame.draw.rect(self.screen, color, (sx * CELL_SIZE + 1, sy * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2),
                             border_radius=4)

        # 3. DRAW UI
        if finger_pos:
            pygame.draw.circle(self.screen, UI_COLOR, finger_pos, 15, 2)

        score_surf = self.font.render(f"SCORE: {self.score}", True, WHITE)
        self.screen.blit(score_surf, (SCREEN_WIDTH // 2 - 60, 15))

        pygame.display.flip()


# Smoothing
smoothed_x, smoothed_y, alpha = 0, 0, 0.4


def get_finger_coords(cap):
    global smoothed_x, smoothed_y
    success, frame = cap.read()
    if not success: return None
    frame = cv2.flip(frame, 1)
    results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    if results.multi_hand_landmarks:
        tip = results.multi_hand_landmarks[0].landmark[8]
        tx, ty = int(tip.x * SCREEN_WIDTH), int(tip.y * SCREEN_HEIGHT)
        smoothed_x = (alpha * tx) + ((1 - alpha) * smoothed_x)
        smoothed_y = (alpha * ty) + ((1 - alpha) * smoothed_y)
        mp_draw.draw_landmarks(frame, results.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS)
        cv2.imshow("Hand Cam", frame)
        return (int(smoothed_x), int(smoothed_y))
    cv2.imshow("Hand Cam", frame)
    return None


def main():
    cap = cv2.VideoCapture(0)
    game = SnakeGame()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release();
                pygame.quit();
                sys.exit()

        f_pos = get_finger_coords(cap)
        game.update_direction(f_pos)
        game.step()
        game.draw(f_pos)
        game.clock.tick(FPS)
        if cv2.waitKey(1) & 0xFF == ord('q'): break


if __name__ == "__main__":
    main()