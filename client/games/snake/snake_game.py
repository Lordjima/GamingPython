"""
Jeu Snake complet — niveaux, accélération, soumission score API.
"""
import pygame
import random
from client.core.game_base import BaseGame
from client.core.settings import Settings

GRID = 20          # taille d'une cellule en pixels
COLS = 40          # nombre de colonnes
ROWS = 28          # nombre de lignes


class SnakeGame(BaseGame):
    @property
    def game_name(self) -> str:
        return "snake"

    def __init__(self, screen: pygame.Surface, settings: Settings, player_name: str = "Player"):
        super().__init__(screen, settings, player_name)
        self._reset()

    def _reset(self):
        self.snake = [(COLS // 2, ROWS // 2)]
        self.direction = (1, 0)
        self.next_dir = (1, 0)
        self.food = self._spawn_food()
        self.score = 0
        self.level = 1
        self.speed = 8.0       # cells/sec
        self._move_acc = 0.0
        self.game_over = False
        self.particles: list = []

    def _spawn_food(self):
        while True:
            pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
            if pos not in self.snake:
                return pos

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.game_over:
                self._reset()
            dirs = {
                pygame.K_UP:    (0, -1), pygame.K_w: (0, -1),
                pygame.K_DOWN:  (0,  1), pygame.K_s: (0,  1),
                pygame.K_LEFT:  (-1, 0), pygame.K_a: (-1, 0),
                pygame.K_RIGHT: ( 1, 0), pygame.K_d: ( 1, 0),
            }
            if event.key in dirs:
                nd = dirs[event.key]
                # Empêche demi-tour
                if (nd[0] + self.direction[0], nd[1] + self.direction[1]) != (0, 0):
                    self.next_dir = nd

    def update(self, dt: float):
        # Particules
        self.particles = [(x, y, a - 4) for x, y, a in self.particles if a > 0]

        self._move_acc += dt
        step = 1.0 / self.speed

        if self._move_acc >= step:
            self._move_acc -= step
            self.direction = self.next_dir
            head = (
                (self.snake[0][0] + self.direction[0]) % COLS,
                (self.snake[0][1] + self.direction[1]) % ROWS,
            )

            # Collision avec soi-même
            if head in self.snake:
                self.game_over = True
                return

            self.snake.insert(0, head)

            if head == self.food:
                self.score += 10 * self.level
                self.food = self._spawn_food()
                # Particules de nourriture
                fx, fy = head
                for _ in range(8):
                    ox, oy = random.randint(-2, 2), random.randint(-2, 2)
                    self.particles.append((fx * GRID + ox, fy * GRID + oy, 255))
                # Accélération par niveau
                if len(self.snake) % 5 == 0:
                    self.level += 1
                    self.speed = min(8.0 + self.level * 1.5, 24.0)
            else:
                self.snake.pop()

    def draw(self):
        W, H = self.screen.get_size()

        # Calcul offset pour centrer la grille
        grid_w = COLS * GRID
        grid_h = ROWS * GRID
        off_x = (W - grid_w) // 2
        off_y = (H - grid_h) // 2 + 20

        self.screen.fill(self.settings.COLOR_BG)

        # Grille de fond
        for col in range(COLS):
            for row in range(ROWS):
                rect = pygame.Rect(off_x + col * GRID, off_y + row * GRID, GRID, GRID)
                pygame.draw.rect(self.screen, (18, 18, 40), rect)
                pygame.draw.rect(self.screen, (28, 28, 55), rect, 1)

        # Particules
        for px, py, alpha in self.particles:
            s = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 200, 60, alpha), (4, 4), 4)
            self.screen.blit(s, (off_x + px * GRID - 4, off_y + py * GRID - 4))

        # Nourriture (pulsante)
        t = pygame.time.get_ticks() / 1000
        pulse = int(3 * abs(pygame.math.Vector2(1, 0).rotate(t * 200).x))
        fx, fy = self.food
        food_rect = pygame.Rect(
            off_x + fx * GRID + 2 - pulse // 2,
            off_y + fy * GRID + 2 - pulse // 2,
            GRID - 4 + pulse,
            GRID - 4 + pulse,
        )
        pygame.draw.ellipse(self.screen, (255, 80, 80), food_rect)
        pygame.draw.ellipse(self.screen, (255, 140, 140), food_rect, 2)

        # Serpent
        for i, (cx, cy) in enumerate(self.snake):
            ratio = 1 - (i / len(self.snake)) * 0.6
            color = (
                int(60 * ratio),
                int(220 * ratio),
                int(120 * ratio),
            )
            rect = pygame.Rect(off_x + cx * GRID + 1, off_y + cy * GRID + 1, GRID - 2, GRID - 2)
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            if i == 0:
                pygame.draw.rect(self.screen, (200, 255, 200), rect, 1, border_radius=4)

        # Niveau
        lvl_surf = self.font_small.render(f"NIVEAU {self.level}", True, self.settings.COLOR_ACCENT)
        self.screen.blit(lvl_surf, (W - lvl_surf.get_width() - 10, 10))

        # Hint restart
        if self.game_over:
            hint = self.font_small.render("R — Rejouer", True, self.settings.COLOR_SUCCESS)
            self.screen.blit(hint, hint.get_rect(center=(W // 2, H // 2 + 110)))
