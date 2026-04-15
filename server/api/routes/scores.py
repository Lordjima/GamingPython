"""Routes FastAPI — Scores."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.api.dependencies import get_db
from server.models.player import Player
from server.models.score import Score
from server.schemas.score import ScoreCreate, ScoreResponse

router = APIRouter()

VALID_GAMES = {"snake", "tetris", "pong"}


@router.post("/", response_model=ScoreResponse, status_code=status.HTTP_201_CREATED)
def submit_score(payload: ScoreCreate, db: Session = Depends(get_db)):
    """Enregistre un score. Crée le joueur s'il n'existe pas."""
    if payload.game_name not in VALID_GAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Jeu inconnu : '{payload.game_name}'. Valides : {VALID_GAMES}",
        )

    # Get-or-create le joueur
    player = db.query(Player).filter(Player.name == payload.player_name).first()
    if not player:
        player = Player(name=payload.player_name)
        db.add(player)
        db.commit()
        db.refresh(player)

    score_obj = Score(
        player_id=player.id,
        player_name=payload.player_name,
        game_name=payload.game_name,
        score=payload.score,
    )
    db.add(score_obj)
    db.commit()
    db.refresh(score_obj)
    return score_obj


@router.get("/player/{player_name}", response_model=list[ScoreResponse])
def get_player_scores(player_name: str, game_name: str = None, db: Session = Depends(get_db)):
    """Historique des scores d'un joueur, optionnellement filtré par jeu."""
    q = db.query(Score).filter(Score.player_name == player_name)
    if game_name:
        q = q.filter(Score.game_name == game_name)
    return q.order_by(Score.score.desc()).limit(20).all()
