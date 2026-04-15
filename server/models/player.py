"""Modèle SQLAlchemy — Joueur."""
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from server.db.database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relations
    scores: Mapped[list] = relationship("Score", back_populates="player", cascade="all, delete")

    def __repr__(self) -> str:
        return f"<Player id={self.id} name={self.name!r}>"
