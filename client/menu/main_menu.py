"""
Menu principal animé de Gaming Python.
Particules flottantes, items colorés avec effet hover, saisie du pseudo.
"""
import math
import sys
import json
import random
import threading
from typing import List, Optional
from pathlib import Path

import pygame

from client.core.settings import Settings
from client.core.sound_manager import SoundManager
from client.core.api_client import APIClient


# ─── Particule ──────────────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x: float, y: float, color: tuple):
        self.x = x
        self.y = y
        self.vx = random.uniform(-0.6, 0.6)
        self.vy = random.uniform(-1.2, -0.3)
        self.color = color
        self.size = random.randint(2, 4)
        self.life = 1.0

    def update(self, dt: float):
        self.x += self.vx
        self.y += self.vy
        self.life -= dt * 0.35

    @property
    def alpha(self) -> int:
        return max(0, int(self.life * 220))

    def is_dead(self) -> bool:
        return self.life <= 0


# ─── Élément de menu ────────────────────────────────────────────────────────────

class MenuItem:
    def __init__(self, label: str, color: tuple, action: str, description: str, icon: object = None):
        self.label = label
        self.color = color
        self.action = action
        self.description = description
        self.icon = icon  # pygame.Surface ou None
        self.hover: float = 0.0
        self.rect = pygame.Rect(0, 0, 0, 0)

    def update(self, dt: float, is_selected: bool):
        target = 1.0 if is_selected else 0.0
        self.hover += (target - self.hover) * 12 * dt
        self.hover = max(0.0, min(1.0, self.hover))  # clamp [0, 1]


# ─── Menu principal ──────────────────────────────────────────────────────────────

# (label, color, action, description, icon_file)
MENU_ITEMS_DATA = [
    ("Snake",        (60, 220, 120),  "snake",        "Mangez, grandissez, survivez !",              "icon_snake"),
    ("Tetris",       (130, 70, 255),  "tetris",       "Empilez les blocs, effacez les lignes !",     "icon_tetris"),
    ("Pong",         (60, 200, 255),  "pong",         "1 joueur vs IA — Classique arcade",           "icon_pong"),
    ("Escape Game",  (0, 230, 120),   "escape",       "5 salles · Enigmes · Interactivite OS",       "icon_escape"),
    ("Scores",       (255, 190, 50),  "leaderboard",  "Classements en ligne",                        "icon_scores"),
    ("Reglages",     (170, 170, 200), "settings",     "Son, resolution, theme",                      "icon_settings"),
    ("Quitter",      (255, 80,  80),  "quit",         "A bientot !",                                 "icon_quit"),
]


class MainMenu:
    def __init__(self, screen: pygame.Surface, settings: Settings, sound_manager: SoundManager):
        self.screen = screen
        self.settings = settings
        self.sound_manager = sound_manager
        self.api_client = APIClient(settings)
        self.clock = pygame.time.Clock()
        self.running = True
        self.time_elapsed = 0.0
        self.particles: List[Particle] = []
        self.selected_index = 0
        self.api_online = False

        # Polices
        self.font_title   = self._load_font(68)
        self.font_sub     = self._load_font(20)
        self.font_item    = self._load_font(34)
        self.font_small   = self._load_font(18)
        self.font_desc    = self._load_font(17)

        # Éléments de menu avec icônes
        icons_dir = settings.IMAGES_DIR / "icons"
        self.items = []
        icon_size = (38, 38)
        for label, color, action, desc, icon_file in MENU_ITEMS_DATA:
            icon_surf = None
            icon_path = icons_dir / f"{icon_file}.png"
            if icon_path.exists():
                try:
                    img = pygame.image.load(str(icon_path)).convert_alpha()
                    icon_surf = pygame.transform.smoothscale(img, icon_size)
                except Exception:
                    pass
            self.items.append(MenuItem(label, color, action, desc, icon_surf))

        # Assets
        self.bg_image   = self._load_image("background.png")
        self.logo_image = self._load_image("logo.png", (160, 160))

        # Vérification API asynchrone
        threading.Thread(target=self._check_api, daemon=True).start()

        # Demande du pseudo joueur
        self.player_name = self._ask_player_name()

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _load_font(self, size: int) -> pygame.font.Font:
        path = self.settings.FONTS_DIR / "Orbitron-Regular.ttf"
        if path.exists():
            return pygame.font.Font(str(path), size)
        return pygame.font.SysFont("segoeui", size, bold=True)

    def _load_image(self, name: str, size: tuple = None) -> Optional[pygame.Surface]:
        path = self.settings.IMAGES_DIR / name
        if not path.exists():
            return None
        try:
            img = pygame.image.load(str(path)).convert_alpha()
            if size:
                img = pygame.transform.smoothscale(img, size)
            return img
        except Exception:
            return None

    def _check_api(self):
        self.api_online = self.api_client.check_health()

    # ── Saisie du pseudo ─────────────────────────────────────────────────────

    def _ask_player_name(self) -> str:
        # Tente de lire depuis la sauvegarde
        save_path = Path(__file__).parent.parent.parent / "user_settings.json"
        if save_path.exists():
            try:
                with open(save_path) as f:
                    data = json.load(f)
                    if data.get("player_name"):
                        return data["player_name"]
            except Exception:
                pass

        name = ""
        asking = True
        t = 0.0

        while asking:
            dt = self.clock.tick(60) / 1000.0
            t += dt
            W, H = self.screen.get_size()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and len(name.strip()) >= 2:
                        asking = False
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        name = "Player"
                        asking = False
                    elif len(name) < 16 and event.unicode.isprintable():
                        name += event.unicode

            # Dessin
            self.screen.fill(self.settings.COLOR_BG)
            if self.bg_image:
                bg = pygame.transform.scale(self.bg_image, (W, H))
                bg.set_alpha(35)
                self.screen.blit(bg, (0, 0))

            bw, bh = 540, 300
            bx, by = (W - bw) // 2, (H - bh) // 2
            box = pygame.Surface((bw, bh), pygame.SRCALPHA)
            box.fill((15, 15, 45, 210))
            self.screen.blit(box, (bx, by))
            pygame.draw.rect(self.screen, self.settings.COLOR_PRIMARY, (bx, by, bw, bh), 2, border_radius=14)

            # Titre
            title = self.font_item.render("Votre pseudonyme", True, self.settings.COLOR_TEXT)
            self.screen.blit(title, title.get_rect(center=(W // 2, by + 55)))

            # Champ texte
            inp_rect = pygame.Rect(bx + 40, by + 105, bw - 80, 54)
            pygame.draw.rect(self.screen, (25, 25, 55), inp_rect, border_radius=8)
            pygame.draw.rect(self.screen, self.settings.COLOR_ACCENT, inp_rect, 2, border_radius=8)

            cursor = "|" if int(t * 2) % 2 == 0 else ""
            inp_surf = self.font_item.render(name + cursor, True, self.settings.COLOR_TEXT)
            self.screen.blit(inp_surf, inp_surf.get_rect(center=inp_rect.center))

            hint = self.font_small.render(
                "ENTRÉE pour confirmer  •  2 caractères minimum", True, self.settings.COLOR_TEXT_DIM
            )
            self.screen.blit(hint, hint.get_rect(center=(W // 2, by + 215)))

            pygame.display.flip()

        result = name.strip() or "Player"

        # Sauvegarde
        try:
            data = {}
            if save_path.exists():
                with open(save_path) as f:
                    data = json.load(f)
            data["player_name"] = result
            with open(save_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

        self.api_client.get_or_create_player(result)
        return result

    # ── Boucle principale ────────────────────────────────────────────────────

    def run(self):
        self.sound_manager.play_music("menu_music.ogg")
        while self.running:
            dt = self.clock.tick(self.settings.FPS) / 1000.0
            dt = min(dt, 0.05)  # cap dt pour éviter hover > 1.0 au premier frame
            self.time_elapsed += dt
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

    def _handle_events(self):
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.items)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.items)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._execute(self.items[self.selected_index].action)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for item in self.items:
                    if item.rect.collidepoint(mouse_pos):
                        self._execute(item.action)
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

        # Hover souris
        for i, item in enumerate(self.items):
            if item.rect.collidepoint(mouse_pos):
                self.selected_index = i

    def _execute(self, action: str):
        if action == "quit":
            self.running = False
        elif action in ("snake", "tetris", "pong"):
            self._launch_game(action)
        elif action == "escape":
            self._launch_escape()
        elif action == "leaderboard":
            from client.menu.leaderboard_menu import LeaderboardMenu
            LeaderboardMenu(self.screen, self.settings, self.api_client).run()
        elif action == "settings":
            from client.menu.settings_menu import SettingsMenu
            SettingsMenu(self.screen, self.settings, self.sound_manager).run()

    def _launch_game(self, name: str):
        self.sound_manager.stop_music()

        if name == "snake":
            from client.games.snake.snake_game import SnakeGame
            game = SnakeGame(self.screen, self.settings, self.player_name)
        elif name == "tetris":
            from client.games.tetris.tetris_game import TetrisGame
            game = TetrisGame(self.screen, self.settings, self.player_name)
        elif name == "pong":
            from client.games.pong.pong_game import PongGame
            game = PongGame(self.screen, self.settings, self.player_name)
        else:
            return

        game.run()
        self.sound_manager.play_music("menu_music.ogg")

    def _launch_escape(self):
        self.sound_manager.stop_music()
        from client.games.escape.escape_game import EscapeGame
        game = EscapeGame(self.screen, self.settings, self.player_name)
        game.run()
        self.sound_manager.play_music("menu_music.ogg")

    # ── Update ───────────────────────────────────────────────────────────────

    def _update(self, dt: float):
        W, H = self.screen.get_size()

        # Spawn particules
        if len(self.particles) < 80 and random.random() < 0.4:
            color = random.choice([
                self.settings.COLOR_PRIMARY,
                self.settings.COLOR_SECONDARY,
                self.settings.COLOR_ACCENT,
            ])
            self.particles.append(
                Particle(random.randint(0, W), random.randint(H // 2, H), color)
            )

        self.particles = [p for p in self.particles if not p.is_dead()]
        for p in self.particles:
            p.update(dt)

        # Hover
        for i, item in enumerate(self.items):
            item.update(dt, i == self.selected_index)

    # ── Draw ─────────────────────────────────────────────────────────────────

    def _draw(self):
        W, H = self.screen.get_size()
        self.screen.fill(self.settings.COLOR_BG)

        # Fond image
        if self.bg_image:
            bg = pygame.transform.scale(self.bg_image, (W, H))
            bg.set_alpha(38)
            self.screen.blit(bg, (0, 0))

        self._draw_circles(W, H)
        self._draw_particles()
        self._draw_header(W, H)
        self._draw_items(W, H)
        self._draw_footer(W, H)

    def _draw_circles(self, W: int, H: int):
        t = self.time_elapsed
        for i in range(5):
            r = 160 + i * 90
            alpha = int(12 + 8 * math.sin(t * 0.5 + i * 1.1))
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.settings.COLOR_PRIMARY, alpha), (r, r), r, 2)
            cx = W // 2 + int(40 * math.sin(t * 0.25 + i))
            cy = H // 2 + int(25 * math.cos(t * 0.18 + i))
            self.screen.blit(surf, (cx - r, cy - r))

    def _draw_particles(self):
        for p in self.particles:
            s = pygame.Surface((p.size * 2, p.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p.color, p.alpha), (p.size, p.size), p.size)
            self.screen.blit(s, (int(p.x) - p.size, int(p.y) - p.size))

    def _draw_header(self, W: int, H: int):
        t = self.time_elapsed
        logo_y = 24 + int(5 * math.sin(t * 1.1))

        if self.logo_image:
            self.screen.blit(self.logo_image, self.logo_image.get_rect(centerx=W // 2, y=logo_y))
            title_y = logo_y + 175
        else:
            title_y = 70

        # Ombre du titre
        glow = self.font_title.render("GAMING PYTHON", True, self.settings.COLOR_PRIMARY)
        glow.set_alpha(70)
        cx = W // 2
        self.screen.blit(glow, glow.get_rect(center=(cx + 3, title_y + 3)))

        # Titre principal
        title = self.font_title.render("GAMING PYTHON", True, self.settings.COLOR_TEXT)
        self.screen.blit(title, title.get_rect(center=(cx, title_y)))

        # Sous-titre
        sub = self.font_sub.render(f"Bienvenue, {self.player_name} 👾", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(sub, sub.get_rect(center=(cx, title_y + 52)))

    def _draw_items(self, W: int, H: int):
        n = len(self.items)
        item_h = 60
        total_h = n * item_h
        start_y = (H - total_h) // 2 + 90
        item_w = min(520, W - 80)
        item_x = (W - item_w) // 2

        for i, item in enumerate(self.items):
            y = start_y + i * item_h
            h = 52
            item.rect = pygame.Rect(item_x, y, item_w, h)
            hov = item.hover

            # Fond coloré
            bg = pygame.Surface((item_w, h), pygame.SRCALPHA)
            r, g, b = item.color
            bg.fill((r, g, b, max(0, min(255, int(35 + 115 * hov)))))
            self.screen.blit(bg, (item_x, y))

            # Barre gauche
            bar_w = int(4 + 4 * hov)
            pygame.draw.rect(self.screen, item.color, (item_x, y, bar_w, h))

            # Contour
            brd = pygame.Surface((item_w, h), pygame.SRCALPHA)
            pygame.draw.rect(brd, (*item.color, max(0, min(255, int(60 + 180 * hov)))), (0, 0, item_w, h), 1, border_radius=4)
            self.screen.blit(brd, (item_x, y))

            # Icône PNG
            icon_x = item_x + 10
            if item.icon:
                icon_y = y + (h - item.icon.get_height()) // 2
                # Légère transparence si pas sélectionné
                icon_copy = item.icon.copy()
                icon_copy.set_alpha(max(0, min(255, int(160 + 95 * hov))))
                self.screen.blit(icon_copy, (icon_x, icon_y))
                text_offset = item.icon.get_width() + 16
            else:
                text_offset = 10

            # Label
            txt_color = self.settings.COLOR_TEXT if hov < 0.1 else (
                tuple(min(255, int(c + (255 - c) * hov * 0.25)) for c in item.color)
            )
            lbl = self.font_item.render(item.label, True, txt_color)
            self.screen.blit(lbl, lbl.get_rect(midleft=(item_x + text_offset, y + h // 2)))

            # Description (apparaît au hover)
            if hov > 0.05 and item.description:
                desc = self.font_desc.render(item.description, True, self.settings.COLOR_TEXT_DIM)
                desc.set_alpha(max(0, min(255, int(255 * hov))))
                self.screen.blit(desc, desc.get_rect(midright=(item_x + item_w - 14, y + h // 2)))

    def _draw_footer(self, W: int, H: int):
        # Statut API
        color = self.settings.COLOR_SUCCESS if self.api_online else self.settings.COLOR_ERROR
        text = "● API connectée" if self.api_online else "● API hors ligne"
        api_surf = self.font_small.render(text, True, color)
        self.screen.blit(api_surf, (10, H - 28))

        # Touches
        ctrl = self.font_small.render("↑↓ Naviguer  •  ENTRÉE Sélectionner", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(ctrl, ctrl.get_rect(bottomright=(W - 10, H - 5)))
