"""Gestion audio — musique de fond et effets sonores."""
import pygame
from client.core.settings import Settings


class SoundManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._current_music: str = ""
        self._sfx_cache: dict = {}

        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(settings.MUSIC_VOLUME)

    def play_music(self, filename: str, loop: bool = True):
        if not self.settings.MUSIC_ENABLED:
            return
        path = self.settings.SOUNDS_DIR / filename
        if not path.exists():
            return
        if self._current_music == filename:
            return
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(self.settings.MUSIC_VOLUME)
            pygame.mixer.music.play(-1 if loop else 0)
            self._current_music = filename
        except pygame.error as e:
            print(f"[Audio] Cannot play {filename}: {e}")

    def stop_music(self):
        pygame.mixer.music.stop()
        self._current_music = ""

    def play_sfx(self, filename: str):
        if not self.settings.SFX_ENABLED:
            return
        if filename not in self._sfx_cache:
            path = self.settings.SOUNDS_DIR / "sfx" / filename
            if not path.exists():
                return
            try:
                self._sfx_cache[filename] = pygame.mixer.Sound(str(path))
            except pygame.error:
                return
        sound = self._sfx_cache[filename]
        sound.set_volume(self.settings.SFX_VOLUME)
        sound.play()

    def set_music_volume(self, volume: float):
        self.settings.MUSIC_VOLUME = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.settings.MUSIC_VOLUME)

    def set_sfx_volume(self, volume: float):
        self.settings.SFX_VOLUME = max(0.0, min(1.0, volume))
        for sound in self._sfx_cache.values():
            sound.set_volume(self.settings.SFX_VOLUME)
