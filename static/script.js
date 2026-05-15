class SnakeGameRenderer {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.gameLoop = null;
        this.isPaused = false;
        this.gameState = null;

        this.init();
        this.setupEventListeners();
        this.startGameLoop();
    }

    async init() {
        await this.fetchGameState();
        this.draw();
    }

    async fetchGameState() {
        try {
            const response = await fetch('/get_game_state');
            this.gameState = await response.json();
            this.updateUI();
        } catch (error) {
            console.error('Error fetching game state:', error);
        }
    }

    async stepGame() {
        if (this.isPaused) return;

        try {
            const response = await fetch('/step_game');
            this.gameState = await response.json();
            this.draw();
            this.updateUI();

            if (this.gameState.game_over) {
                this.showGameOver();
            }
        } catch (error) {
            console.error('Error stepping game:', error);
        }
    }

    async resetGame() {
        this.isPaused = false;
        try {
            const response = await fetch('/reset_game');
            this.gameState = await response.json();
            this.hideGameOver();
            this.draw();
            this.updateUI();
        } catch (error) {
            console.error('Error resetting game:', error);
        }
    }

    draw() {
        if (!this.gameState) return;

        const { snake, food, grid_width, grid_height, cell_size, game_over, finger_pos } = this.gameState;

        // Clear canvas with gradient background
        const gradient = this.ctx.createLinearGradient(0, 0, 0, this.canvas.height);
        gradient.addColorStop(0, '#0a0a2a');
        gradient.addColorStop(1, '#1a1a3a');
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw grid lines with glow effect
        this.ctx.strokeStyle = 'rgba(255,255,255,0.08)';
        this.ctx.lineWidth = 1;
        for (let i = 0; i <= grid_width; i++) {
            this.ctx.beginPath();
            this.ctx.moveTo(i * cell_size, 0);
            this.ctx.lineTo(i * cell_size, this.canvas.height);
            this.ctx.stroke();

            this.ctx.beginPath();
            this.ctx.moveTo(0, i * cell_size);
            this.ctx.lineTo(this.canvas.width, i * cell_size);
            this.ctx.stroke();
        }

        // Draw food with pulse effect
        const fx = food[0] * cell_size + cell_size / 2;
        const fy = food[1] * cell_size + cell_size / 2;

        this.ctx.shadowBlur = 15;
        this.ctx.shadowColor = '#ff4444';
        this.ctx.beginPath();
        this.ctx.arc(fx, fy, cell_size / 2, 0, Math.PI * 2);
        this.ctx.fillStyle = '#ffffff';
        this.ctx.fill();
        this.ctx.beginPath();
        this.ctx.arc(fx, fy, cell_size / 2 - 3, 0, Math.PI * 2);
        this.ctx.fillStyle = '#ff3232';
        this.ctx.fill();

        // Add food inner glow
        this.ctx.beginPath();
        this.ctx.arc(fx, fy, cell_size / 4, 0, Math.PI * 2);
        this.ctx.fillStyle = '#ff8888';
        this.ctx.fill();
        this.ctx.shadowBlur = 0;

        // Draw snake
        snake.forEach((segment, index) => {
            const x = segment[0] * cell_size;
            const y = segment[1] * cell_size;
            const isHead = index === 0;

            this.ctx.shadowBlur = isHead ? 10 : 5;
            this.ctx.shadowColor = '#00ff96';

            const gradient = this.ctx.createLinearGradient(x, y, x + cell_size, y + cell_size);
            if (isHead) {
                gradient.addColorStop(0, '#00ff96');
                gradient.addColorStop(1, '#00cc78');
            } else {
                gradient.addColorStop(0, '#00b460');
                gradient.addColorStop(1, '#009048');
            }

            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(x + 2, y + 2, cell_size - 4, cell_size - 4);

            // Draw scale pattern on body
            if (!isHead) {
                this.ctx.fillStyle = 'rgba(0,0,0,0.1)';
                this.ctx.fillRect(x + cell_size/3, y + 2, 2, cell_size - 4);
                this.ctx.fillRect(x + 2, y + cell_size/3, cell_size - 4, 2);
            }

            // Draw eyes on head
            if (isHead) {
                this.ctx.fillStyle = '#ffffff';
                const eyeSize = cell_size / 5;
                const eyeOffset = cell_size / 5;
                this.ctx.fillRect(x + cell_size - eyeOffset - eyeSize, y + eyeOffset, eyeSize, eyeSize);
                this.ctx.fillRect(x + eyeOffset, y + eyeOffset, eyeSize, eyeSize);
                this.ctx.fillStyle = '#000000';
                this.ctx.fillRect(x + cell_size - eyeOffset - eyeSize + 2, y + eyeOffset + 2, eyeSize - 4, eyeSize - 4);
                this.ctx.fillRect(x + eyeOffset + 2, y + eyeOffset + 2, eyeSize - 4, eyeSize - 4);

                // Add tongue for style
                this.ctx.beginPath();
                this.ctx.moveTo(x + cell_size/2, y + cell_size - 5);
                this.ctx.lineTo(x + cell_size/2 - 3, y + cell_size + 3);
                this.ctx.lineTo(x + cell_size/2, y + cell_size);
                this.ctx.lineTo(x + cell_size/2 + 3, y + cell_size + 3);
                this.ctx.fillStyle = '#ff4444';
                this.ctx.fill();
            }
        });

        this.ctx.shadowBlur = 0;

        // DRAW CLEAN YELLOW FINGER INDICATOR - NO TEXT, NO DOTTED LINES
        if (finger_pos && !game_over) {
            const [fx_pos, fy_pos] = finger_pos;

            // Outer glow
            this.ctx.shadowBlur = 20;
            this.ctx.shadowColor = '#ffcc00';

            // Large outer transparent circle (pulse effect)
            const time = Date.now() / 200;
            const pulse = 28 + Math.sin(time) * 6;
            this.ctx.beginPath();
            this.ctx.arc(fx_pos, fy_pos, pulse, 0, Math.PI * 2);
            this.ctx.fillStyle = 'rgba(255, 215, 0, 0.2)';
            this.ctx.fill();

            // Outer ring
            this.ctx.beginPath();
            this.ctx.arc(fx_pos, fy_pos, 22, 0, Math.PI * 2);
            this.ctx.strokeStyle = '#ffcc00';
            this.ctx.lineWidth = 3;
            this.ctx.stroke();

            // Main yellow circle
            this.ctx.beginPath();
            this.ctx.arc(fx_pos, fy_pos, 18, 0, Math.PI * 2);
            this.ctx.fillStyle = '#ffcc00';
            this.ctx.fill();

            // Inner orange gradient
            const gradientCircle = this.ctx.createRadialGradient(fx_pos - 3, fy_pos - 3, 3, fx_pos, fy_pos, 15);
            gradientCircle.addColorStop(0, '#ffaa00');
            gradientCircle.addColorStop(1, '#ff6600');
            this.ctx.beginPath();
            this.ctx.arc(fx_pos, fy_pos, 12, 0, Math.PI * 2);
            this.ctx.fillStyle = gradientCircle;
            this.ctx.fill();

            // White bright center
            this.ctx.beginPath();
            this.ctx.arc(fx_pos - 2, fy_pos - 2, 3, 0, Math.PI * 2);
            this.ctx.fillStyle = '#ffffff';
            this.ctx.fill();

            this.ctx.shadowBlur = 0;

            // Add subtle shine effect
            this.ctx.beginPath();
            this.ctx.arc(fx_pos - 5, fy_pos - 5, 2, 0, Math.PI * 2);
            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            this.ctx.fill();

        } else if (finger_pos && game_over) {
            // Dimmed indicator when game over
            this.ctx.beginPath();
            this.ctx.arc(finger_pos[0], finger_pos[1], 20, 0, Math.PI * 2);
            this.ctx.fillStyle = 'rgba(255, 200, 0, 0.3)';
            this.ctx.fill();
            this.ctx.beginPath();
            this.ctx.arc(finger_pos[0], finger_pos[1], 14, 0, Math.PI * 2);
            this.ctx.fillStyle = 'rgba(255, 180, 0, 0.5)';
            this.ctx.fill();
        }

        // Draw game over effect
        if (game_over) {
            this.ctx.fillStyle = 'rgba(0,0,0,0.75)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

            this.ctx.font = 'bold 48px Orbitron';
            this.ctx.fillStyle = '#ff4757';
            this.ctx.shadowBlur = 10;
            this.ctx.shadowColor = '#ff0000';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('GAME OVER', this.canvas.width/2, this.canvas.height/2 - 40);
            this.ctx.font = '24px Orbitron';
            this.ctx.fillStyle = '#ffffff';
            this.ctx.fillText('Press R or click RESET', this.canvas.width/2, this.canvas.height/2 + 30);
            this.ctx.textAlign = 'left';
            this.ctx.shadowBlur = 0;
        }
    }

    updateUI() {
        if (!this.gameState) return;

        document.getElementById('scoreDisplay').textContent = this.gameState.score;

        const statusDisplay = document.getElementById('statusDisplay');

        if (this.gameState.game_over) {
            statusDisplay.innerHTML = '<span class="status-dot gameover"></span> Game Over';
        } else if (this.isPaused) {
            statusDisplay.innerHTML = '<span class="status-dot"></span> Paused';
        } else {
            statusDisplay.innerHTML = '<span class="status-dot playing"></span> Playing';
        }
    }

    showGameOver() {
        const overlay = document.getElementById('gameOverlay');
        document.getElementById('finalScore').textContent = this.gameState.score;
        overlay.classList.remove('hidden');
    }

    hideGameOver() {
        const overlay = document.getElementById('gameOverlay');
        overlay.classList.add('hidden');
    }

    togglePause() {
        this.isPaused = !this.isPaused;
        this.updateUI();
        this.draw();
    }

    setupEventListeners() {
        document.getElementById('resetBtn').addEventListener('click', () => this.resetGame());
        document.getElementById('manualResetBtn').addEventListener('click', () => this.resetGame());

        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space') {
                e.preventDefault();
                this.togglePause();
            } else if (e.code === 'KeyR') {
                this.resetGame();
            }
        });
    }

    startGameLoop() {
        setInterval(() => {
            this.stepGame();
        }, 100);
    }
}

// Initialize game when page loads
window.addEventListener('load', () => {
    new SnakeGameRenderer();
});