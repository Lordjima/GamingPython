"""
Classe de base abstraite pour tous les jeux.
Chaque jeu hérite de BaseGame et implémente update(), draw(), handle_event().
"""
import abc
import pygame
from client.core.settings import Settings
from client.core.api_client import APIClient


class BaseGame(abc.ABC):
    """Classe abstraite : boucle de jeu, HUD, soumission de score via API."""

    def __init__(self, screen: pygame.Surface, settings: Settings, player_name: str = "Player"):
        self.screen = screen
        self.settings = settings
        self.player_name = player_name
        self.api_client = APIClient(settings)
        self.clock = pygame.time.Clock()
        self.running = False
        self.score = 0
        self.game_over = False

        # Polices
        self.font_large = self._load_font(64)
        self.font_medium = self._load_font(36)
        self.font_small = self._load_font(22)

    def _load_font(self, size: int) -> pygame.font.Font:
        path = self.settings.FONTS_DIR / "Orbitron-Regular.ttf"
        if path.exists():
            return pygame.font.Font(str(path), size)
        return pygame.font.SysFont("segoeui", size, bold=True)

    @abc.abstractmethod
    def update(self, dt: float):
        """Met à jour l'état du jeu (appelé chaque frame)."""
        pass

    @abc.abstractmethod
    def draw(self):
        """Dessine le jeu sur l'écran."""
        pass

    @abc.abstractmethod
    def handle_event(self, event: pygame.event.Event):
        """Gère les événements clavier/souris."""
        pass

    @property
    @abc.abstractmethod
    def game_name(self) -> str:
        """Identifiant du jeu pour l'API (ex: 'snake')."""
        pass

    def run(self) -> int:
        """Boucle principale du jeu. Retourne le score final."""
        self.running = True
        self.game_over = False
        self.score = 0

        while self.running:
            dt = self.clock.tick(self.settings.FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                else:
                    self.handle_event(event)

            if not self.game_over:
                self.update(dt)

            self.draw()
            self.draw_hud()
            if self.game_over:
                self.draw_game_over()

            pygame.display.flip()

        # Soumission du score en arrière-plan
        if self.score > 0:
            self.api_client.submit_score_sync(self.game_name, self.player_name, self.score)

        return self.score

    def draw_hud(self):
        """HUD minimal : score en haut à gauche, ESC en bas."""
        W, H = self.screen.get_size()
        score_surf = self.font_small.render(f"SCORE  {self.score}", True, self.settings.COLOR_TEXT)
        # Fond semi-transparent derrière le score
        pad = 8
        bg = pygame.Surface((score_surf.get_width() + pad * 2, score_surf.get_height() + pad * 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        self.screen.blit(bg, (6, 6))
        self.screen.blit(score_surf, (6 + pad, 6 + pad))

        esc_surf = self.font_small.render("ESC — Quitter", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(esc_surf, (10, H - 30))

    def draw_game_over(self):
        """Overlay de fin de partie."""
        W, H = self.screen.get_size()
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        cx, cy = W // 2, H // 2

        go_surf = self.font_large.render("GAME OVER", True, self.settings.COLOR_SECONDARY)
        self.screen.blit(go_surf, go_surf.get_rect(center=(cx, cy - 70)))

        score_surf = self.font_medium.render(f"Score final : {self.score}", True, self.settings.COLOR_TEXT)
        self.screen.blit(score_surf, score_surf.get_rect(center=(cx, cy)))

        hint_surf = self.font_small.render("ESC — Retour au menu", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(hint_surf, hint_surf.get_rect(center=(cx, cy + 60)))
