"""Engine SQLAlchemy et factory de sessions."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from server.core.config import settings

# connect_args : SQLite nécessite check_same_thread=False, MySQL n'en a pas besoin
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.API_DEBUG,
    pool_pre_ping=True,   # Vérifie la connexion avant chaque requête (crucial pour MySQL)
    pool_recycle=3600,    # Recycle les connexions toutes les heures (évite "MySQL server gone")
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
