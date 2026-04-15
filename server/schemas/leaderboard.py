"""Schémas Pydantic — Leaderboard et Jeux."""
from datetime import datetime
from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    player_name: str
    score: int
    created_at: datetime

    model_config = {"from_attributes": True}


class GameResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: str
    icon: str
    enabled: bool

    model_config = {"from_attributes": True}
