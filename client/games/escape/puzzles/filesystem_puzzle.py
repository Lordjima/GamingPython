"""
Salle 4 — Le Fichier Caché
Navigation dans un système de fichiers virtuel (arborescence).
Un vrai dossier temporaire est créé dans %TEMP%/escape_game/vault/
avec un fichier secret caché dedans.
"""
import math
import os
import random
import tempfile
from pathlib import Path
import pygame
from client.core.settings import Settings
from .base_puzzle import BasePuzzle


SECRET_FILENAME = "secret.key"
SECRET_CONTENT  = "VAULT-OMEGA-3301"   # mot de passe à trouver


# Arborescence virtuelle affichée
VIRTUAL_TREE = {
    "vault": {
        "system": {
            "config.sys": None,
            "boot.ini": None,
            ".hidden": {          # dossier caché !
                "secret.key": None,
            },
        },
        "logs": {
            "access.log": None,
            "error.log": None,
            "debug.log": None,
        },
        "users": {
            "admin": {
                "profile.dat": None,
                "notes.txt": None,
            },
            "ghost": {
                "init.sh": None,
            },
        },
    }
}


class FilesystemPuzzle(BasePuzzle):

    def __init__(self, screen: pygame.Surface, settings: Settings):
        super().__init__(
            screen, settings,
            title="📁  SALLE 4 — LE FICHIER CACHÉ",
            hint="Les dossiers cachés commencent par un point : .hidden",
        )
        self.current_path   = ["vault"]
        self.selected_idx   = 0
        self.input_mode     = False   # saisie du mot de passe
        self.input_text     = ""
        self.anim_t         = 0.0
        self.found_file     = False   # le joueur a atteint secret.key
        self.real_path      = self._create_real_files()

    # ── Crée les vrais fichiers sur l'OS ──────────────────────────────────────

    def _create_real_files(self) -> Path:
        base = Path(tempfile.gettempdir()) / "escape_game" / "vault"
        base.mkdir(parents=True, exist_ok=True)
        # Leurres
        (base / "README.txt").write_text("Rien à voir ici... ou peut-être que si ?\n", encoding="utf-8")
        # Dossier caché avec le secret
        hidden = base / ".hidden"
        hidden.mkdir(exist_ok=True)
        secret_file = hidden / SECRET_FILENAME
        secret_file.write_text(
            f"=== FICHIER CLASSIFIÉ ===\nClé : {SECRET_CONTENT}\n",
            encoding="utf-8",
        )
        return base

    # ── Navigation dans l'arbre virtuel ────────────────────────────────────────

    def _get_current_node(self) -> dict | None:
        node = VIRTUAL_TREE
        for part in self.current_path:
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return None
        return node

    def _get_entries(self):
        node = self._get_current_node()
        if not isinstance(node, dict):
            return []
        entries = []
        if len(self.current_path) > 1:
            entries.append(("..", "dir"))
        for key, val in node.items():
            entries.append((key, "dir" if isinstance(val, dict) else "file"))
        return entries

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if self.input_mode:
            self._handle_input(event)
        else:
            self._handle_nav(event)

    def _handle_nav(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return
        entries = self._get_entries()
        if not entries:
            return

        if event.key == pygame.K_UP:
            self.selected_idx = (self.selected_idx - 1) % len(entries)
        elif event.key == pygame.K_DOWN:
            self.selected_idx = (self.selected_idx + 1) % len(entries)
        elif event.key in (pygame.K_RETURN, pygame.K_RIGHT):
            name, kind = entries[self.selected_idx]
            if name == "..":
                self.current_path.pop()
                self.selected_idx = 0
            elif kind == "dir":
                self.current_path.append(name)
                self.selected_idx = 0
            elif kind == "file" and name == SECRET_FILENAME:
                self.found_file = True
                self.input_mode = True
                self.show_feedback(f"📄  Fichier trouvé : {name}  — Entrez la clé secrète !", success=True)
        elif event.key == pygame.K_LEFT or event.key == pygame.K_BACKSPACE:
            if len(self.current_path) > 1:
                self.current_path.pop()
                self.selected_idx = 0

    def _handle_input(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_RETURN:
            if self.input_text.strip().upper() == SECRET_CONTENT:
                self._solved = True
                self.show_feedback("✅  CLÉ VALIDE — COFFRE DÉVERROUILLÉ !", success=True)
            else:
                self.show_feedback(f"❌  Clé incorrecte : '{self.input_text}'", success=False)
                self.input_text = ""
        elif event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
        elif event.key == pygame.K_ESCAPE:
            self.input_mode = False
        elif len(self.input_text) < 24 and event.unicode.isprintable():
            self.input_text += event.unicode.upper()

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float):
        self._update_feedback(dt)
        self.anim_t += dt

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self):
        W, H = self.screen.get_size()
        self.screen.fill((8, 5, 20))
        self._draw_title_bar(f"OS Temp : {self.real_path}")

        # Panneau principal
        pw, ph = 700, 460
        px, py = (W - pw) // 2, (H - ph) // 2

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((12, 8, 30, 230))
        self.screen.blit(panel, (px, py))
        pygame.draw.rect(self.screen, self.settings.COLOR_SECONDARY, (px, py, pw, ph), 2, border_radius=10)

        # Chemin courant
        path_str = "/" + "/".join(self.current_path)
        path_surf = self.font_mono.render(f"📂  {path_str}", True, self.settings.COLOR_WARNING)
        self.screen.blit(path_surf, (px + 16, py + 16))
        pygame.draw.line(self.screen, self.settings.COLOR_PRIMARY, (px, py + 44), (px + pw, py + 44), 1)

        # Entrées
        entries = self._get_entries()
        line_h = 36
        for i, (name, kind) in enumerate(entries):
            y = py + 52 + i * line_h
            is_sel = (i == self.selected_idx)

            if is_sel and not self.input_mode:
                sel_bg = pygame.Surface((pw - 4, line_h - 2), pygame.SRCALPHA)
                sel_bg.fill((80, 60, 180, 120))
                self.screen.blit(sel_bg, (px + 2, y))

            icon = "📁 " if kind == "dir" else "📄 "
            if name.startswith("."):
                icon = "👁 "   # fichier/dossier caché
            color = self.settings.COLOR_ACCENT if kind == "dir" else self.settings.COLOR_TEXT
            if name == SECRET_FILENAME:
                color = self.settings.COLOR_SUCCESS
            entry_surf = self.font_mono.render(f"  {icon}{name}", True, color)
            self.screen.blit(entry_surf, (px + 8, y + 6))

        # Contrôles
        ctrl = self.font_small.render("↑↓ Naviguer  •  ENTRÉE/→ Ouvrir  •  ← Remonter", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(ctrl, ctrl.get_rect(center=(W // 2, py + ph - 20)))

        # Mode saisie clé
        if self.input_mode:
            self._draw_key_input(W, H)

        # Chemin du vrai fichier
        real_s = self.font_small.render(
            f"📍 Vrai dossier créé : {self.real_path}",
            True, self.settings.COLOR_TEXT_DIM,
        )
        self.screen.blit(real_s, real_s.get_rect(center=(W // 2, py + ph + 22)))

        self._draw_hint_box()
        self._draw_feedback()
        if self._solved:
            self._draw_solved_overlay(W, H)

    def _draw_key_input(self, W: int, H: int):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        bw, bh = 540, 200
        bx, by = (W - bw) // 2, (H - bh) // 2
        box = pygame.Surface((bw, bh), pygame.SRCALPHA)
        box.fill((18, 12, 48, 240))
        self.screen.blit(box, (bx, by))
        pygame.draw.rect(self.screen, self.settings.COLOR_SUCCESS, (bx, by, bw, bh), 2, border_radius=10)

        msg = self.font_body.render("📄  Contenu de secret.key :", True, self.settings.COLOR_SUCCESS)
        self.screen.blit(msg, msg.get_rect(center=(W // 2, by + 30)))

        hint_key = self.font_mono.render("Clé : VAULT-OMEGA-????", True, self.settings.COLOR_WARNING)
        self.screen.blit(hint_key, hint_key.get_rect(center=(W // 2, by + 70)))

        cursor = "|" if int(self.anim_t * 2) % 2 == 0 else " "
        inp_s = self.font_body.render(self.input_text + cursor, True, self.settings.COLOR_TEXT)
        inp_box = pygame.Rect(bx + 40, by + 110, bw - 80, 44)
        pygame.draw.rect(self.screen, (20, 15, 45), inp_box, border_radius=6)
        pygame.draw.rect(self.screen, self.settings.COLOR_ACCENT, inp_box, 2, border_radius=6)
        self.screen.blit(inp_s, inp_s.get_rect(center=inp_box.center))

        esc_s = self.font_small.render("ENTRÉE pour valider  •  ÉCHAP pour fermer", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(esc_s, esc_s.get_rect(center=(W // 2, by + bh - 18)))

    def _draw_solved_overlay(self, W, H):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((20, 0, 50, 130))
        self.screen.blit(overlay, (0, 0))
        msg = self.font_title.render("🔓  COFFRE OUVERT — Appuyez sur ESPACE", True, self.settings.COLOR_SUCCESS)
        self.screen.blit(msg, msg.get_rect(center=(W // 2, H // 2)))
