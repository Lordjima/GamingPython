"""
Jeu Tetris complet — 7 pièces, rotation, niveaux, ligne effacée.
"""
import pygame
import random
from client.core.game_base import BaseGame
from client.core.settings import Settings

COLS, ROWS = 10, 20
CELL = 30

TETROMINOES = {
    "I": ([(0,1),(1,1),(2,1),(3,1)], (60, 220, 255)),
    "O": ([(1,0),(2,0),(1,1),(2,1)], (255, 220, 60)),
    "T": ([(0,1),(1,1),(2,1),(1,0)], (180, 60, 255)),
    "S": ([(1,0),(2,0),(0,1),(1,1)], (60, 220, 120)),
    "Z": ([(0,0),(1,0),(1,1),(2,1)], (255, 80, 80)),
    "J": ([(0,0),(0,1),(1,1),(2,1)], (60, 120, 255)),
    "L": ([(2,0),(0,1),(1,1),(2,1)], (255, 140, 60)),
}


def rotate_cw(cells):
    min_r = min(r for _, r in cells)
    max_c = max(c for c, _ in cells)
    return [(max_c - r, c - min_r) if False else (r, c) for c, r in cells]
    # Vraie rotation :
    return [(r, -c) for c, r in cells]


class Piece:
    def __init__(self, name: str):
        self.name = name
        shapes, self.color = TETROMINOES[name]
        self.cells = list(shapes)
        self.x = COLS // 2 - 2
        self.y = 0

    def get_positions(self):
        return [(self.x + c, self.y + r) for c, r in self.cells]

    def rotate(self):
        pivot_c = sum(c for c, _ in self.cells) / len(self.cells)
        pivot_r = sum(r for _, r in self.cells) / len(self.cells)
        new_cells = []
        for c, r in self.cells:
            nc = int(pivot_r - r + pivot_c + 0.5)
            nr = int(c - pivot_c + pivot_r + 0.5)
            new_cells.append((nc, nr))
        return new_cells


class TetrisGame(BaseGame):
    @property
    def game_name(self) -> str:
        return "tetris"

    def __init__(self, screen: pygame.Surface, settings: Settings, player_name: str = "Player"):
        super().__init__(screen, settings, player_name)
        self._reset()

    def _reset(self):
        self.board = [[None] * COLS for _ in range(ROWS)]
        self.current = self._new_piece()
        self.next_piece = self._new_piece()
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self._fall_acc = 0.0
        self._fall_speed = 1.0   # cells/sec
        self.game_over = False

    def _new_piece(self) -> Piece:
        return Piece(random.choice(list(TETROMINOES.keys())))

    def _is_valid(self, piece: Piece, cells=None, dx=0, dy=0) -> bool:
        if cells is None:
            cells = piece.cells
        for c, r in cells:
            nx, ny = piece.x + c + dx, piece.y + r + dy
            if nx < 0 or nx >= COLS or ny >= ROWS:
                return False
            if ny >= 0 and self.board[ny][nx] is not None:
                return False
        return True

    def _lock(self):
        for x, y in self.current.get_positions():
            if 0 <= y < ROWS and 0 <= x < COLS:
                self.board[y][x] = self.current.color

        # Effacement lignes
        full_rows = [r for r in range(ROWS) if all(self.board[r][c] is not None for c in range(COLS))]
        pts = [0, 100, 300, 500, 800]
        self.score += pts[min(len(full_rows), 4)] * self.level
        self.lines_cleared += len(full_rows)

        for r in full_rows:
            del self.board[r]
            self.board.insert(0, [None] * COLS)

        self.level = 1 + self.lines_cleared // 10
        self._fall_speed = min(1.0 + (self.level - 1) * 0.3, 15.0)

        self.current = self.next_piece
        self.next_piece = self._new_piece()

        if not self._is_valid(self.current):
            self.game_over = True

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.game_over:
                self._reset()
            if self.game_over:
                return
            if event.key == pygame.K_LEFT:
                if self._is_valid(self.current, dx=-1):
                    self.current.x -= 1
            elif event.key == pygame.K_RIGHT:
                if self._is_valid(self.current, dx=1):
                    self.current.x += 1
            elif event.key == pygame.K_DOWN:
                if self._is_valid(self.current, dy=1):
                    self.current.y += 1
            elif event.key == pygame.K_UP:
                rotated = self.current.rotate()
                if self._is_valid(self.current, cells=rotated):
                    self.current.cells = rotated
            elif event.key == pygame.K_SPACE:
                # Hard drop
                while self._is_valid(self.current, dy=1):
                    self.current.y += 1
                self._lock()

    def update(self, dt: float):
        self._fall_acc += dt
        step = 1.0 / self._fall_speed
        if self._fall_acc >= step:
            self._fall_acc -= step
            if self._is_valid(self.current, dy=1):
                self.current.y += 1
            else:
                self._lock()

    def draw(self):
        W, H = self.screen.get_size()
        self.screen.fill(self.settings.COLOR_BG)

        board_w = COLS * CELL
        board_h = ROWS * CELL
        off_x = (W - board_w) // 2 - 80
        off_y = (H - board_h) // 2 + 20

        # Fond plateau
        pygame.draw.rect(self.screen, (15, 15, 38), (off_x - 2, off_y - 2, board_w + 4, board_h + 4), border_radius=4)
        for r in range(ROWS):
            for c in range(COLS):
                rect = pygame.Rect(off_x + c * CELL, off_y + r * CELL, CELL - 1, CELL - 1)
                color = self.board[r][c] if self.board[r][c] else (22, 22, 48)
                pygame.draw.rect(self.screen, color, rect, border_radius=2)

        # Pièce fantôme (ghost)
        ghost_y = self.current.y
        while self._is_valid(self.current, dy=ghost_y - self.current.y + 1):
            ghost_y += 1
        ghost_piece_cells = self.current.cells
        for c, r in ghost_piece_cells:
            gx, gy = off_x + (self.current.x + c) * CELL, off_y + ghost_y + r * CELL
            ghost_surf = pygame.Surface((CELL - 1, CELL - 1), pygame.SRCALPHA)
            ghost_surf.fill((*self.current.color, 50))
            self.screen.blit(ghost_surf, (gx, gy))

        # Pièce courante
        for x, y in self.current.get_positions():
            if y >= 0:
                rect = pygame.Rect(off_x + x * CELL, off_y + y * CELL, CELL - 1, CELL - 1)
                pygame.draw.rect(self.screen, self.current.color, rect, border_radius=2)
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 1, border_radius=2)

        # Panneau latéral
        panel_x = off_x + board_w + 30
        panel_y = off_y

        # Prochaine pièce
        nxt_lbl = self.font_small.render("SUIVANT", True, self.settings.COLOR_TEXT_DIM)
        self.screen.blit(nxt_lbl, (panel_x, panel_y))

        mini_off_x = panel_x + 10
        mini_off_y = panel_y + 30
        for c, r in self.next_piece.cells:
            rect = pygame.Rect(mini_off_x + c * (CELL - 4), mini_off_y + r * (CELL - 4), CELL - 5, CELL - 5)
            pygame.draw.rect(self.screen, self.next_piece.color, rect, border_radius=2)

        # Infos
        infos = [
            ("SCORE",  str(self.score)),
            ("LIGNES", str(self.lines_cleared)),
            ("NIVEAU", str(self.level)),
        ]
        info_y = panel_y + 130
        for label, val in infos:
            l_surf = self.font_small.render(label, True, self.settings.COLOR_TEXT_DIM)
            v_surf = self.font_medium.render(val, True, self.settings.COLOR_TEXT)
            self.screen.blit(l_surf, (panel_x, info_y))
            self.screen.blit(v_surf, (panel_x, info_y + 22))
            info_y += 80

        if self.game_over:
            hint = self.font_small.render("R — Rejouer", True, self.settings.COLOR_SUCCESS)
            self.screen.blit(hint, hint.get_rect(center=(W // 2, H // 2 + 120)))
