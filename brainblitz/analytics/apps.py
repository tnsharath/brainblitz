import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "analytics"

    def ready(self):
        try:
            from .mongodb_config import get_mongo_db_name, mongo_enabled

            if not mongo_enabled():
                return
            logger.info(
                "Mongo analytics enabled (database=%s); ensuring quiz_attempts indexes.",
                get_mongo_db_name(),
            )
            from .mongo_indexes import ensure_quiz_attempt_indexes

            ensure_quiz_attempt_indexes()
        except Exception:
            logger.warning(
                "Could not ensure MongoDB indexes at startup "
                "(Mongo may be disabled or unreachable).",
                exc_info=True,
            )
