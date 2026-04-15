"""Tests de l'API FastAPI — Players, Scores, Leaderboard."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.main import app
from server.api.dependencies import get_db
from server.db.database import Base

# Base de données en mémoire pour les tests
TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


client = TestClient(app)


# ── Health ───────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Players ──────────────────────────────────────────────────────────────────

def test_create_player():
    r = client.post("/api/players/", json={"name": "TestPlayer"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "TestPlayer"
    assert "id" in data


def test_create_duplicate_player():
    client.post("/api/players/", json={"name": "Dupe"})
    r = client.post("/api/players/", json={"name": "Dupe"})
    assert r.status_code == 409


def test_get_or_create_player():
    r1 = client.post("/api/players/get-or-create", json={"name": "AutoPlayer"})
    r2 = client.post("/api/players/get-or-create", json={"name": "AutoPlayer"})
    assert r1.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]


def test_get_player():
    r = client.post("/api/players/", json={"name": "FindMe"})
    pid = r.json()["id"]
    r2 = client.get(f"/api/players/{pid}")
    assert r2.status_code == 200
    assert r2.json()["name"] == "FindMe"


def test_get_unknown_player():
    r = client.get("/api/players/9999")
    assert r.status_code == 404


# ── Scores ───────────────────────────────────────────────────────────────────

def test_submit_score():
    r = client.post("/api/scores/", json={
        "game_name": "snake", "player_name": "Scorer", "score": 500
    })
    assert r.status_code == 201
    assert r.json()["score"] == 500


def test_submit_score_invalid_game():
    r = client.post("/api/scores/", json={
        "game_name": "unknown_game", "player_name": "X", "score": 100
    })
    assert r.status_code == 400


# ── Leaderboard ──────────────────────────────────────────────────────────────

def test_leaderboard_empty():
    r = client.get("/api/leaderboard/snake")
    assert r.status_code == 200
    assert r.json() == []


def test_leaderboard_with_scores():
    client.post("/api/scores/", json={"game_name": "tetris", "player_name": "A", "score": 1000})
    client.post("/api/scores/", json={"game_name": "tetris", "player_name": "B", "score": 2000})
    client.post("/api/scores/", json={"game_name": "tetris", "player_name": "A", "score": 500})  # Doublon A

    r = client.get("/api/leaderboard/tetris")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2           # Un seul score par joueur
    assert data[0]["score"] == 2000  # B en premier
    assert data[0]["rank"] == 1


# ── Games ────────────────────────────────────────────────────────────────────

def test_list_games():
    r = client.get("/api/games/")
    assert r.status_code == 200
    names = [g["name"] for g in r.json()]
    assert "snake" in names
    assert "tetris" in names
    assert "pong" in names
