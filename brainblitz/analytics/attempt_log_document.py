"""
Build BSON-friendly documents for the `quiz_attempts` collection.

`timestamp` is a timezone-aware `datetime` (BSON Date); ISO strings also work but
indexes and range queries are nicer with native dates.
"""

from __future__ import annotations

from typing import Any, Iterable

from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from quiz.models import Choice, Quiz


def build_attempt_log_document(
    *,
    django_attempt_id: int,
    user: AbstractUser,
    quiz: Quiz,
    score: int,
    choice_by_qid: dict[int, Choice],
    ordered_question_ids: list[int],
    quiz_question_rows: Iterable[Any],
) -> dict:
    category_names_ordered: list[str] = []
    for qq in quiz_question_rows:
        q = qq.question
        category_names_ordered.append(q.category.name if q.category_id else "")
    primary_category = next((n for n in category_names_ordered if n), "") or ""
    categories = sorted({n for n in category_names_ordered if n})

    answers: dict[str, dict] = {}
    for qid in ordered_question_ids:
        c = choice_by_qid[qid]
        answers[str(qid)] = {
            "question_text": c.question.text,
            "selected_choice_id": c.id,
            "selected_choice_text": c.text,
            "is_correct": c.is_correct,
        }

    return {
        "user_id": user.id,
        "username": user.get_username(),
        "quiz_id": quiz.id,
        "quiz_title": quiz.title,
        "primary_category": primary_category,
        "categories": categories,
        "score": score,
        "completed": True,
        "django_attempt_id": django_attempt_id,
        "answers": answers,
        "timestamp": timezone.now(),
    }
