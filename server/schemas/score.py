"""Schémas Pydantic — Scores."""
from datetime import datetime
from pydantic import BaseModel, Field


class ScoreCreate(BaseModel):
    game_name: str = Field(..., description="Identifiant du jeu (ex: 'snake')")
    player_name: str = Field(..., min_length=2, max_length=64)
    score: int = Field(..., ge=0, description="Score positif")


class ScoreResponse(BaseModel):
    id: int
    player_id: int
    player_name: str
    game_name: str
    score: int
    created_at: datetime

    model_config = {"from_attributes": True}
