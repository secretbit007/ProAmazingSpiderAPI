"""File-backed daily leaderboard. One row per player_id per date."""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

TOP_N = 20
MAX_ELAPSED_SECONDS = 24 * 3600
MAX_NICKNAME_LEN = 20

LEADERBOARD_DIR = Path(os.environ.get("SPIDER_LEADERBOARD_DIR", "leaderboards"))


def compute_score(moves: int, elapsed_seconds: int) -> int:
    raw = 10000 - moves * 15 - elapsed_seconds * 2
    return max(0, int(round(raw)))


def _sort_key(entry: Dict[str, Any]) -> tuple:
    return (
        -int(entry.get("score", 0)),
        int(entry.get("moves", 0)),
        int(entry.get("elapsed_seconds", 0)),
        float(entry.get("submitted_at", 0)),
    )


def _is_better(new: Dict[str, Any], old: Dict[str, Any]) -> bool:
    return _sort_key(new)[:3] < _sort_key(old)[:3]


class LeaderboardStore:
    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self._data_dir = Path(data_dir) if data_dir else None
        self._lock = threading.Lock()

    @property
    def data_dir(self) -> Path:
        return self._data_dir if self._data_dir is not None else Path(LEADERBOARD_DIR)

    def path_for(self, date_str: str) -> Path:
        return self.data_dir / f"daily-{date_str}.json"

    def submit(
        self,
        date_str: str,
        player_id: str,
        nickname: str,
        moves: int,
        elapsed_seconds: int,
    ) -> Dict[str, Any]:
        elapsed = max(0, min(MAX_ELAPSED_SECONDS, int(elapsed_seconds)))
        moves = max(0, int(moves))
        score = compute_score(moves, elapsed)
        incoming = {
            "player_id": player_id,
            "nickname": nickname,
            "score": score,
            "moves": moves,
            "elapsed_seconds": elapsed,
            "submitted_at": time.time(),
        }
        with self._lock:
            payload = self._load(date_str)
            entries: List[Dict[str, Any]] = payload.get("entries", [])
            existing = next((e for e in entries if e.get("player_id") == player_id), None)
            if existing is None:
                entries.append(incoming)
            elif _is_better(incoming, existing):
                entries = [e for e in entries if e.get("player_id") != player_id]
                entries.append(incoming)
            else:
                existing["nickname"] = nickname
            entries.sort(key=_sort_key)
            payload = {"date": date_str, "entries": entries}
            self._save(date_str, payload)
        return self.as_response(date_str, player_id)

    def as_response(self, date_str: str, player_id: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            payload = self._load(date_str)
        entries: List[Dict[str, Any]] = list(payload.get("entries", []))
        entries.sort(key=_sort_key)
        you = None
        if player_id:
            for index, entry in enumerate(entries):
                if entry.get("player_id") == player_id:
                    you = {
                        "rank": index + 1,
                        "nickname": entry.get("nickname", ""),
                        "score": int(entry.get("score", 0)),
                        "moves": int(entry.get("moves", 0)),
                        "elapsed_seconds": int(entry.get("elapsed_seconds", 0)),
                    }
                    break
        public = []
        for index, entry in enumerate(entries[:TOP_N]):
            public.append(
                {
                    "rank": index + 1,
                    "nickname": entry.get("nickname", ""),
                    "score": int(entry.get("score", 0)),
                    "moves": int(entry.get("moves", 0)),
                    "elapsed_seconds": int(entry.get("elapsed_seconds", 0)),
                    "is_you": bool(player_id and entry.get("player_id") == player_id),
                }
            )
        return {
            "date": date_str,
            "entries": public,
            "you": you,
            "total": len(entries),
        }

    def _load(self, date_str: str) -> Dict[str, Any]:
        path = self.path_for(date_str)
        if not path.exists():
            return {"date": date_str, "entries": []}
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                return {"date": date_str, "entries": []}
            entries = data.get("entries")
            if not isinstance(entries, list):
                entries = []
            return {"date": date_str, "entries": entries}
        except (OSError, json.JSONDecodeError):
            return {"date": date_str, "entries": []}

    def _save(self, date_str: str, payload: Dict[str, Any]) -> None:
        path = self.path_for(date_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix="lb-", suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise


store = LeaderboardStore()
