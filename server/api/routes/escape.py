"""Routes FastAPI — Escape Game."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.api.dependencies import get_db
from server.models.player import Player
from server.models.escape_session import EscapeSession
from server.schemas.escape import (
    EscapeStartRequest,
    EscapeStartResponse,
    EscapeRoomClearRequest,
    EscapeRoomClearResponse,
    EscapeCompleteResponse,
    EscapeLeaderboardEntry,
)

router = APIRouter()

TOTAL_ROOMS = 5
BASE_SCORE = 10_000
HINT_PENALTY = 500
TIME_BONUS_FACTOR = 50  # points par seconde économisée (vs 30 min max)
MAX_SECONDS = 30 * 60


def _compute_score(session: EscapeSession) -> int:
    """Calcul du score final."""
    if not session.is_completed:
        return session.rooms_cleared * 500

    duration = session.duration_seconds or MAX_SECONDS
    time_bonus = max(0, (MAX_SECONDS - duration) * TIME_BONUS_FACTOR // 60)
    hint_malus = session.hints_used * HINT_PENALTY
    return max(0, BASE_SCORE + time_bonus - hint_malus)


# ── Démarrer une session ─────────────────────────────────────────────────────

@router.post("/start", response_model=EscapeStartResponse, status_code=status.HTTP_201_CREATED)
def start_escape(payload: EscapeStartRequest, db: Session = Depends(get_db)):
    """Crée ou récupère le joueur, puis démarre une nouvelle session d'escape."""
    player = db.query(Player).filter(Player.name == payload.player_name).first()
    if not player:
        player = Player(name=payload.player_name)
        db.add(player)
        db.commit()
        db.refresh(player)

    session = EscapeSession(player_id=player.id)
    db.add(session)
    db.commit()
    db.refresh(session)

    return EscapeStartResponse(
        session_id=session.id,
        player_id=player.id,
        started_at=session.started_at,
    )


# ── Valider une salle ─────────────────────────────────────────────────────────

@router.put("/{session_id}/room", response_model=EscapeRoomClearResponse)
def clear_room(session_id: int, payload: EscapeRoomClearRequest, db: Session = Depends(get_db)):
    """Marque une salle comme validée."""
    session = db.query(EscapeSession).filter(EscapeSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable.")
    if session.is_completed:
        raise HTTPException(status_code=400, detail="Session déjà terminée.")

    if payload.room_number > session.rooms_cleared:
        session.rooms_cleared = payload.room_number

    if payload.hint_used:
        session.hints_used += 1

    if session.rooms_cleared >= TOTAL_ROOMS:
        session.is_completed = True
        session.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(session)

    return EscapeRoomClearResponse(
        session_id=session.id,
        rooms_cleared=session.rooms_cleared,
        hints_used=session.hints_used,
        is_completed=session.is_completed,
    )


# ── Terminer manuellement une session ────────────────────────────────────────

@router.post("/{session_id}/complete", response_model=EscapeCompleteResponse)
def complete_escape(session_id: int, db: Session = Depends(get_db)):
    """Finalise la session (timeout ou abandon)."""
    session = db.query(EscapeSession).filter(EscapeSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable.")

    if not session.completed_at:
        session.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)

    player = db.query(Player).filter(Player.id == session.player_id).first()

    return EscapeCompleteResponse(
        session_id=session.id,
        player_name=player.name if player else "Inconnu",
        rooms_cleared=session.rooms_cleared,
        hints_used=session.hints_used,
        duration_seconds=session.duration_seconds,
        score=_compute_score(session),
        is_completed=session.is_completed,
    )


# ── Leaderboard ───────────────────────────────────────────────────────────────

@router.get("/leaderboard", response_model=list[EscapeLeaderboardEntry])
def escape_leaderboard(limit: int = 20, db: Session = Depends(get_db)):
    """Classement des escape games (complétés en priorité, puis par score)."""
    sessions = (
        db.query(EscapeSession)
        .filter(EscapeSession.completed_at.isnot(None))
        .order_by(
            EscapeSession.rooms_cleared.desc(),
            EscapeSession.hints_used.asc(),
        )
        .limit(limit)
        .all()
    )

    result = []
    for rank, s in enumerate(sessions, start=1):
        player = db.query(Player).filter(Player.id == s.player_id).first()
        result.append(
            EscapeLeaderboardEntry(
                rank=rank,
                player_name=player.name if player else "Inconnu",
                rooms_cleared=s.rooms_cleared,
                duration_seconds=s.duration_seconds,
                hints_used=s.hints_used,
                score=_compute_score(s),
                completed_at=s.completed_at,
            )
        )
    return result
