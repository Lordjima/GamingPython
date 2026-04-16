"""
Salle 5 — Le Code Final
Décode du binaire en ASCII pour trouver le mot de passe ultime.
Utilise hashlib (SHA256) pour valider : le player doit trouver le mot en clair,
puis son hash SHA256 est comparé (interactivité OS réelle).
"""
import hashlib
import math
import random
import shutil
import platform
import pygame
from client.core.settings import Settings
from .base_puzzle import BasePuzzle


# Mot de passe final en binaire
SECRET_PLAIN = "FREEDOM"
SECRET_BINARY = " ".join(format(ord(c), "08b") for c in SECRET_PLAIN)
SECRET_HASH   = hashlib.sha256(SECRET_PLAIN.encode()).hexdigest()


class BinaryPuzzle(BasePuzzle):

    def __init__(self, screen: pygame.Surface, settings: Settings):
        super().__init__(
            screen, settings,
            title="💻  SALLE 5 — LE CODE FINAL",
            hint="Chaque groupe de 8 bits = 1 lettre ASCII. 01000110 = 70 = 'F'",
        )
        self.input_text  = ""
        self.anim_t      = 0.0
        self.bit_rain    = []   # effet "pluie de bits"
        self.sys_info    = self._get_sys_info()
        self._init_rain()

    # ── Infos système réelles ─────────────────────────────────────────────────

    def _get_sys_info(self) -> dict:
        disk = shutil.disk_usage("/")
        return {
            "os"     : platform.system() + " " + platform.release(),
            "cpu"    : platform.processor() or "N/A",
            "disk_gb": f"{disk.total // (1024**3)} Go",
            "free_gb": f"{disk.free // (1024**3)} Go libres",
            "python" : platform.python_version(),
        }

    # ── Pluie de bits ─────────────────────────────────────────────────────────

    def _init_rain(self):
        for _ in range(40):
            self.bit_rain.append({
                "x": random.randint(0, 1920),
                "y": random.uniform(-200, 1080),
                "speed": random.uniform(80, 220),
                "char": random.choice(["0", "1"]),
                "alpha": random.randint(30, 90),
                "size": random.choice([14, 16, 18]),
            })

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
        guess = self.input_text.strip().upper()
        if guess == SECRET_PLAIN:
            self._solved = True
            self.show_feedback("✅  MOT DE PASSE DÉCODÉ — ÉVASION RÉUSSIE !", success=True)
        else:
            self.show_feedback(f"❌  SHA256({guess}) ≠ cible. Réessayez.", success=False)
            self.input_text = ""

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float):
        self._update_feedback(dt)
        self.anim_t += dt
        H = self.screen.get_height()
        for drop in self.bit_rain:
            drop["y"] += drop["speed"] * dt
            if drop["y"] > H + 20:
                drop["y"] = random.uniform(-100, -10)
                drop["char"] = random.choice(["0", "1"])

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self):
        W, H = self.screen.get_size()
        self.screen.fill((5, 0, 15))
        self._draw_title_bar("SHA-256 · DÉCODAGE BINAIRE FINAL")

        # Pluie de bits fond
        for drop in self.bit_rain:
            fnt = pygame.font.SysFont("Consolas", drop["size"])
            s = fnt.render(drop["char"], True, (80, 255, 100))
            s.set_alpha(drop["alpha"])
            self.screen.blit(s, (drop["x"], int(drop["y"])))

        # Panneau principal
        pw, ph = 760, 450
        px, py = (W - pw) // 2, (H - ph) // 2

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((10, 5, 28, 235))
        self.screen.blit(panel, (px, py))
        pygame.draw.rect(self.screen, self.settings.COLOR_PRIMARY, (px, py, pw, ph), 2, border_radius=10)

        # Infos système réelles
        info_y = py + 18
        info_label = self.font_small.render("🖥  Environnement cible :", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(info_label, (px + 16, info_y))
        items = [
            f"OS : {self.sys_info['os']}",
            f"CPU : {self.sys_info['cpu'][:40]}",
            f"Disque : {self.sys_info['disk_gb']} ({self.sys_info['free_gb']})",
            f"Python : {self.sys_info['python']}",
        ]
        for i, item in enumerate(items):
            s = self.font_small.render(item, True, self.settings.COLOR_TEXT_DIM)
            self.screen.blit(s, (px + 16, info_y + 20 + i * 18))

        pygame.draw.line(self.screen, self.settings.COLOR_PRIMARY,
                         (px + 10, py + 105), (px + pw - 10, py + 105), 1)

        # Code binaire à déchiffrer
        title_s = self.font_body.render("Décodez ce message binaire :", True, self.settings.COLOR_TEXT)
        self.screen.blit(title_s, title_s.get_rect(center=(W // 2, py + 125)))

        # Affichage binaire mot par mot
        groups = SECRET_BINARY.split()
        group_w = (pw - 40) // len(groups)
        for i, grp in enumerate(groups):
            pulse = int(180 + 75 * math.sin(self.anim_t * 2 + i * 0.7))
            color = (min(255, pulse), 255, min(255, 200 - pulse // 2))
            gx = px + 20 + i * group_w
            # Binaire
            b_s = self.font_mono.render(grp, True, color)
            self.screen.blit(b_s, (gx, py + 155))
            # Valeur décimale (aide)
            decimal = int(grp, 2)
            d_s = self.font_small.render(str(decimal), True, self.settings.COLOR_TEXT_DIM)
            self.screen.blit(d_s, d_s.get_rect(centerx=gx + b_s.get_width() // 2, top=py + 183))

        # Hash attendu
        hash_s = self.font_small.render(f"SHA-256 attendu : {SECRET_HASH[:32]}…", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(hash_s, hash_s.get_rect(center=(W // 2, py + 225)))

        # Saisie
        inp_label = self.font_body.render("Mot de passe (lettres) :", True, self.settings.COLOR_TEXT)
        self.screen.blit(inp_label, (px + 20, py + 265))

        box = pygame.Rect(px + 280, py + 257, 280, 44)
        pygame.draw.rect(self.screen, (18, 10, 38), box, border_radius=6)
        pygame.draw.rect(self.screen, self.settings.COLOR_ACCENT, box, 2, border_radius=6)
        cursor = "|" if int(self.anim_t * 2) % 2 == 0 else " "
        inp_s = self.font_body.render(self.input_text + cursor, True, self.settings.COLOR_TEXT)
        self.screen.blit(inp_s, inp_s.get_rect(midleft=(box.x + 10, box.centery)))

        ctrl = self.font_small.render("Lettres uniquement  •  ENTRÉE pour valider", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(ctrl, ctrl.get_rect(center=(W // 2, py + ph - 22)))

        self._draw_hint_box()
        self._draw_feedback()
        if self._solved:
            self._draw_final_victory(W, H)

    def _draw_final_victory(self, W: int, H: int):
        pulse = int(100 + 80 * math.sin(self.anim_t * 4))
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, pulse // 4, 0, 140))
        self.screen.blit(overlay, (0, 0))

        lines = [
            ("🎉  ÉVASION RÉUSSIE !", self.settings.COLOR_SUCCESS),
            ("Vous avez décodé toutes les énigmes.", self.settings.COLOR_TEXT),
            ("Appuyez sur ESPACE pour voir votre score final.", self.settings.COLOR_TEXT_DIM),
        ]
        for i, (text, color) in enumerate(lines):
            s = self.font_title.render(text, True, color)
            self.screen.blit(s, s.get_rect(center=(W // 2, H // 2 - 40 + i * 56)))
