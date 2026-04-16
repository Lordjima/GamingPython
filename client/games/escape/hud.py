"""
HUD de l'escape game :
  - Chronomètre décompte (30 min par défaut)
  - Barre de progression des salles
  - Bouton d'indice (max 3)
  - Mini-instructions
"""
import math
import pygame
from client.core.settings import Settings


class EscapeHUD:
    TOTAL_ROOMS   = 5
    TOTAL_SECONDS = 30 * 60   # 30 minutes
    MAX_HINTS     = 3

    def __init__(self, screen: pygame.Surface, settings: Settings):
        self.screen   = screen
        self.settings = settings
        self.elapsed  = 0.0
        self.hints_used = 0
        self.rooms_cleared = 0
        self.hint_requested = False   # flag consommé par le moteur

        self.font_big   = self._font(32)
        self.font_mid   = self._font(20)
        self.font_small = self._font(15)

        # Rect du bouton indice
        self.hint_btn = pygame.Rect(0, 0, 0, 0)

    def _font(self, size: int) -> pygame.font.Font:
        path = self.settings.FONTS_DIR / "Orbitron-Regular.ttf"
        if path.exists():
            return pygame.font.Font(str(path), size)
        return pygame.font.SysFont("segoeui", size, bold=True)

    # ── Propriétés ────────────────────────────────────────────────────────────

    @property
    def remaining(self) -> float:
        return max(0.0, self.TOTAL_SECONDS - self.elapsed)

    @property
    def is_time_up(self) -> bool:
        return self.elapsed >= self.TOTAL_SECONDS

    @property
    def can_hint(self) -> bool:
        return self.hints_used < self.MAX_HINTS

    # ── Mise à jour ───────────────────────────────────────────────────────────

    def update(self, dt: float):
        self.elapsed += dt
        self.hint_requested = False   # reset chaque frame

    # ── Rendu ─────────────────────────────────────────────────────────────────

    def draw(self):
        W, H = self.screen.get_size()
        self._draw_top_bar(W)
        self._draw_hint_button(W, H)

    def _draw_top_bar(self, W: int):
        BAR_H = 44
        bar = pygame.Surface((W, BAR_H), pygame.SRCALPHA)
        bar.fill((6, 6, 22, 210))
        self.screen.blit(bar, (0, 0))
        pygame.draw.line(self.screen, self.settings.COLOR_PRIMARY, (0, BAR_H), (W, BAR_H), 1)

        # Chronomètre
        mins  = int(self.remaining) // 60
        secs  = int(self.remaining) % 60
        time_str = f"{mins:02d}:{secs:02d}"
        urgent = self.remaining < 300   # < 5 min
        pulse  = 0.5 + 0.5 * math.sin(self.elapsed * 6) if urgent else 1.0
        t_color = (int(255 * pulse), int(80 * pulse), int(80 * pulse)) if urgent else self.settings.COLOR_WARNING
        timer_s = self.font_big.render(f"⏱ {time_str}", True, t_color)
        self.screen.blit(timer_s, timer_s.get_rect(midleft=(12, BAR_H // 2)))

        # Progression salles
        prog_label = self.font_mid.render(
            f"Salle {self.rooms_cleared + 1}/{self.TOTAL_ROOMS}", True, self.settings.COLOR_TEXT
        )
        self.screen.blit(prog_label, prog_label.get_rect(center=(W // 2, BAR_H // 2)))

        # Barres de progression
        bar_total_w = 200
        bar_x = W // 2 - bar_total_w // 2 + prog_label.get_width() // 2 + 10
        bar_y = BAR_H // 2 - 5
        for i in range(self.TOTAL_ROOMS):
            bx = bar_x + i * 28
            color = self.settings.COLOR_SUCCESS if i < self.rooms_cleared else (40, 40, 70)
            if i == self.rooms_cleared:
                color = self.settings.COLOR_WARNING
            pygame.draw.rect(self.screen, color, (bx, bar_y, 20, 10), border_radius=3)

        # Indices restants
        hint_txt = self.font_small.render(
            f"💡 Indices : {self.MAX_HINTS - self.hints_used}/{self.MAX_HINTS}",
            True, self.settings.COLOR_TEXT_DIM,
        )
        self.screen.blit(hint_txt, hint_txt.get_rect(midright=(W - 12, BAR_H // 2)))

    def _draw_hint_button(self, W: int, H: int):
        """Bouton flottant en bas à droite."""
        bw, bh = 160, 38
        bx, by = W - bw - 12, H - bh - 12
        self.hint_btn = pygame.Rect(bx, by, bw, bh)

        enabled = self.can_hint
        bg_color = (40, 32, 10) if enabled else (30, 30, 40)
        bd_color = self.settings.COLOR_WARNING if enabled else (60, 60, 80)

        pygame.draw.rect(self.screen, bg_color, self.hint_btn, border_radius=8)
        pygame.draw.rect(self.screen, bd_color, self.hint_btn, 2, border_radius=8)

        label = f"💡 Indice ({self.MAX_HINTS - self.hints_used} restant{'s' if self.MAX_HINTS - self.hints_used > 1 else ''})"
        s = self.font_small.render(label, True, bd_color)
        self.screen.blit(s, s.get_rect(center=self.hint_btn.center))

    # ── Gestion du clic indice ────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Retourne True si un indice a été demandé."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hint_btn.collidepoint(event.pos) and self.can_hint:
                self.hints_used += 1
                self.hint_requested = True
                return True
        return False
