"""Dépendance FastAPI — fournit une session DB par requête."""
from typing import Generator
from sqlalchemy.orm import Session
from server.db.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Dependency injection : session SQLAlchemy par requête HTTP."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
