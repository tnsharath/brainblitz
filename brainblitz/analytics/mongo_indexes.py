"""
Indexes speed up filtered/sorted queries. Without them, MongoDB scans the collection.

    db.quiz_attempts.create_index(...)
    explain() shows whether an index was used.

Create indexes once at startup (see analytics.apps.ready) — idempotent via create_index.
"""

from __future__ import annotations

import logging
from typing import Any

from pymongo import DESCENDING

from .mongo_client import COLLECTION_QUIZ_ATTEMPTS, get_db

logger = logging.getLogger(__name__)


def ensure_quiz_attempt_indexes() -> None:
    db = get_db()
    if db is None:
        return
    coll = db[COLLECTION_QUIZ_ATTEMPTS]
    coll.create_index([("user_id", 1)])
    coll.create_index([("primary_category", 1)])
    coll.create_index([("timestamp", DESCENDING)])
    coll.create_index([("username", 1), ("score", DESCENDING)])


def explain_find_user_attempts(user_id: int) -> dict[str, Any] | None:
    """For teaching: run explain() on a typical profile query."""
    db = get_db()
    if db is None:
        return None
    try:
        return db[COLLECTION_QUIZ_ATTEMPTS].find({"user_id": user_id}).explain()
    except Exception:
        logger.exception("MongoDB explain_find_user_attempts failed")
        return None
