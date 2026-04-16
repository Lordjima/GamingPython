"""Initialisation de la base de données — crée les tables si elles n'existent pas."""
from server.db.database import engine, Base

# Import de tous les modèles pour que SQLAlchemy les détecte
from server.models import player, score, game  # noqa: F401
from server.models import escape_session  # noqa: F401


def init_db():
    """Crée toutes les tables en BDD."""
    Base.metadata.create_all(bind=engine)
