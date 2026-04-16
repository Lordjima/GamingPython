"""
Salle 2 — Le Chiffre Perdu
Décode un message chiffré (César aléatoire) pour trouver le mot de passe.
Un vrai fichier .enc est généré sur le disque dans %TEMP%/escape_game/.
"""
import math
import os
import random
import string
import tempfile
from pathlib import Path
import pygame
from client.core.settings import Settings
from .base_puzzle import BasePuzzle


SECRET_WORD = "CRYPTEX"
ALPHABET    = string.ascii_uppercase


def caesar_encode(text: str, shift: int) -> str:
    result = []
    for ch in text.upper():
        if ch in ALPHABET:
            result.append(ALPHABET[(ALPHABET.index(ch) + shift) % 26])
        else:
            result.append(ch)
    return "".join(result)


class CipherPuzzle(BasePuzzle):

    def __init__(self, screen: pygame.Surface, settings: Settings):
        super().__init__(
            screen, settings,
            title="🔑  SALLE 2 — LE CHIFFRE PERDU",
            hint=f"Le décalage est entre 1 et 13. Essayez plusieurs valeurs !",
        )
        self.shift      = random.randint(3, 13)
        self.ciphered   = caesar_encode(SECRET_WORD, self.shift)
        self.input_text = ""
        self.anim_t     = 0.0
        self.file_path  = self._write_enc_file()

        # Lettres affichées une par une (animation intro)
        self.reveal_idx = 0
        self.reveal_t   = 0.0

    # ── Génère le fichier .enc sur le disque ──────────────────────────────────

    def _write_enc_file(self) -> Path:
        folder = Path(tempfile.gettempdir()) / "escape_game"
        folder.mkdir(exist_ok=True)
        path = folder / "puzzle.enc"
        content = (
            f"=== GHOST TERMINAL — FICHIER CHIFFRÉ ===\n"
            f"Algorithme : César\n"
            f"Décalage   : [CLASSIFIÉ]\n"
            f"Message    : {self.ciphered}\n"
            f"⚠ Déchiffrez ce message pour obtenir le mot de passe.\n"
        )
        path.write_text(content, encoding="utf-8")
        return path

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._check_answer()
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif len(self.input_text) < 12 and event.unicode.isalpha():
                self.input_text += event.unicode.upper()

    def _check_answer(self):
        if self.input_text.strip() == SECRET_WORD:
            self._solved = True
            self.show_feedback("✅  MOT DE PASSE CORRECT — SALLE DÉVERROUILLÉE !", success=True)
        else:
            self.show_feedback(f"❌  '{self.input_text}' est incorrect. Réessayez.", success=False)
            self.input_text = ""

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float):
        self._update_feedback(dt)
        self.anim_t += dt
        self.reveal_t += dt
        if self.reveal_t >= 0.15 and self.reveal_idx < len(self.ciphered):
            self.reveal_idx += 1
            self.reveal_t = 0.0

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self):
        W, H = self.screen.get_size()
        self.screen.fill(self.settings.COLOR_BG)
        self._draw_title_bar(f"Fichier : {self.file_path}")

        # ── Panneau central ──────────────────────────────────────────────────
        pw, ph = 640, 420
        px, py = (W - pw) // 2, (H - ph) // 2

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((12, 8, 35, 220))
        self.screen.blit(panel, (px, py))
        pygame.draw.rect(self.screen, self.settings.COLOR_PRIMARY, (px, py, pw, ph), 2, border_radius=10)

        # Titre interne
        t = self.font_body.render("Message intercepté (chiffrement César) :", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(t, t.get_rect(center=(W // 2, py + 36)))

        # Message chiffré animé (lettre par lettre)
        visible = self.ciphered[:self.reveal_idx]
        glow_alpha = int(180 + 60 * math.sin(self.anim_t * 3))
        for i, ch in enumerate(visible):
            hue_shift = math.sin(self.anim_t * 2 + i * 0.5)
            r = min(255, max(0, int(100 + 155 * abs(hue_shift))))
            g = min(255, max(0, int(60 + 80 * hue_shift)))
            b = 255
            ch_surf = self.font_title.render(ch, True, (r, g, b))
            x = px + 40 + i * (pw - 80) // max(len(self.ciphered), 1)
            self.screen.blit(ch_surf, (x, py + 90))

        # Info décalage → affiché comme "alphabet wheel"
        y_wheel = py + 160
        label = self.font_body.render("Décalage possible (clic ou flèches) :", True, self.settings.COLOR_TEXT)
        self.screen.blit(label, label.get_rect(center=(W // 2, y_wheel)))

        # Saisie du résultat
        self._draw_input_box(W, H, pw, px, py)

        # Chemin du fichier .enc
        file_info = self.font_small.render(
            f"📄 Fichier chiffré créé : {self.file_path}",
            True, self.settings.COLOR_TEXT_DIM,
        )
        self.screen.blit(file_info, file_info.get_rect(center=(W // 2, py + ph + 20)))

        self._draw_hint_box()
        self._draw_feedback()
        if self._solved:
            self._draw_solved_overlay(W, H)

    def _draw_input_box(self, W, H, pw, px, py):
        label = self.font_body.render("Mot de passe déchiffré ↓", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(label, label.get_rect(center=(W // 2, py + 250)))

        box_w, box_h = 320, 52
        bx = (W - box_w) // 2
        by = py + 280
        pygame.draw.rect(self.screen, (20, 15, 50), (bx, by, box_w, box_h), border_radius=8)
        pygame.draw.rect(self.screen, self.settings.COLOR_ACCENT, (bx, by, box_w, box_h), 2, border_radius=8)

        display = self.input_text + ("|" if int(self.anim_t * 2) % 2 == 0 else "")
        inp_s = self.font_body.render(display, True, self.settings.COLOR_TEXT)
        self.screen.blit(inp_s, inp_s.get_rect(center=(bx + box_w // 2, by + box_h // 2)))

        hint_enter = self.font_small.render("ENTRÉE pour valider", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(hint_enter, hint_enter.get_rect(center=(W // 2, by + box_h + 16)))

    def _draw_solved_overlay(self, W, H):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 20, 50, 140))
        self.screen.blit(overlay, (0, 0))
        msg = self.font_title.render("🔓  DÉCHIFFRÉ — Appuyez sur ESPACE", True, self.settings.COLOR_SUCCESS)
        self.screen.blit(msg, msg.get_rect(center=(W // 2, H // 2)))
