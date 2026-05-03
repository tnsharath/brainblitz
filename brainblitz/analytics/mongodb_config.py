"""
MongoDB is used here for append-only quiz attempt *event logs* only.

Configure with a single connection string:
- ``MONGO_URI`` in `.env` (alternative env name: ``MONGODB_URI``).

``MONGO_DB`` sets the Mongo database PyMongo attaches to via ``client[db_name]``
(Atlas URIs often have no DB in the URL path).

Verbose traces: ``BRAINBLITZ_LOG_LEVEL=DEBUG`` in `.env`.
"""

from __future__ import annotations

from django.conf import settings


def mongo_diagnostics_summary() -> str:
    """
    Human-readable explanation of whether Mongo logging is enabled.
    Does not include the URI (secrets).
    """
    cfg = getattr(settings, "MONGODB", {}) or {}
    has_uri = bool((cfg.get("URI") or "").strip())
    db_name = get_mongo_db_name()
    if has_uri:
        mode = "MONGO_URI is set → analytics ON"
    else:
        mode = "analytics OFF: set MONGO_URI (or MONGODB_URI) in .env"

    return f"{mode} | target_db={db_name!r} (same name in Compass)"


def mongo_enabled() -> bool:
    """True when ``settings.MONGODB['URI']`` is non-empty (``override_settings``-friendly)."""
    cfg = getattr(settings, "MONGODB", {}) or {}
    return bool((cfg.get("URI") or "").strip())


def get_mongo_uri() -> str:
    """Connection string from settings only (no host/user/password construction)."""
    cfg = getattr(settings, "MONGODB", {}) or {}
    return (cfg.get("URI") or "").strip()


def get_mongo_db_name() -> str:
    cfg = getattr(settings, "MONGODB", {}) or {}
    return (cfg.get("DB") or "brainblitz").strip() or "brainblitz"
