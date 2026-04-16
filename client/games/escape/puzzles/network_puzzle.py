"""
Salle 3 — Le Réseau Corrompu
Reconstitue une adresse IP fragmentée. socket.gethostname() donne la vraie machine.
Le joueur doit assembler des fragments réseau pour trouver l'IP cible.
"""
import math
import random
import socket
import pygame
from client.core.settings import Settings
from .base_puzzle import BasePuzzle


# L'IP cible est construite à partir de vraies infos + valeurs fixes
TARGET_IP = "192.168.1.42"
FRAGMENTS = [
    ("Fragment A (réseau local standard):", "192.168"),
    ("Fragment B (sous-réseau type LAN) :", "1"),
    ("Fragment C (indice : 6 × 7) :", "42"),
]


class NetworkPuzzle(BasePuzzle):

    def __init__(self, screen: pygame.Surface, settings: Settings):
        super().__init__(
            screen, settings,
            title="🌐  SALLE 3 — LE RÉSEAU CORROMPU",
            hint="Assemblez les 4 octets : A.B.C → 192.168.1.??  (6×7=?)",
        )
        self.input_text = ""
        self.anim_t     = 0.0
        self.packet_anim = []    # paquets animés sur le fond
        self.hostname  = self._get_hostname()
        self.local_ip  = self._get_local_ip()
        self._init_packets()

    # ── Infos réseau réelles ──────────────────────────────────────────────────

    def _get_hostname(self) -> str:
        try:
            return socket.gethostname()
        except Exception:
            return "UNKNOWN"

    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # ── Animation paquets ─────────────────────────────────────────────────────

    def _init_packets(self):
        for _ in range(12):
            self.packet_anim.append({
                "x": random.randint(-200, 1920),
                "y": random.randint(0, 1080),
                "speed": random.uniform(60, 180),
                "text": random.choice([
                    "SYN", "ACK", "RST", "FIN", "PSH",
                    "0xDEAD", "0xBEEF", "???", "[CORRUPT]",
                    "192.168.???.???", "10.0.0.??",
                ]),
                "color": random.choice([
                    (60, 200, 255, 80),
                    (255, 80, 80, 60),
                    (80, 255, 120, 70),
                ]),
            })

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._check_answer()
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif len(self.input_text) < 15:
                ch = event.unicode
                if ch.isdigit() or ch == ".":
                    self.input_text += ch

    def _check_answer(self):
        if self.input_text.strip() == TARGET_IP:
            self._solved = True
            self.show_feedback("✅  ADRESSE IP CORRECTE — CONNEXION RÉTABLIE !", success=True)
        else:
            self.show_feedback(f"❌  {self.input_text} — Paquets invalides !", success=False)
            self.input_text = ""

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float):
        self._update_feedback(dt)
        self.anim_t += dt
        W, H = self.screen.get_size()
        for p in self.packet_anim:
            p["x"] += p["speed"] * dt
            if p["x"] > W + 100:
                p["x"] = -200
                p["y"] = random.randint(0, H)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self):
        W, H = self.screen.get_size()
        self.screen.fill((4, 8, 20))
        self._draw_title_bar(f"Machine : {self.hostname}  |  IP locale : {self.local_ip}")

        # Paquets volants
        for p in self.packet_anim:
            s = self.font_small.render(p["text"], True, p["color"][:3])
            s.set_alpha(p["color"][3])
            self.screen.blit(s, (int(p["x"]), int(p["y"])))

        # Panneau central
        pw, ph = 680, 400
        px, py = (W - pw) // 2, (H - ph) // 2

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((8, 15, 35, 220))
        self.screen.blit(panel, (px, py))
        pygame.draw.rect(self.screen, self.settings.COLOR_ACCENT, (px, py, pw, ph), 2, border_radius=10)

        # Titre
        title = self.font_body.render("🔍  Reconstituez l'adresse IP de la cible :", True, self.settings.COLOR_TEXT)
        self.screen.blit(title, title.get_rect(center=(W // 2, py + 30)))

        # Infos réelles OS
        info1 = self.font_small.render(f"🖥  Votre machine    : {self.hostname}", True, self.settings.COLOR_TEXT_DIM)
        info2 = self.font_small.render(f"🔌  Votre IP locale : {self.local_ip}", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(info1, (px + 20, py + 65))
        self.screen.blit(info2, (px + 20, py + 88))

        # Séparateur
        pygame.draw.line(self.screen, self.settings.COLOR_PRIMARY,
                         (px + 10, py + 110), (px + pw - 10, py + 110), 1)

        # Fragments
        for i, (label, frag) in enumerate(FRAGMENTS):
            y_frag = py + 130 + i * 54
            lb = self.font_small.render(label, True, self.settings.COLOR_TEXT_DIM)
            fr = self.font_body.render(frag, True, self.settings.COLOR_WARNING)
            self.screen.blit(lb, (px + 20, y_frag))
            self.screen.blit(fr, (px + 340, y_frag))

        # Saisie IP
        input_label = self.font_body.render("IP complète :", True, self.settings.COLOR_TEXT)
        self.screen.blit(input_label, (px + 20, py + 300))

        box = pygame.Rect(px + 180, py + 292, 260, 40)
        pygame.draw.rect(self.screen, (15, 20, 48), box, border_radius=6)
        pygame.draw.rect(self.screen, self.settings.COLOR_ACCENT, box, 2, border_radius=6)
        cursor = "|" if int(self.anim_t * 2) % 2 == 0 else " "
        inp_s = self.font_body.render(self.input_text + cursor, True, self.settings.COLOR_TEXT)
        self.screen.blit(inp_s, inp_s.get_rect(midleft=(box.x + 8, box.centery)))

        hint_s = self.font_small.render("Chiffres et points uniquement  •  ENTRÉE pour valider", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(hint_s, hint_s.get_rect(center=(W // 2, py + ph - 20)))

        self._draw_hint_box()
        self._draw_feedback()
        if self._solved:
            self._draw_solved_overlay(W, H)

    def _draw_solved_overlay(self, W, H):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 30, 60, 130))
        self.screen.blit(overlay, (0, 0))
        msg = self.font_title.render("🔓  IP CORRECTE — Appuyez sur ESPACE", True, self.settings.COLOR_SUCCESS)
        self.screen.blit(msg, msg.get_rect(center=(W // 2, H // 2)))
