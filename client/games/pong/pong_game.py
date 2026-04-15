"""
Jeu Pong — 1 joueur vs IA, effets de balles colorées.
"""
import pygame
import random
import math
from client.core.game_base import BaseGame
from client.core.settings import Settings


class PongGame(BaseGame):
    PADDLE_W = 14
    PADDLE_H = 90
    BALL_SIZE = 14
    PADDLE_SPEED = 380.0
    AI_SPEED = 320.0
    BALL_SPEED_INIT = 320.0
    BALL_SPEED_MAX = 620.0

    @property
    def game_name(self) -> str:
        return "pong"

    def __init__(self, screen: pygame.Surface, settings: Settings, player_name: str = "Player"):
        super().__init__(screen, settings, player_name)
        self._reset()

    def _reset(self):
        W, H = self.screen.get_size()
        self.player_y = H // 2 - self.PADDLE_H // 2
        self.ai_y     = H // 2 - self.PADDLE_H // 2
        self.score = 0
        self.ai_score = 0
        self._serve()
        self.game_over = False
        self.trail: list = []

    def _serve(self):
        W, H = self.screen.get_size()
        self.ball_x = float(W // 2)
        self.ball_y = float(H // 2)
        angle = random.uniform(-0.6, 0.6)
        direction = random.choice([-1, 1])
        self.ball_vx = direction * self.BALL_SPEED_INIT * math.cos(angle)
        self.ball_vy = self.BALL_SPEED_INIT * math.sin(angle)
        self.ball_speed = self.BALL_SPEED_INIT

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and self.game_over:
            self._reset()

    def update(self, dt: float):
        W, H = self.screen.get_size()
        keys = pygame.key.get_pressed()

        # Joueur
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.player_y -= self.PADDLE_SPEED * dt
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.player_y += self.PADDLE_SPEED * dt
        self.player_y = max(0, min(H - self.PADDLE_H, self.player_y))

        # IA simple — suit la balle
        ai_center = self.ai_y + self.PADDLE_H // 2
        if ai_center < self.ball_y - 8:
            self.ai_y += self.AI_SPEED * dt
        elif ai_center > self.ball_y + 8:
            self.ai_y -= self.AI_SPEED * dt
        self.ai_y = max(0, min(H - self.PADDLE_H, self.ai_y))

        # Mouvement balle
        self.trail.append((int(self.ball_x), int(self.ball_y)))
        if len(self.trail) > 12:
            self.trail.pop(0)

        self.ball_x += self.ball_vx * dt
        self.ball_y += self.ball_vy * dt

        # Rebond haut/bas
        if self.ball_y <= 0:
            self.ball_y = 0
            self.ball_vy = abs(self.ball_vy)
        elif self.ball_y >= H - self.BALL_SIZE:
            self.ball_y = H - self.BALL_SIZE
            self.ball_vy = -abs(self.ball_vy)

        # Paddle gauche (joueur)
        p_rect = pygame.Rect(30, int(self.player_y), self.PADDLE_W, self.PADDLE_H)
        b_rect = pygame.Rect(int(self.ball_x), int(self.ball_y), self.BALL_SIZE, self.BALL_SIZE)

        if b_rect.colliderect(p_rect) and self.ball_vx < 0:
            self.ball_vx = abs(self.ball_vx) * 1.05
            hit_pos = (self.ball_y + self.BALL_SIZE / 2 - self.player_y) / self.PADDLE_H
            self.ball_vy = (hit_pos - 0.5) * 2 * self.ball_speed
            self.ball_speed = min(self.ball_speed * 1.05, self.BALL_SPEED_MAX)

        # Paddle droit (IA)
        ai_rect = pygame.Rect(W - 30 - self.PADDLE_W, int(self.ai_y), self.PADDLE_W, self.PADDLE_H)
        if b_rect.colliderect(ai_rect) and self.ball_vx > 0:
            self.ball_vx = -abs(self.ball_vx) * 1.05
            hit_pos = (self.ball_y + self.BALL_SIZE / 2 - self.ai_y) / self.PADDLE_H
            self.ball_vy = (hit_pos - 0.5) * 2 * self.ball_speed
            self.ball_speed = min(self.ball_speed * 1.05, self.BALL_SPEED_MAX)

        # Point
        if self.ball_x < 0:
            self.ai_score += 1
            if self.ai_score >= 7:
                self.game_over = True
            else:
                self._serve()
        elif self.ball_x > W:
            self.score += 1
            self._serve()

    def draw(self):
        W, H = self.screen.get_size()
        self.screen.fill((8, 8, 22))

        # Ligne centrale
        for y in range(0, H, 20):
            pygame.draw.rect(self.screen, (40, 40, 70), (W // 2 - 2, y, 4, 12))

        # Traîne balle
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(180 * i / len(self.trail))
            r = max(2, self.BALL_SIZE // 2 * i // len(self.trail))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 180, 255, alpha), (r, r), r)
            self.screen.blit(s, (tx - r, ty - r))

        # Balle
        bx, by = int(self.ball_x), int(self.ball_y)
        center = (bx + self.BALL_SIZE // 2, by + self.BALL_SIZE // 2)
        pygame.draw.circle(self.screen, (255, 255, 255), center, self.BALL_SIZE // 2)

        # Glow balle
        glow = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(glow, (100, 180, 255, 60), (20, 20), 18)
        self.screen.blit(glow, (center[0] - 20, center[1] - 20))

        # Paddles
        p_rect = pygame.Rect(30, int(self.player_y), self.PADDLE_W, self.PADDLE_H)
        pygame.draw.rect(self.screen, self.settings.COLOR_PRIMARY, p_rect, border_radius=6)

        ai_rect = pygame.Rect(W - 30 - self.PADDLE_W, int(self.ai_y), self.PADDLE_W, self.PADDLE_H)
        pygame.draw.rect(self.screen, self.settings.COLOR_SECONDARY, ai_rect, border_radius=6)

        # Scores
        s_player = self.font_large.render(str(self.score), True, self.settings.COLOR_PRIMARY)
        s_ai = self.font_large.render(str(self.ai_score), True, self.settings.COLOR_SECONDARY)
        self.screen.blit(s_player, s_player.get_rect(center=(W // 4, 50)))
        self.screen.blit(s_ai, s_ai.get_rect(center=(W * 3 // 4, 50)))

        # Labels
        you = self.font_small.render(self.player_name, True, self.settings.COLOR_TEXT_DIM)
        ai  = self.font_small.render("IA", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(you, you.get_rect(center=(W // 4, 100)))
        self.screen.blit(ai,  ai.get_rect(center=(W * 3 // 4, 100)))

        if self.game_over:
            result = "✓ VICTOIRE !" if self.score > self.ai_score else "✗ Défaite..."
            color = self.settings.COLOR_SUCCESS if self.score > self.ai_score else self.settings.COLOR_ERROR
            res_surf = self.font_medium.render(result, True, color)
            self.screen.blit(res_surf, res_surf.get_rect(center=(W // 2, H // 2 - 20)))
            hint = self.font_small.render("R — Rejouer", True, self.settings.COLOR_SUCCESS)
            self.screen.blit(hint, hint.get_rect(center=(W // 2, H // 2 + 40)))
