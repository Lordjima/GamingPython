"""Schémas Pydantic — Escape Game."""
from datetime import datetime
from pydantic import BaseModel


class EscapeStartRequest(BaseModel):
    player_name: str


class EscapeStartResponse(BaseModel):
    session_id: int
    player_id: int
    started_at: datetime

    model_config = {"from_attributes": True}


class EscapeRoomClearRequest(BaseModel):
    room_number: int   # 1..5
    hint_used: bool = False


class EscapeRoomClearResponse(BaseModel):
    session_id: int
    rooms_cleared: int
    hints_used: int
    is_completed: bool

    model_config = {"from_attributes": True}


class EscapeCompleteRequest(BaseModel):
    pass  # suffit d'appeler l'endpoint


class EscapeCompleteResponse(BaseModel):
    session_id: int
    player_name: str
    rooms_cleared: int
    hints_used: int
    duration_seconds: int | None
    score: int
    is_completed: bool

    model_config = {"from_attributes": True}


class EscapeLeaderboardEntry(BaseModel):
    rank: int
    player_name: str
    rooms_cleared: int
    duration_seconds: int | None
    hints_used: int
    score: int
    completed_at: datetime | None

    model_config = {"from_attributes": True}
