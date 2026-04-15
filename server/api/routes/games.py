"""Routes FastAPI — Jeux disponibles."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.api.dependencies import get_db
from server.models.game import Game

router = APIRouter()

# Données initiales des jeux
DEFAULT_GAMES = [
    {"name": "snake",  "display_name": "Snake",  "icon": "🐍", "description": "Mangez, grandissez, survivez !"},
    {"name": "tetris", "display_name": "Tetris", "icon": "🧱", "description": "Empilez les blocs, effacez les lignes !"},
    {"name": "pong",   "display_name": "Pong",   "icon": "🏓", "description": "1 joueur vs IA — Le classique de l'arcade."},
]


def seed_games(db: Session):
    """Insère les jeux par défaut s'ils n'existent pas."""
    for g in DEFAULT_GAMES:
        if not db.query(Game).filter(Game.name == g["name"]).first():
            db.add(Game(**g))
    db.commit()


@router.get("/")
def list_games(db: Session = Depends(get_db)):
    """Liste tous les jeux activés."""
    seed_games(db)
    games = db.query(Game).filter(Game.enabled == True).all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "display_name": g.display_name,
            "icon": g.icon,
            "description": g.description,
            "enabled": g.enabled,
        }
        for g in games
    ]
