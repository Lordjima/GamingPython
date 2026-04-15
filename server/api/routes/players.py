"""Routes FastAPI — Joueurs (CRUD)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.api.dependencies import get_db
from server.models.player import Player
from server.schemas.player import PlayerCreate, PlayerGetOrCreate, PlayerResponse

router = APIRouter()


@router.post("/", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
def create_player(payload: PlayerCreate, db: Session = Depends(get_db)):
    """Crée un nouveau joueur."""
    existing = db.query(Player).filter(Player.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Le joueur '{payload.name}' existe déjà.",
        )
    player = Player(name=payload.name)
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@router.post("/get-or-create", response_model=PlayerResponse)
def get_or_create_player(payload: PlayerGetOrCreate, db: Session = Depends(get_db)):
    """Récupère ou crée un joueur par son nom."""
    player = db.query(Player).filter(Player.name == payload.name).first()
    if not player:
        player = Player(name=payload.name)
        db.add(player)
        db.commit()
        db.refresh(player)
    return player


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(player_id: int, db: Session = Depends(get_db)):
    """Récupère un joueur par son ID."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Joueur introuvable.")
    return player


@router.get("/", response_model=list[PlayerResponse])
def list_players(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Liste tous les joueurs."""
    return db.query(Player).offset(skip).limit(limit).all()
