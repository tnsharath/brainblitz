"""
PyMongo helpers for `quiz_attempts`: insert (log), find, update_one, delete_one.

Query operator examples (for filters / $match):
    {'score': {'$gt': 50}}
    {'score': {'$gte': 50, '$lte': 100}}
    {'primary_category': {'$in': ['Python', 'Databases']}}
    {'$and': [{'score': {'$gt': 0}}, {'completed': True}]}
"""

from __future__ import annotations

import logging
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from .mongodb_config import get_mongo_db_name, get_mongo_uri, mongo_enabled

logger = logging.getLogger(__name__)

COLLECTION_QUIZ_ATTEMPTS = "quiz_attempts"

_client: MongoClient | None = None
_init_error_logged = False


def _mongo_client_kwargs(uri: str) -> dict[str, Any]:
    """
    Extra MongoClient options. Atlas and *.mongodb.net require TLS; using Certifi's CA
    bundle avoids TLS handshake failures on some macOS/Python builds where the default
    store is outdated or mismatched.
    """
    kwargs: dict[str, Any] = {"serverSelectionTimeoutMS": 3000}
    lower = uri.lower()
    uses_tls = (
        uri.startswith("mongodb+srv://")
        or ".mongodb.net" in uri
        or "tls=true" in lower
        or "ssl=true" in lower
    )
    if uses_tls:
        try:
            import certifi

            kwargs["tlsCAFile"] = certifi.where()
        except ImportError:
            logger.warning(
                "Mongo URI uses TLS but certifi is not installed; "
                "pip install certifi is recommended for MongoDB Atlas."
            )
    return kwargs


def reset_mongo_connection() -> None:
    """
    Close the cached client (e.g. after connection-string changes). Next call to
    get_client() will build a new MongoClient.
    """
    global _client, _init_error_logged
    if _client is not None:
        try:
            _client.close()
        except Exception:
            logger.debug("Error closing MongoClient", exc_info=True)
    _client = None
    _init_error_logged = False


def get_client() -> MongoClient | None:
    """
    Singleton MongoClient, or None if Mongo is disabled or client construction fails.

    A failed first connection no longer blocks all later requests: we only cache
    a client after a successful ``MongoClient()`` construction (each GET continues
    to retry construction until then — avoids permanent stuck state after transient DNS errors).
    """
    global _client, _init_error_logged
    if not mongo_enabled():
        logger.debug("Mongo get_client: skipped (MONGO_URI not set)")
        return None
    if _client is not None:
        return _client
    logger.info(
        "Mongo get_client: creating MongoClient singleton (timeout=3s) → db=%r collection=%r",
        get_mongo_db_name(),
        COLLECTION_QUIZ_ATTEMPTS,
    )
    try:
        uri = get_mongo_uri()
        _client = MongoClient(uri, **_mongo_client_kwargs(uri))
        _init_error_logged = False
        logger.info(
            "Mongo get_client: MongoClient object constructed (connections are lazy until first op)."
        )
        return _client
    except Exception:
        if not _init_error_logged:
            logger.warning(
                "MongoDB client initialization failed (attempt logs disabled until this succeeds). "
                "Fix MONGO_URI / network / MONGO_DB vs Compass DB name, then restart or call "
                "analytics.mongo_client.reset_mongo_connection().",
                exc_info=True,
            )
            _init_error_logged = True
        return None


def get_db() -> Database | None:
    client = get_client()
    if client is None:
        return None
    name = get_mongo_db_name()
    logger.debug("Mongo get_db: using database %r", name)
    return client[name]


def ping_mongo() -> tuple[bool, str | None]:
    """
    Return (True, None) if the cluster responds to ping, else (False, short error text).
    Use this to distinguish "Mongo unreachable" from "connected but no documents".
    """
    db = get_db()
    if db is None:
        return False, "Mongo client is unavailable (URI disabled or client creation failed)."
    try:
        db.command("ping")
        return True, None
    except Exception as exc:
        return False, str(exc)


def _collection() -> Collection | None:
    db = get_db()
    if db is None:
        return None
    return db[COLLECTION_QUIZ_ATTEMPTS]


def log_attempt(data: dict[str, Any]) -> ObjectId | None:
    """
    INSERT ONE — analogous to INSERT INTO ... VALUES (...)
    Returns inserted document _id, or None if Mongo is disabled or insert failed.
    """
    if not mongo_enabled():
        logger.warning("log_attempt SKIP: MONGO_URI is not set in Django settings.")
        return None
    logger.info(
        "log_attempt START django_attempt_id=%s user=%s quiz=%s score=%s answers_keys=%s",
        data.get("django_attempt_id"),
        data.get("user_id"),
        data.get("quiz_id"),
        data.get("score"),
        sorted((data.get("answers") or {}).keys()),
    )
    coll = _collection()
    if coll is None:
        logger.warning(
            "log_attempt SKIP: collection handle is None — check MongoClient errors above "
            "and that MONGO_URI / MONGO_DB are correct.",
        )
        return None
    db_name = get_mongo_db_name()
    try:
        # First round-trip proves we can reach the cluster (helps debug vs silent URI/db mismatch).
        coll.database.command("ping")
        logger.info(
            "log_attempt NETWORK_OK ping succeeded → inserting into db=%r collection=%r",
            db_name,
            COLLECTION_QUIZ_ATTEMPTS,
        )
        result = coll.insert_one(data)
        oid = result.inserted_id
        logger.info(
            "MongoDB quiz_attempts insert_one ok _id=%s db=%s django_attempt_id=%s",
            oid,
            db_name,
            data.get("django_attempt_id"),
        )
        return oid
    except Exception:
        logger.exception(
            "MongoDB log_attempt insert_one failed (db=%s collection=%s)",
            db_name,
            COLLECTION_QUIZ_ATTEMPTS,
        )
        return None


def get_user_attempts(user_id: int, limit: int = 10) -> list[dict[str, Any]]:
    """
    FIND — filter (WHERE), projection (SELECT columns), sort, limit.
    """
    coll = _collection()
    if coll is None:
        return []
    try:
        return list(
            coll.find(
                {"user_id": user_id},
                {"quiz_title": 1, "score": 1, "_id": 0},
            )
            .sort("timestamp", -1)
            .limit(limit)
        )
    except Exception:
        logger.exception("MongoDB get_user_attempts failed")
        return []


def update_attempt_reviewed(doc_id: str | ObjectId, reviewed: bool = True) -> bool:
    """
    UPDATE ONE with $set — updates specific fields.
    """
    coll = _collection()
    if coll is None:
        return False
    try:
        _id = _parse_oid(doc_id)
        if _id is None:
            return False
        result = coll.update_one({"_id": _id}, {"$set": {"reviewed": reviewed}})
        return result.matched_count > 0
    except Exception:
        logger.exception("MongoDB update_attempt_reviewed failed")
        return False


def delete_attempt_log(doc_id: str | ObjectId) -> bool:
    """DELETE ONE."""
    coll = _collection()
    if coll is None:
        return False
    try:
        _id = _parse_oid(doc_id)
        if _id is None:
            return False
        result = coll.delete_one({"_id": _id})
        return result.deleted_count > 0
    except Exception:
        logger.exception("MongoDB delete_attempt_log failed")
        return False


def _parse_oid(doc_id: str | ObjectId) -> ObjectId | None:
    if isinstance(doc_id, ObjectId):
        return doc_id
    try:
        return ObjectId(doc_id)
    except (InvalidId, TypeError):
        return None
