"""
Aggregation pipelines: filter → group → sort → reshape.

Rough SQL equivalent for average_score_per_category():

    SELECT primary_category AS category,
           ROUND(AVG(score), 1) AS avg_score,
           COUNT(*) AS attempts,
           MAX(score) AS top_score
    FROM quiz_attempts
    WHERE score > 0
    GROUP BY primary_category
    ORDER BY avg_score DESC;
"""

from __future__ import annotations

import logging
from typing import Any

from .mongo_client import COLLECTION_QUIZ_ATTEMPTS, get_db

logger = logging.getLogger(__name__)


def average_score_per_category_pipeline() -> list[dict[str, Any]]:
    return [
        {"$match": {"score": {"$gt": 0}}},
        {
            "$group": {
                "_id": "$primary_category",
                "avg_score": {"$avg": "$score"},
                "attempts": {"$sum": 1},
                "top_score": {"$max": "$score"},
            }
        },
        {"$sort": {"avg_score": -1}},
        {
            "$project": {
                "category": "$_id",
                "avg_score": {"$round": ["$avg_score", 1]},
                "attempts": 1,
                "top_score": 1,
                "_id": 0,
            }
        },
    ]


def run_pipeline(
    pipeline: list[dict[str, Any]],
    collection_name: str = COLLECTION_QUIZ_ATTEMPTS,
) -> list[dict[str, Any]]:
    """Execute aggregate(pipeline); returns a list for easy Django templates/tests."""
    db = get_db()
    if db is None:
        return []
    try:
        return list(db[collection_name].aggregate(pipeline))
    except Exception:
        logger.exception("MongoDB aggregation failed collection=%s", collection_name)
        return []


def average_score_per_category() -> list[dict[str, Any]]:
    """Convenience: run the teaching pipeline."""
    return run_pipeline(average_score_per_category_pipeline())
