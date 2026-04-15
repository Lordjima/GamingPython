"""Modèle SQLAlchemy — Score."""
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from server.db.database import Base


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    player_name: Mapped[str] = mapped_column(String(64), nullable=False)  # Dénormalisé pour perf
    game_name: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relation
    player: Mapped["Player"] = relationship("Player", back_populates="scores")  # type: ignore

    def __repr__(self) -> str:
        return f"<Score id={self.id} game={self.game_name!r} score={self.score}>"
