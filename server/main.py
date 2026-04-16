"""
FastAPI — Point d'entrée du serveur Gaming Python
Lance : uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.core.config import settings
from server.db.database import engine
from server.db.init_db import init_db
from server.api.routes import players, scores, leaderboard, games, escape


# ── Application ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="h4ckR API",
    description="API REST pour la plateforme h4ckR — escape game, scores, joueurs, leaderboards.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ─────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Initialise la base de données au démarrage."""
    init_db()
    print("✅  Base de données initialisée")
    print(f"🔐  h4ckR API v2.0 — {settings.API_HOST}:{settings.API_PORT}")

# ── Routers ─────────────────────────────────────────────────────────────────────

app.include_router(players.router,     prefix="/api/players",     tags=["Joueurs"])
app.include_router(scores.router,      prefix="/api/scores",      tags=["Scores"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["Leaderboard"])
app.include_router(games.router,       prefix="/api/games",       tags=["Jeux"])
app.include_router(escape.router,      prefix="/api/escape",      tags=["Escape Game"])

# ── Routes utilitaires ──────────────────────────────────────────────────────────

@app.get("/health", tags=["Santé"])
async def health_check():
    return {"status": "ok", "service": "h4ckR API", "version": "2.0.0"}

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "🔐 h4ckR API",
        "docs": "/docs",
        "health": "/health",
    }
