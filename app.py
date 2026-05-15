from flask import Flask, render_template, Response, jsonify
import cv2
import mediapipe as mp
import numpy as np
from collections import deque
import random
import os
import time

app = Flask(__name__)

# --- GAME CONFIGURATION ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
CELL_SIZE = 32
GRID_WIDTH = SCREEN_WIDTH // CELL_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // CELL_SIZE

# Initialize MediaPipe with error handling
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1
)
mp_draw = mp.solutions.drawing_utils


class SnakeGame:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.snake = deque([[GRID_WIDTH // 2, GRID_HEIGHT // 2]])
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.game_over = False
        self.food = self.generate_food()
        self.current_finger_pos = None

    def generate_food(self):
        while True:
            x = random.randint(1, GRID_WIDTH - 2)
            y = random.randint(2, GRID_HEIGHT - 2)
            new_food = [x, y]
            if new_food not in list(self.snake):
                return new_food

    def update_direction(self, finger_pos):
        if not finger_pos or self.game_over:
            return

        self.current_finger_pos = finger_pos

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
        if self.game_over:
            return

        self.direction = self.next_direction
        head = self.snake[0]
        new_head = [(head[0] + self.direction[0]) % GRID_WIDTH,
                    (head[1] + self.direction[1]) % GRID_HEIGHT]

        if new_head in list(self.snake)[1:]:
            self.game_over = True
            return

        self.snake.appendleft(new_head)
        if new_head[0] == self.food[0] and new_head[1] == self.food[1]:
            self.score += 10
            self.food = self.generate_food()
        else:
            self.snake.pop()

    def get_game_state(self):
        return {
            'snake': list(self.snake),
            'food': self.food,
            'score': self.score,
            'game_over': self.game_over,
            'grid_width': GRID_WIDTH,
            'grid_height': GRID_HEIGHT,
            'cell_size': CELL_SIZE,
            'finger_pos': self.current_finger_pos
        }


game_state = SnakeGame()
smoothed_x, smoothed_y, alpha = 0, 0, 0.4
current_finger_for_game = None


def generate_frames():
    global smoothed_x, smoothed_y, current_finger_for_game

    # Try to open camera (will work on Render if available, otherwise show placeholder)
    cap = None
    try:
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap and cap.isOpened():
                print(f"Camera opened successfully with index {i}")
                break
    except Exception as e:
        print(f"Camera error: {e}")
        cap = None

    while True:
        if cap is None or not cap.isOpened():
            # Create a placeholder frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "Camera Feed", (250, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, "Move mouse to control snake", (180, 250),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # Mouse control fallback
            import pygame
            pygame.init()
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos:
                finger_pos = mouse_pos
                current_finger_for_game = finger_pos
                game_state.update_direction(finger_pos)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1)
            continue

        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        finger_pos = None

        if results.multi_hand_landmarks:
            tip = results.multi_hand_landmarks[0].landmark[8]
            tx, ty = int(tip.x * SCREEN_WIDTH), int(tip.y * SCREEN_HEIGHT)
            smoothed_x = (alpha * tx) + ((1 - alpha) * smoothed_x)
            smoothed_y = (alpha * ty) + ((1 - alpha) * smoothed_y)

            mp_draw.draw_landmarks(frame, results.multi_hand_landmarks[0], mp_hands.HAND_CONNECTIONS)

            cv2.circle(frame, (int(smoothed_x), int(smoothed_y)), 20, (0, 255, 255), -1)
            cv2.circle(frame, (int(smoothed_x), int(smoothed_y)), 25, (255, 255, 255), 3)
            cv2.circle(frame, (int(smoothed_x), int(smoothed_y)), 8, (255, 100, 0), -1)

            finger_pos = (int(smoothed_x), int(smoothed_y))
            current_finger_for_game = finger_pos

            game_state.update_direction(finger_pos)
        else:
            current_finger_for_game = None

        cv2.putText(frame, "SHOW INDEX FINGER TO CONTROL SNAKE", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_game_state')
def get_game_state():
    return jsonify(game_state.get_game_state())


@app.route('/reset_game')
def reset_game():
    game_state.reset_game()
    return jsonify({'status': 'reset'})


@app.route('/step_game')
def step_game():
    game_state.step()
    return jsonify(game_state.get_game_state())


@app.route('/mouse_control', methods=['POST'])
def mouse_control():
    """Fallback control for testing without camera"""
    from flask import request
    data = request.json
    if data and 'x' in data and 'y' in data:
        game_state.update_direction((data['x'], data['y']))
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)