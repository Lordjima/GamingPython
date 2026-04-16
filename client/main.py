"""
h4ckR — Point d'entrée principal
Lance le menu principal Pygame
"""
import pygame
import sys
import os

# Ajoute la racine du projet au path Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.core.settings import Settings
from client.core.sound_manager import SoundManager
from client.menu.main_menu import MainMenu


def main():
    pygame.init()
    pygame.mixer.init()

    settings = Settings()

    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h))

    pygame.display.set_caption("🔐 h4ckR")

    # Icône de fenêtre
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "images", "logo.png")
    if os.path.exists(icon_path):
        icon = pygame.image.load(icon_path)
        pygame.display.set_icon(icon)

    sound_manager = SoundManager(settings)
    menu = MainMenu(screen, settings, sound_manager)
    menu.run()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
