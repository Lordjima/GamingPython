"""Routes FastAPI — Leaderboard."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from server.api.dependencies import get_db
from server.models.score import Score

router = APIRouter()


@router.get("/{game_name}")
def get_leaderboard(
    game_name: str,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retourne le top N des meilleurs scores pour un jeu donné.
    Un seul score par joueur (le meilleur).
    """
    # Sous-requête : meilleur score par joueur pour ce jeu
    best_per_player = (
        db.query(Score.player_name, func.max(Score.score).label("score"))
        .filter(Score.game_name == game_name)
        .group_by(Score.player_name)
        .subquery()
    )

    # Joins pour récupérer la date du score
    results = (
        db.query(
            Score.player_name,
            Score.score,
            Score.created_at,
        )
        .join(
            best_per_player,
            (Score.player_name == best_per_player.c.player_name)
            & (Score.score == best_per_player.c.score),
        )
        .filter(Score.game_name == game_name)
        .order_by(Score.score.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "rank": i + 1,
            "player_name": row.player_name,
            "score": row.score,
            "created_at": row.created_at.isoformat() if row.created_at else "",
        }
        for i, row in enumerate(results)
    ]
