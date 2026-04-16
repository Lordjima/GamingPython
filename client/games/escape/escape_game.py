"""
Moteur principal de l'Escape Game.
FSM : intro → room_1..5 → victory / timeout
Gère la progression, les transitions, la communication API.
"""
import math
import sys
import threading
import pygame
from client.core.settings import Settings
from client.core.api_client import APIClient
from .hud import EscapeHUD
from .puzzles.terminal_puzzle    import TerminalPuzzle
from .puzzles.cipher_puzzle      import CipherPuzzle
from .puzzles.network_puzzle     import NetworkPuzzle
from .puzzles.filesystem_puzzle  import FilesystemPuzzle
from .puzzles.binary_puzzle      import BinaryPuzzle


ROOM_NAMES = [
    "🖥  Le Terminal Fantôme",
    "🔑  Le Chiffre Perdu",
    "🌐  Le Réseau Corrompu",
    "📁  Le Fichier Caché",
    "💻  Le Code Final",
]

ROOM_COLORS = [
    (0, 200, 80),       # vert terminal
    (100, 60, 255),     # violet chiffrement
    (60, 200, 255),     # bleu réseau
    (220, 80, 220),     # rose filesystem
    (255, 200, 0),      # or binaire
]

# Descriptions narratives (affichées en overlay avant chaque salle)
ROOM_INTROS = [
    ("Salle 1", "Un terminal abandonné tourne encore.\nTrouvez le code de confinement du processus fantôme."),
    ("Salle 2", "Un message chiffré a été intercepté.\nDécodez-le pour obtenir le mot de passe."),
    ("Salle 3", "Des paquets corrompus circulent sur le réseau.\nReconstituer l'adresse IP de la cible."),
    ("Salle 4", "Un fichier secret est caché dans le système.\nNaviguez dans l'arborescence pour le trouver."),
    ("Salle 5", "Le code final est encodé en binaire.\nDécodez-le — c'est votre seule chance de liberté."),
]


class EscapeGame:

    STATE_INTRO      = "intro"
    STATE_ROOM       = "room"
    STATE_TRANSITION = "transition"
    STATE_VICTORY    = "victory"
    STATE_TIMEOUT    = "timeout"

    def __init__(self, screen: pygame.Surface, settings: Settings, player_name: str):
        self.screen      = screen
        self.settings    = settings
        self.player_name = player_name
        self.api_client  = APIClient(settings)
        self.clock       = pygame.time.Clock()
        self.running     = True
        self.state       = self.STATE_INTRO

        self.current_room    = 0   # 0-based index
        self.session_id: int | None = None

        # HUD
        self.hud = EscapeHUD(screen, settings)

        # Intro
        self.intro_t     = 0.0
        self.intro_done  = False

        # Transition entre salles
        self.trans_t     = 0.0
        self.TRANS_DUR   = 1.8   # secondes

        # Score final
        self.final_score      = 0
        self.final_duration   = 0

        # Polices
        self.font_title = self._font(52)
        self.font_body  = self._font(26)
        self.font_small = self._font(18)

        # Puzzle actuel
        self.puzzle = None

        # Démarre la session en arrière-plan
        threading.Thread(target=self._start_api_session, daemon=True).start()

    # ── API ───────────────────────────────────────────────────────────────────

    def _start_api_session(self):
        try:
            resp = self.api_client._post("/escape/start", {"player_name": self.player_name})
            if resp:
                self.session_id = resp.get("session_id")
        except Exception:
            pass   # mode hors-ligne silencieux

    def _notify_room_cleared(self, room_number: int, hint_used: bool):
        if not self.session_id:
            return
        try:
            self.api_client._post(
                f"/escape/{self.session_id}/room",
                {"room_number": room_number, "hint_used": hint_used},
                method="put",
            )
        except Exception:
            pass

    def _complete_session(self):
        if not self.session_id:
            return
        try:
            resp = self.api_client._post(f"/escape/{self.session_id}/complete", {})
            if resp:
                self.final_score = resp.get("score", 0)
        except Exception:
            pass

    # ── Polices ───────────────────────────────────────────────────────────────

    def _font(self, size: int) -> pygame.font.Font:
        path = self.settings.FONTS_DIR / "Orbitron-Regular.ttf"
        if path.exists():
            return pygame.font.Font(str(path), size)
        return pygame.font.SysFont("segoeui", size, bold=True)

    # ── Puzzles ───────────────────────────────────────────────────────────────

    def _build_puzzle(self, room_idx: int):
        constructors = [
            TerminalPuzzle,
            CipherPuzzle,
            NetworkPuzzle,
            FilesystemPuzzle,
            BinaryPuzzle,
        ]
        return constructors[room_idx](self.screen, self.settings)

    # ── Boucle principale ─────────────────────────────────────────────────────

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            dt = min(dt, 0.05)

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                else:
                    self._handle_event(event)

            self._update(dt)
            self._draw()
            pygame.display.flip()

    def _handle_event(self, event: pygame.event.Event):
        if self.state == self.STATE_INTRO:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self._enter_room(0)

        elif self.state == self.STATE_ROOM and self.puzzle:
            # Indice via HUD
            self.hud.handle_event(event)
            # Puzzle
            self.puzzle.handle_event(event)
            # Avancer quand résolu
            if self.puzzle.is_solved():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self._advance_room()

        elif self.state == self.STATE_VICTORY:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.running = False

        elif self.state == self.STATE_TIMEOUT:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.running = False

    def _update(self, dt: float):
        if self.state == self.STATE_INTRO:
            self.intro_t += dt

        elif self.state == self.STATE_ROOM:
            self.hud.update(dt)
            if self.puzzle:
                self.puzzle.update(dt)
            if self.hud.is_time_up:
                self._enter_timeout()

        elif self.state == self.STATE_TRANSITION:
            self.trans_t += dt
            if self.trans_t >= self.TRANS_DUR:
                self._enter_room(self.current_room)

        elif self.state == self.STATE_VICTORY:
            self.hud.update(dt)

    def _draw(self):
        if self.state == self.STATE_INTRO:
            self._draw_intro()
        elif self.state == self.STATE_ROOM:
            if self.puzzle:
                self.puzzle.draw()
            self.hud.draw()
        elif self.state == self.STATE_TRANSITION:
            self._draw_transition()
        elif self.state == self.STATE_VICTORY:
            self._draw_victory()
        elif self.state == self.STATE_TIMEOUT:
            self._draw_timeout()

    # ── Transitions d'état ────────────────────────────────────────────────────

    def _enter_room(self, idx: int):
        self.current_room = idx
        self.hud.rooms_cleared = idx
        self.puzzle = self._build_puzzle(idx)
        self.state = self.STATE_ROOM
        self.trans_t = 0.0

    def _advance_room(self):
        hint_used = self.hud.hint_requested
        threading.Thread(
            target=self._notify_room_cleared,
            args=(self.current_room + 1, hint_used),
            daemon=True,
        ).start()

        next_room = self.current_room + 1
        if next_room >= 5:
            self.hud.rooms_cleared = 5
            self.final_duration = int(self.hud.elapsed)
            threading.Thread(target=self._complete_session, daemon=True).start()
            self.state = self.STATE_VICTORY
        else:
            self.state = self.STATE_TRANSITION
            self.trans_t = 0.0
            self.current_room = next_room

    def _enter_timeout(self):
        threading.Thread(target=self._complete_session, daemon=True).start()
        self.state = self.STATE_TIMEOUT

    # ── Dessins d'état ────────────────────────────────────────────────────────

    def _draw_intro(self):
        W, H = self.screen.get_size()
        t = self.intro_t
        self.screen.fill(self.settings.COLOR_BG)

        # Cercles animés
        for i in range(6):
            r = 100 + i * 70
            alpha = int(20 + 15 * math.sin(t * 0.6 + i))
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.settings.COLOR_PRIMARY, alpha), (r, r), r, 2)
            self.screen.blit(surf, (W // 2 - r, H // 2 - r))

        # Titre
        glow = self.font_title.render("🔐 ESCAPE GAME INFORMATIQUE", True, self.settings.COLOR_PRIMARY)
        glow.set_alpha(60)
        self.screen.blit(glow, glow.get_rect(center=(W // 2 + 3, H // 2 - 100 + 3)))
        title = self.font_title.render("🔐 ESCAPE GAME INFORMATIQUE", True, self.settings.COLOR_TEXT)
        self.screen.blit(title, title.get_rect(center=(W // 2, H // 2 - 100)))

        sub = self.font_body.render(
            f"Bienvenue, {self.player_name} — 5 salles, 30 minutes, aucune erreur permise.",
            True, self.settings.COLOR_TEXT_DIM,
        )
        self.screen.blit(sub, sub.get_rect(center=(W // 2, H // 2 - 30)))

        # Liste des salles
        for i, (num, desc) in enumerate(ROOM_INTROS):
            color = ROOM_COLORS[i]
            s = self.font_small.render(f"  {num} : {desc.split(chr(10))[0]}", True, color)
            self.screen.blit(s, s.get_rect(center=(W // 2, H // 2 + 30 + i * 32)))

        # Blink ESPACE
        if int(t * 2) % 2 == 0:
            start = self.font_body.render("Appuyez sur ESPACE pour commencer", True, self.settings.COLOR_ACCENT)
            self.screen.blit(start, start.get_rect(center=(W // 2, H - 60)))

    def _draw_transition(self):
        W, H = self.screen.get_size()
        progress = self.trans_t / self.TRANS_DUR

        self.screen.fill((0, 0, 0))
        # Scan-line effect
        line_count = int(H * progress)
        color = ROOM_COLORS[min(self.current_room, 4)]
        for y in range(0, line_count, 3):
            alpha = max(0, int(180 * (1 - progress)))
            s = pygame.Surface((W, 2), pygame.SRCALPHA)
            s.fill((*color, alpha))
            self.screen.blit(s, (0, y))

        # Texte salle suivante
        idx = min(self.current_room, 4)
        title = self.font_title.render(ROOM_NAMES[idx], True, ROOM_COLORS[idx])
        alpha = int(255 * min(1.0, progress * 2))
        title.set_alpha(alpha)
        self.screen.blit(title, title.get_rect(center=(W // 2, H // 2)))

        sub = self.font_body.render(ROOM_INTROS[idx][1].split("\n")[0], True, self.settings.COLOR_TEXT_DIM)
        sub.set_alpha(alpha)
        self.screen.blit(sub, sub.get_rect(center=(W // 2, H // 2 + 60)))

    def _draw_victory(self):
        W, H = self.screen.get_size()
        t = self.hud.elapsed
        self.screen.fill((4, 12, 4))

        # Pluie de caractères verts
        for i in range(30):
            x = (i * 67 + int(t * 40)) % W
            y = (i * 113 + int(t * 80)) % H
            fnt = pygame.font.SysFont("Consolas", 16)
            ch = chr(0x30A0 + (i * 7 + int(t * 10)) % 96)
            s = fnt.render(ch, True, (0, 180, 0))
            s.set_alpha(60)
            self.screen.blit(s, (x, y))

        lines = [
            "🎉  FÉLICITATIONS !",
            f"   {self.player_name}, vous avez résolu toutes les énigmes !",
            f"   Salles : 5/5   •   Temps : {self.final_duration // 60}m{self.final_duration % 60:02d}s",
            f"   Score : {self.final_score} pts",
            "",
            "   Appuyez sur ESPACE pour revenir au menu",
        ]
        colors = [
            self.settings.COLOR_SUCCESS,
            self.settings.COLOR_TEXT,
            self.settings.COLOR_ACCENT,
            self.settings.COLOR_WARNING,
            self.settings.COLOR_TEXT,
            self.settings.COLOR_TEXT_DIM,
        ]
        for i, (line, color) in enumerate(zip(lines, colors)):
            s = self.font_body.render(line, True, color)
            self.screen.blit(s, s.get_rect(center=(W // 2, H // 2 - 120 + i * 50)))

    def _draw_timeout(self):
        W, H = self.screen.get_size()
        self.screen.fill((20, 4, 4))

        lines = [
            "⏰  TEMPS ÉCOULÉ",
            f"Vous avez débloqué {self.hud.rooms_cleared}/5 salles.",
            "Le système vous a expulsé.",
            "",
            "Appuyez sur ESPACE pour réessayer",
        ]
        colors = [
            self.settings.COLOR_ERROR,
            self.settings.COLOR_TEXT,
            self.settings.COLOR_TEXT_DIM,
            self.settings.COLOR_TEXT,
            self.settings.COLOR_TEXT_DIM,
        ]
        for i, (line, color) in enumerate(zip(lines, colors)):
            s = self.font_body.render(line, True, color)
            self.screen.blit(s, s.get_rect(center=(W // 2, H // 2 - 100 + i * 52)))
