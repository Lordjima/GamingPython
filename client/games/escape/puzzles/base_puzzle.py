"""Classe abstraite pour toutes les énigmes de l'escape game."""
from abc import ABC, abstractmethod
import pygame
from client.core.settings import Settings


class BasePuzzle(ABC):
    """
    Contrat commun à toutes les énigmes.
    Chaque sous-classe doit implémenter :
      - handle_event(event) → met à jour l'état interne
      - update(dt)           → animations / logique
      - draw(screen)         → rendu pygame
      - is_solved()          → True quand l'énigme est résolue
    """

    # Durée d'affichage du feedback (secondes)
    FEEDBACK_DURATION = 2.5

    def __init__(self, screen: pygame.Surface, settings: Settings, title: str, hint: str):
        self.screen = screen
        self.settings = settings
        self.title = title
        self.hint = hint

        self._solved = False
        self._failed = False
        self._feedback_msg = ""
        self._feedback_color = settings.COLOR_ERROR
        self._feedback_timer = 0.0

        # Polices partagées
        self.font_title = self._load_font(36)
        self.font_body  = self._load_font(22)
        self.font_small = self._load_font(17)
        self.font_mono  = self._load_mono(20)

    # ── Polices ──────────────────────────────────────────────────────────────

    def _load_font(self, size: int) -> pygame.font.Font:
        path = self.settings.FONTS_DIR / "Orbitron-Regular.ttf"
        if path.exists():
            return pygame.font.Font(str(path), size)
        return pygame.font.SysFont("segoeui", size, bold=True)

    def _load_mono(self, size: int) -> pygame.font.Font:
        for name in ("Courier New", "Consolas", "Lucida Console", "monospace"):
            try:
                return pygame.font.SysFont(name, size)
            except Exception:
                pass
        return pygame.font.SysFont("monospace", size)

    # ── API publique ─────────────────────────────────────────────────────────

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Traite un événement Pygame."""

    @abstractmethod
    def update(self, dt: float) -> None:
        """Met à jour la logique et les animations."""

    @abstractmethod
    def draw(self) -> None:
        """Dessine l'énigme sur self.screen."""

    def is_solved(self) -> bool:
        return self._solved

    def is_failed(self) -> bool:
        return self._failed

    # ── Helpers visuels partagés ─────────────────────────────────────────────

    def show_feedback(self, msg: str, success: bool = False):
        self._feedback_msg = msg
        self._feedback_color = self.settings.COLOR_SUCCESS if success else self.settings.COLOR_ERROR
        self._feedback_timer = self.FEEDBACK_DURATION

    def _update_feedback(self, dt: float):
        if self._feedback_timer > 0:
            self._feedback_timer -= dt

    def _draw_feedback(self):
        if self._feedback_timer > 0 and self._feedback_msg:
            W, H = self.screen.get_size()
            alpha = min(255, int(255 * self._feedback_timer / self.FEEDBACK_DURATION))
            surf = self.font_body.render(self._feedback_msg, True, self._feedback_color)
            surf.set_alpha(alpha)
            self.screen.blit(surf, surf.get_rect(center=(W // 2, H - 60)))

    def _draw_title_bar(self, subtitle: str = ""):
        """Bandeau de titre en haut de l'écran."""
        W, _ = self.screen.get_size()
        bar = pygame.Surface((W, 56), pygame.SRCALPHA)
        bar.fill((10, 10, 30, 210))
        self.screen.blit(bar, (0, 0))

        t_surf = self.font_title.render(self.title, True, self.settings.COLOR_ACCENT)
        self.screen.blit(t_surf, t_surf.get_rect(midleft=(20, 28)))

        if subtitle:
            s_surf = self.font_small.render(subtitle, True, self.settings.COLOR_TEXT_DIM)
            self.screen.blit(s_surf, s_surf.get_rect(midright=(W - 20, 28)))

    def _draw_hint_box(self, y_offset: int = 0):
        """Petit encadré d'indice en bas."""
        W, H = self.screen.get_size()
        hint_surf = self.font_small.render(f"💡 Indice : {self.hint}", True, self.settings.COLOR_WARNING)
        bx = (W - hint_surf.get_width() - 20) // 2
        by = H - 90 - y_offset
        bg = pygame.Surface((hint_surf.get_width() + 20, 30), pygame.SRCALPHA)
        bg.fill((40, 30, 0, 160))
        self.screen.blit(bg, (bx, by))
        self.screen.blit(hint_surf, (bx + 10, by + 5))

    def wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        """Coupe le texte en lignes selon la largeur max."""
        words = text.split()
        lines, current = [], ""
        for word in words:
            test = (current + " " + word).strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines
