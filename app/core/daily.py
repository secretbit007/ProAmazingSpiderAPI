"""Shared daily-challenge deal (same seed for every player on a given date)."""
from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from typing import Optional

DAILY_DIFFICULTY = 4
DAILY_SUIT_COUNT = 2
DAILY_SALT = "proAmazingSpider:daily"


def utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def parse_date(value: Optional[str]) -> str:
    if not value:
        return utc_today()
    date.fromisoformat(value)
    return value


def daily_seed(date_str: str) -> int:
    digest = hashlib.sha256(f"{DAILY_SALT}:{date_str}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16)
