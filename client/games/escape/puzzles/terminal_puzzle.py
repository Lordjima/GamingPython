"""
Salle 1 — Terminal Fantôme
Le joueur doit taper la bonne séquence de commandes dans un pseudo-terminal.
Certaines commandes (whoami, hostname, echo, dir) appellent le vrai OS via subprocess.
"""
import math
import os
import random
import subprocess
import pygame
from client.core.settings import Settings
from .base_puzzle import BasePuzzle

# Commandes réelles autorisées (whitelist stricte)
SAFE_COMMANDS = {"whoami", "hostname", "echo", "ver"}

# Scénario : l'admin a laissé un mot de passe dans le système
# Le joueur doit découvrir le "secret" caché dans les sorties OS
SECRET_CODE = "GHOST_7749"

NARRATIVE = (
    "⚠  ALERTE : Accès non autorisé détecté.\n"
    "Un processus fantôme tourne sur ce système.\n"
    "Identifiez la machine, puis tapez le code de confinement :\n"
    "Commandes disponibles : help, whoami, hostname, dir, echo <texte>, clear\n"
    "Objectif : taper  confinement GHOST_7749"
)

HELP_TEXT = [
    "  whoami      — Qui êtes-vous ?",
    "  hostname    — Nom de cette machine",
    "  dir         — Liste le répertoire courant (vrai OS)",
    "  echo <txt>  — Affiche du texte",
    "  ver         — Version du système",
    "  clear       — Efface le terminal",
    "  confinement <CODE> — Soumet le code de confinement",
]


class TerminalPuzzle(BasePuzzle):
    MAX_HISTORY = 200   # lignes max dans le buffer
    MAX_INPUT   = 80

    def __init__(self, screen: pygame.Surface, settings: Settings):
        super().__init__(
            screen, settings,
            title="🖥  SALLE 1 — LE TERMINAL FANTÔME",
            hint="Essayez whoami et hostname, puis cherchez le code GHOST_****",
        )
        self.input_text  = ""
        self.history: list[tuple[str, tuple]] = []  # (texte, couleur)
        self.cursor_vis  = True
        self.cursor_tick = 0.0
        self.glitch_t    = 0.0
        self._boot_sequence()

    # ── Init ──────────────────────────────────────────────────────────────────

    def _boot_sequence(self):
        self._print("╔══════════════════════════════════════════╗", self.settings.COLOR_PRIMARY)
        self._print("║  GHOST TERMINAL v3.1  — ACCÈS CRITIQUE   ║", self.settings.COLOR_PRIMARY)
        self._print("╚══════════════════════════════════════════╝", self.settings.COLOR_PRIMARY)
        self._print("")
        for line in NARRATIVE.split("\n"):
            self._print(line, self.settings.COLOR_WARNING)
        self._print("")
        self._print(f"Le code de confinement est fragmenté dans le système.", self.settings.COLOR_TEXT_DIM)
        self._print(f"Fragment 1/2 : GHOST_", self.settings.COLOR_TEXT_DIM)
        self._print(f"Fragment 2/2 : [résultat numérique de hostname | derniers 4 chiffres = 7749]", self.settings.COLOR_TEXT_DIM)
        self._print("")

    def _print(self, text: str, color: tuple = None):
        color = color or self.settings.COLOR_TEXT
        self.history.append((text, color))
        if len(self.history) > self.MAX_HISTORY:
            self.history.pop(0)

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._run_command(self.input_text.strip())
                self.input_text = ""
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_UP:
                pass   # TODO : historique des commandes
            elif len(self.input_text) < self.MAX_INPUT and event.unicode.isprintable():
                self.input_text += event.unicode

    def _run_command(self, cmd: str):
        self._print(f"root@ghost:~$ {cmd}", self.settings.COLOR_ACCENT)
        if not cmd:
            return

        parts = cmd.split(None, 1)
        verb  = parts[0].lower()
        arg   = parts[1] if len(parts) > 1 else ""

        if verb == "help":
            for line in HELP_TEXT:
                self._print(line, self.settings.COLOR_TEXT_DIM)

        elif verb == "clear":
            self.history.clear()

        elif verb == "confinement":
            if arg.strip().upper() == SECRET_CODE:
                self._print("✅  CODE ACCEPTÉ — Processus fantôme confiné !", self.settings.COLOR_SUCCESS)
                self._print("🔓  SALLE DÉVERROUILLÉE", self.settings.COLOR_SUCCESS)
                self._solved = True
            else:
                self._print(f"❌  Code invalide : '{arg}'", self.settings.COLOR_ERROR)
                self._print("    Continuez à explorer le système…", self.settings.COLOR_TEXT_DIM)

        elif verb in SAFE_COMMANDS or verb == "dir":
            output = self._call_os(verb, arg)
            for line in output.split("\n")[:30]:   # max 30 lignes
                self._print(line, self.settings.COLOR_TEXT)

        else:
            self._print(f"Commande inconnue : '{verb}'. Tapez 'help'.", self.settings.COLOR_ERROR)

    def _call_os(self, verb: str, arg: str) -> str:
        try:
            if verb == "whoami":
                return subprocess.check_output("whoami", shell=True, text=True, timeout=3).strip()
            elif verb == "hostname":
                return subprocess.check_output("hostname", shell=True, text=True, timeout=3).strip()
            elif verb == "echo":
                return arg if arg else ""
            elif verb == "ver":
                return subprocess.check_output("ver", shell=True, text=True, timeout=3).strip()
            elif verb == "dir":
                return subprocess.check_output("dir", shell=True, text=True, timeout=3, stderr=subprocess.STDOUT)
        except subprocess.TimeoutExpired:
            return "[timeout]"
        except Exception as e:
            return f"[erreur : {e}]"
        return ""

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float):
        self._update_feedback(dt)
        self.cursor_tick += dt
        if self.cursor_tick >= 0.5:
            self.cursor_vis = not self.cursor_vis
            self.cursor_tick = 0.0
        self.glitch_t += dt

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self):
        W, H = self.screen.get_size()

        # Fond noir style terminal
        self.screen.fill((4, 8, 4))

        # Effet scanlines (légères lignes horizontales)
        for y in range(0, H, 4):
            alpha = 12 + int(4 * math.sin(y * 0.05 + self.glitch_t * 2))
            s = pygame.Surface((W, 1), pygame.SRCALPHA)
            s.fill((0, 0, 0, alpha))
            self.screen.blit(s, (0, y))

        self._draw_title_bar()

        # Zone terminal
        PADDING  = 14
        INPUT_H  = 40
        start_y  = 64
        end_y    = H - INPUT_H - 20
        term_h   = end_y - start_y

        line_h   = self.font_mono.get_height() + 2
        max_lines = term_h // line_h
        visible   = self.history[-max_lines:] if len(self.history) > max_lines else self.history

        for i, (text, color) in enumerate(visible):
            surf = self.font_mono.render(text, True, color)
            self.screen.blit(surf, (PADDING, start_y + i * line_h))

        # Barre de saisie
        bar_y = H - INPUT_H - 10
        pygame.draw.rect(self.screen, (10, 25, 10), (0, bar_y, W, INPUT_H + 10))
        pygame.draw.line(self.screen, self.settings.COLOR_SUCCESS, (0, bar_y), (W, bar_y), 1)

        prompt = "root@ghost:~$ "
        cursor_char = "█" if self.cursor_vis else " "
        line = prompt + self.input_text + cursor_char
        inp_surf = self.font_mono.render(line, True, self.settings.COLOR_SUCCESS)
        self.screen.blit(inp_surf, (PADDING, bar_y + 8))

        self._draw_feedback()
        if self._solved:
            self._draw_solved_overlay(W, H)

    def _draw_solved_overlay(self, W: int, H: int):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 30, 0, 120))
        self.screen.blit(overlay, (0, 0))
        msg = self.font_title.render("🔓  SALLE DÉVERROUILLÉE — Appuyez sur ESPACE", True, self.settings.COLOR_SUCCESS)
        self.screen.blit(msg, msg.get_rect(center=(W // 2, H // 2)))
