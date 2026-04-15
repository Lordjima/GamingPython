"""Schémas Pydantic — Joueurs."""
from datetime import datetime
from pydantic import BaseModel, Field


class PlayerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=64, description="Pseudonyme unique")


class PlayerGetOrCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=64)


class PlayerResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}
