"""Menu leaderboard — affiche les top 10 via l'API FastAPI."""
import pygame
from typing import List, Dict
from client.core.settings import Settings
from client.core.api_client import APIClient

GAMES = [
    ("🐍 Snake",  "snake"),
    ("🧱 Tetris", "tetris"),
    ("🏓 Pong",   "pong"),
]


class LeaderboardMenu:
    def __init__(self, screen: pygame.Surface, settings: Settings, api_client: APIClient):
        self.screen = screen
        self.settings = settings
        self.api = api_client
        self.clock = pygame.time.Clock()
        self.running = True
        self.selected_game = 0
        self.entries: List[Dict] = []
        self.loading = True
        self.time_elapsed = 0.0

        self.font_title = self._load_font(44)
        self.font_tab   = self._load_font(26)
        self.font_row   = self._load_font(22)
        self.font_small = self._load_font(18)

        self._fetch()

    def _load_font(self, size: int) -> pygame.font.Font:
        path = self.settings.FONTS_DIR / "Orbitron-Regular.ttf"
        if path.exists():
            return pygame.font.Font(str(path), size)
        return pygame.font.SysFont("segoeui", size, bold=True)

    def _fetch(self):
        import threading
        def load():
            self.loading = True
            game_name = GAMES[self.selected_game][1]
            self.entries = self.api.get_leaderboard(game_name, limit=10)
            self.loading = False
        threading.Thread(target=load, daemon=True).start()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.time_elapsed += dt
            self._handle_events()
            self._draw()
            pygame.display.flip()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_LEFT:
                    self.selected_game = (self.selected_game - 1) % len(GAMES)
                    self._fetch()
                elif event.key == pygame.K_RIGHT:
                    self.selected_game = (self.selected_game + 1) % len(GAMES)
                    self._fetch()

    def _draw(self):
        W, H = self.screen.get_size()
        self.screen.fill(self.settings.COLOR_BG)

        # Titre
        title = self.font_title.render("🏆  LEADERBOARD", True, self.settings.COLOR_WARNING)
        self.screen.blit(title, title.get_rect(center=(W // 2, 50)))

        # Onglets jeux
        tab_w = 200
        total_tabs = len(GAMES) * tab_w
        tab_x = (W - total_tabs) // 2

        for i, (label, _) in enumerate(GAMES):
            rect = pygame.Rect(tab_x + i * tab_w, 100, tab_w - 10, 44)
            color = self.settings.COLOR_PRIMARY if i == self.selected_game else (50, 50, 80)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            lbl = self.font_tab.render(label, True, self.settings.COLOR_TEXT)
            self.screen.blit(lbl, lbl.get_rect(center=rect.center))

        # Tableau
        if self.loading:
            dots = "." * (int(self.time_elapsed * 3) % 4)
            msg = self.font_row.render(f"Chargement{dots}", True, self.settings.COLOR_TEXT_DIM)
            self.screen.blit(msg, msg.get_rect(center=(W // 2, H // 2)))
        elif not self.entries:
            msg = self.font_row.render("Aucun score enregistré.", True, self.settings.COLOR_TEXT_DIM)
            self.screen.blit(msg, msg.get_rect(center=(W // 2, H // 2)))
        else:
            col_w = 640
            col_x = (W - col_w) // 2
            row_h = 46
            start_y = 170

            # En-tête
            headers = [("#", 60), ("Joueur", 260), ("Score", 120), ("Date", 200)]
            hx = col_x
            for header, w in headers:
                h_surf = self.font_small.render(header, True, self.settings.COLOR_TEXT_DIM)
                self.screen.blit(h_surf, (hx, start_y))
                hx += w

            pygame.draw.line(self.screen, self.settings.COLOR_PRIMARY,
                             (col_x, start_y + 26), (col_x + col_w, start_y + 26), 1)

            medals = ["🥇", "🥈", "🥉"]
            for idx, entry in enumerate(self.entries[:10]):
                y = start_y + 36 + idx * row_h

                # Fond alterné
                if idx % 2 == 0:
                    row_bg = pygame.Surface((col_w, row_h - 4), pygame.SRCALPHA)
                    row_bg.fill((255, 255, 255, 8))
                    self.screen.blit(row_bg, (col_x, y))

                rank = medals[idx] if idx < 3 else str(idx + 1)
                row_data = [
                    (rank, 60),
                    (entry.get("player_name", "—")[:18], 260),
                    (str(entry.get("score", 0)), 120),
                    (entry.get("created_at", "")[:10], 200),
                ]
                rx = col_x
                for val, w in row_data:
                    color = self.settings.COLOR_WARNING if idx == 0 else self.settings.COLOR_TEXT
                    surf = self.font_row.render(val, True, color)
                    self.screen.blit(surf, (rx, y + 8))
                    rx += w

        # Pieds de page
        hint = self.font_small.render("← → Changer de jeu  •  ESC Retour", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(hint, hint.get_rect(center=(W // 2, H - 20)))
