"""Menu des réglages — son, résolution."""
import pygame
from client.core.settings import Settings
from client.core.sound_manager import SoundManager


class SettingsMenu:
    RESOLUTIONS = [(1280, 720), (1366, 768), (1600, 900), (1920, 1080)]

    def __init__(self, screen: pygame.Surface, settings: Settings, sound_manager: SoundManager):
        self.screen = screen
        self.settings = settings
        self.sound_manager = sound_manager
        self.clock = pygame.time.Clock()
        self.running = True
        self.selected = 0

        self.font_title = self._load_font(44)
        self.font_item  = self._load_font(26)
        self.font_small = self._load_font(18)

        # Index résolution actuel
        cur_res = (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        self.res_index = self.RESOLUTIONS.index(cur_res) if cur_res in self.RESOLUTIONS else 0

        self.rows = [
            "Musique",
            "Volume musique",
            "Effets sonores",
            "Volume effets",
            "Résolution",
            "Plein écran",
            "─" * 20,
            "Sauvegarder et quitter",
        ]

    def _load_font(self, size: int) -> pygame.font.Font:
        path = self.settings.FONTS_DIR / "Orbitron-Regular.ttf"
        if path.exists():
            return pygame.font.Font(str(path), size)
        return pygame.font.SysFont("segoeui", size, bold=True)

    def run(self):
        while self.running:
            self.clock.tick(60)
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
                elif event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(self.rows)
                    if self.rows[self.selected].startswith("─"):
                        self.selected = (self.selected - 1) % len(self.rows)
                elif event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.rows)
                    if self.rows[self.selected].startswith("─"):
                        self.selected = (self.selected + 1) % len(self.rows)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._action(self.rows[self.selected])
                elif event.key == pygame.K_LEFT:
                    self._change(-1)
                elif event.key == pygame.K_RIGHT:
                    self._change(+1)

    def _action(self, row: str):
        if "Sauvegarder" in row:
            self.settings.save()
            self.running = False
        elif "Musique" == row:
            self.settings.MUSIC_ENABLED = not self.settings.MUSIC_ENABLED
        elif "Effets sonores" == row:
            self.settings.SFX_ENABLED = not self.settings.SFX_ENABLED
        elif "Plein écran" == row:
            self.settings.FULLSCREEN = not self.settings.FULLSCREEN

    def _change(self, direction: int):
        row = self.rows[self.selected]
        if "Volume musique" in row:
            new_vol = round(self.settings.MUSIC_VOLUME + direction * 0.1, 1)
            self.sound_manager.set_music_volume(new_vol)
        elif "Volume effets" in row:
            new_vol = round(self.settings.SFX_VOLUME + direction * 0.1, 1)
            self.sound_manager.set_sfx_volume(new_vol)
        elif "Résolution" in row:
            self.res_index = (self.res_index + direction) % len(self.RESOLUTIONS)
            w, h = self.RESOLUTIONS[self.res_index]
            self.settings.SCREEN_WIDTH = w
            self.settings.SCREEN_HEIGHT = h

    def _draw(self):
        W, H = self.screen.get_size()
        self.screen.fill(self.settings.COLOR_BG)

        title = self.font_title.render("⚙  RÉGLAGES", True, self.settings.COLOR_TEXT)
        self.screen.blit(title, title.get_rect(center=(W // 2, 50)))

        pygame.draw.line(self.screen, self.settings.COLOR_PRIMARY,
                         (W // 2 - 250, 85), (W // 2 + 250, 85), 1)

        row_h = 54
        start_y = 110
        col_x = W // 2 - 280

        for i, row in enumerate(self.rows):
            y = start_y + i * row_h
            is_sel = i == self.selected

            if row.startswith("─"):
                pygame.draw.line(self.screen, (60, 60, 90),
                                 (col_x, y + row_h // 2), (col_x + 560, y + row_h // 2), 1)
                continue

            if is_sel:
                sel_bg = pygame.Surface((560, row_h - 6), pygame.SRCALPHA)
                sel_bg.fill((*self.settings.COLOR_PRIMARY, 50))
                self.screen.blit(sel_bg, (col_x, y))
                pygame.draw.rect(self.screen, self.settings.COLOR_PRIMARY,
                                 (col_x, y, 560, row_h - 6), 1, border_radius=4)

            color = self.settings.COLOR_TEXT if is_sel else self.settings.COLOR_TEXT_DIM
            lbl = self.font_item.render(row, True, color)
            self.screen.blit(lbl, (col_x + 12, y + 10))

            # Valeur courante à droite
            val = self._get_value(row)
            if val:
                val_surf = self.font_item.render(val, True, self.settings.COLOR_ACCENT)
                self.screen.blit(val_surf, val_surf.get_rect(midright=(col_x + 548, y + row_h // 2 - 3)))

        hint = self.font_small.render(
            "↑↓ Naviguer  •  ←→ Modifier  •  ENTRÉE Confirmer  •  ESC Annuler",
            True, self.settings.COLOR_TEXT_DIM
        )
        self.screen.blit(hint, hint.get_rect(center=(W // 2, H - 20)))

    def _get_value(self, row: str) -> str:
        if row == "Musique":
            return "ON ✓" if self.settings.MUSIC_ENABLED else "OFF"
        elif row == "Volume musique":
            return f"{int(self.settings.MUSIC_VOLUME * 100)} %"
        elif row == "Effets sonores":
            return "ON ✓" if self.settings.SFX_ENABLED else "OFF"
        elif row == "Volume effets":
            return f"{int(self.settings.SFX_VOLUME * 100)} %"
        elif row == "Résolution":
            w, h = self.RESOLUTIONS[self.res_index]
            return f"{w} × {h}"
        elif row == "Plein écran":
            return "ON ✓" if self.settings.FULLSCREEN else "OFF"
        return ""
