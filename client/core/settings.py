"""Configuration globale du client Pygame."""
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ASSETS_DIR = BASE_DIR / "assets"


class Settings:
    # ── Fenêtre ─────────────────────────────────────────────────────────
    SCREEN_WIDTH: int = 1280
    SCREEN_HEIGHT: int = 720
    FPS: int = 60
    TITLE: str = "Gaming Python"
    FULLSCREEN: bool = False

    # ── API ─────────────────────────────────────────────────────────────
    API_BASE_URL: str = "http://localhost:8000/api"
    API_TIMEOUT: int = 5

    # ── Audio ────────────────────────────────────────────────────────────
    MUSIC_VOLUME: float = 0.5
    SFX_VOLUME: float = 0.7
    MUSIC_ENABLED: bool = True
    SFX_ENABLED: bool = True

    # ── Palette de couleurs ──────────────────────────────────────────────
    COLOR_BG: tuple = (8, 8, 22)
    COLOR_PRIMARY: tuple = (100, 60, 255)
    COLOR_SECONDARY: tuple = (255, 60, 130)
    COLOR_ACCENT: tuple = (60, 220, 255)
    COLOR_TEXT: tuple = (235, 235, 255)
    COLOR_TEXT_DIM: tuple = (130, 130, 175)
    COLOR_SUCCESS: tuple = (60, 220, 120)
    COLOR_ERROR: tuple = (255, 80, 80)
    COLOR_WARNING: tuple = (255, 180, 60)

    # ── Chemins des assets ───────────────────────────────────────────────
    ASSETS_DIR: Path = ASSETS_DIR
    FONTS_DIR: Path = ASSETS_DIR / "fonts"
    IMAGES_DIR: Path = ASSETS_DIR / "images"
    SOUNDS_DIR: Path = ASSETS_DIR / "sounds"
    THEMES_DIR: Path = ASSETS_DIR / "themes"

    def __init__(self):
        self._load_user_settings()

    def _load_user_settings(self):
        """Charge les préférences utilisateur sauvegardées."""
        save_path = BASE_DIR.parent / "user_settings.json"
        if save_path.exists():
            try:
                with open(save_path, "r") as f:
                    data = json.load(f)
                self.SCREEN_WIDTH = data.get("screen_width", self.SCREEN_WIDTH)
                self.SCREEN_HEIGHT = data.get("screen_height", self.SCREEN_HEIGHT)
                self.MUSIC_VOLUME = data.get("music_volume", self.MUSIC_VOLUME)
                self.SFX_VOLUME = data.get("sfx_volume", self.SFX_VOLUME)
                self.MUSIC_ENABLED = data.get("music_enabled", self.MUSIC_ENABLED)
                self.SFX_ENABLED = data.get("sfx_enabled", self.SFX_ENABLED)
                self.FULLSCREEN = data.get("fullscreen", self.FULLSCREEN)
            except Exception:
                pass

    def save(self):
        """Sauvegarde les paramètres utilisateur."""
        config = {
            "screen_width": self.SCREEN_WIDTH,
            "screen_height": self.SCREEN_HEIGHT,
            "music_volume": self.MUSIC_VOLUME,
            "sfx_volume": self.SFX_VOLUME,
            "music_enabled": self.MUSIC_ENABLED,
            "sfx_enabled": self.SFX_ENABLED,
            "fullscreen": self.FULLSCREEN,
        }
        save_path = BASE_DIR.parent / "user_settings.json"
        with open(save_path, "w") as f:
            json.dump(config, f, indent=2)

    def load_theme(self, theme_name: str = "default") -> dict:
        theme_path = self.THEMES_DIR / f"{theme_name}.json"
        if theme_path.exists():
            with open(theme_path, "r") as f:
                return json.load(f)
        return {}
