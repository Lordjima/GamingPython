"""
Client HTTP vers l'API FastAPI.
Fournit des méthodes synchrones (utilisables depuis Pygame).
"""
import threading
from typing import Optional, List, Dict

import httpx

from client.core.settings import Settings


class APIClient:
    """Client HTTP simple — synchrone, thread-safe."""

    def __init__(self, settings: Settings):
        self.base_url = settings.API_BASE_URL
        self.timeout = settings.API_TIMEOUT

    # ── Helpers internes ─────────────────────────────────────────────────

    def _get(self, endpoint: str) -> Optional[Dict]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.get(f"{self.base_url}{endpoint}")
                r.raise_for_status()
                return r.json()
        except Exception as e:
            print(f"[API] GET {endpoint} → {e}")
            return None

    def _post(self, endpoint: str, data: dict) -> Optional[Dict]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.post(f"{self.base_url}{endpoint}", json=data)
                r.raise_for_status()
                return r.json()
        except Exception as e:
            print(f"[API] POST {endpoint} → {e}")
            return None

    # ── Joueurs ──────────────────────────────────────────────────────────

    def get_or_create_player(self, name: str) -> Optional[Dict]:
        return self._post("/players/get-or-create", {"name": name})

    def get_player(self, player_id: int) -> Optional[Dict]:
        return self._get(f"/players/{player_id}")

    # ── Scores ───────────────────────────────────────────────────────────

    def submit_score_sync(self, game_name: str, player_name: str, score: int):
        """Soumet un score en arrière-plan (non bloquant — thread daemon)."""
        def _submit():
            self._post("/scores/", {
                "game_name": game_name,
                "player_name": player_name,
                "score": score,
            })
        threading.Thread(target=_submit, daemon=True).start()

    # ── Leaderboard ──────────────────────────────────────────────────────

    def get_leaderboard(self, game_name: str, limit: int = 10) -> List[Dict]:
        result = self._get(f"/leaderboard/{game_name}?limit={limit}")
        return result if isinstance(result, list) else []

    def get_all_games(self) -> List[Dict]:
        result = self._get("/games/")
        return result if isinstance(result, list) else []

    # ── Santé de l'API ───────────────────────────────────────────────────

    def check_health(self) -> bool:
        try:
            root = self.base_url.rsplit("/api", 1)[0]
            with httpx.Client(timeout=2) as client:
                r = client.get(f"{root}/health")
                return r.status_code == 200
        except Exception:
            return False
