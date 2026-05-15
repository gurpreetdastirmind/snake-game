import cv2
import mediapipe as mp
import pygame
import numpy as np
import sys
import random
from collections import deque

# --- CONFIGURATION ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
GRID_SIZE = 25
CELL_SIZE = SCREEN_WIDTH // GRID_SIZE
FPS = 10

# Colors
BLACK = (15, 15, 15)
WHITE = (255, 255, 255)
SNAKE_HEAD = (0, 255, 150)
SNAKE_BODY = (0, 180, 100)
FOOD_COLOR = (255, 50, 50)
UI_COLOR = (0, 255, 255)

# Initialize MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils


class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AI Snake - No Game Over Version")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Verdana", 24, bold=True)
        self.reset_game()

    def reset_game(self):
        self.snake = deque([[GRID_SIZE // 2, GRID_SIZE // 2]])
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.food = self.generate_food()
        self.score = 0
        self.game_over = False  # Keeping for logic, but we will prevent it

    def generate_food(self):
        while True:
            food = [random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)]
            if food not in self.snake: return food

    def update_direction(self, finger_pos):
        if not finger_pos: return

        fx, fy = finger_pos
        hx = self.snake[0][0] * CELL_SIZE + CELL_SIZE // 2
        hy = self.snake[0][1] * CELL_SIZE + CELL_SIZE // 2

        dx = fx - hx
        dy = fy - hy

        # Increased sensitivity for easier control
        threshold = 20
        if abs(dx) > threshold or abs(dy) > threshold:
            if abs(dx) > abs(dy):
                new_dir = (1, 0) if dx > 0 else (-1, 0)
            else:
                new_dir = (0, 1) if dy > 0 else (0, -1)

            # Allow turns, but prevent 180-degree snaps
            if len(self.snake) > 1:
                if (new_dir[0] * -1, new_dir[1] * -1) != self.direction:
                    self.next_direction = new_dir
            else:
                self.next_direction = new_dir

    def step(self):
        self.direction = self.next_direction
        head = self.snake[0]

        # --- SCREEN WRAPPING (PREVENTS WALL GAME OVER) ---
        new_head_x = (head[0] + self.direction[0]) % GRID_SIZE
        new_head_y = (head[1] + self.direction[1]) % GRID_SIZE
        new_head = [new_head_x, new_head_y]

        # Note: I removed the check for 'new_head in self.snake'
        # so you don't die if you hit your own body!

        self.snake.appendleft(new_head)
        if new_head == self.food:
            self.score += 10
            self.food = self.generate_food()
        else:
            self.snake.pop()

    def draw(self, finger_pos):
        self.screen.fill(BLACK)

        # Food
        px = self.food[0] * CELL_SIZE + CELL_SIZE // 2
        py = self.food[1] * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(self.screen, FOOD_COLOR, (px, py), CELL_SIZE // 2 - 2)

        # Snake
        for i, (sx, sy) in enumerate(self.snake):
            color = SNAKE_HEAD if i == 0 else SNAKE_BODY
            rect = (sx * CELL_SIZE + 1, sy * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2)
            pygame.draw.rect(self.screen, color, rect, border_radius=4)

        # Visual indicator of where you are pointing
        if finger_pos:
            pygame.draw.circle(self.screen, UI_COLOR, finger_pos, 8)

        score_surf = self.font.render(f"SCORE: {self.score}", True, WHITE)
        self.screen.blit(score_surf, (20, 20))
        pygame.display.flip()


# Smoothing Variables
smoothed_x, smoothed_y = 0, 0
alpha = 0.5


def get_finger_coords(cap):
    global smoothed_x, smoothed_y
    success, frame = cap.read()
    if not success: return None

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    finger_pixels = None
    if results.multi_hand_landmarks:
        hand = results.multi_hand_landmarks[0]
        tip = hand.landmark[8]

        tx, ty = int(tip.x * SCREEN_WIDTH), int(tip.y * SCREEN_HEIGHT)
        smoothed_x = (alpha * tx) + ((1 - alpha) * smoothed_x)
        smoothed_y = (alpha * ty) + ((1 - alpha) * smoothed_y)
        finger_pixels = (int(smoothed_x), int(smoothed_y))

        mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

    cv2.imshow("Hand Cam", frame)
    return finger_pixels


def main():
    cap = cv2.VideoCapture(0)
    game = SnakeGame()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()

        finger_pos = get_finger_coords(cap)
        game.update_direction(finger_pos)
        game.step()
        game.draw(finger_pos)

        game.clock.tick(FPS)
        if cv2.waitKey(1) & 0xFF == ord('q'): break


if __name__ == "__main__":
    main()