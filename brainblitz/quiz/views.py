import logging

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.utils import timezone

from analytics.attempt_log_document import build_attempt_log_document
from analytics.mongodb_config import (
    get_mongo_db_name,
    mongo_diagnostics_summary,
    mongo_enabled,
)
from analytics.mongo_client import log_attempt

from .forms import ChoiceFormSet, QuestionSubmitForm
from .models import AttemptAnswer, Choice, Question, Quiz, QuizAttempt, QuizQuestion

logger = logging.getLogger(__name__)


def quiz_list(request):
    quizzes = (
        Quiz.objects.filter(questions__is_approved=True)
        .distinct()
        .order_by("title")
    )
    attempted_quiz_ids = set()
    if request.user.is_authenticated:
        attempted_quiz_ids = set(
            QuizAttempt.objects.filter(user=request.user, completed_at__isnull=False).values_list(
                "quiz_id", flat=True
            )
        )
    return render(
        request,
        "quiz/quiz_list.html",
        {"quizzes": quizzes, "attempted_quiz_ids": attempted_quiz_ids},
    )


@login_required
def take_quiz(request, quiz_id: int):
    quiz = get_object_or_404(Quiz, pk=quiz_id)

    existing_attempt = QuizAttempt.objects.filter(user=request.user, quiz=quiz).first()
    if existing_attempt and existing_attempt.completed_at:
        return redirect("quiz:leaderboard", quiz_id=quiz.id)

    quiz_questions = (
        QuizQuestion.objects.filter(quiz=quiz, question__is_approved=True)
        .select_related("question", "question__category")
        .prefetch_related("question__choices")
        .order_by("order_num")
    )

    if request.method == "POST":
        question_ids = [qq.question_id for qq in quiz_questions]
        selected_choice_ids = []

        for qid in question_ids:
            key = f"q_{qid}"
            val = request.POST.get(key)
            if not val:
                return render(
                    request,
                    "quiz/take_quiz.html",
                    {
                        "quiz": quiz,
                        "quiz_questions": quiz_questions,
                        "error": "Please answer all questions before submitting.",
                    },
                )
            selected_choice_ids.append(int(val))

        # Validate that selected choices belong to the quiz questions.
        valid_choices = (
            Choice.objects.filter(id__in=selected_choice_ids, question_id__in=question_ids)
            .select_related("question")
        )
        if valid_choices.count() != len(selected_choice_ids):
            return render(
                request,
                "quiz/take_quiz.html",
                {
                    "quiz": quiz,
                    "quiz_questions": quiz_questions,
                    "error": "Invalid choice selection. Please try again.",
                },
            )

        choice_by_qid = {c.question_id: c for c in valid_choices}

        with transaction.atomic():
            attempt, _ = QuizAttempt.objects.get_or_create(
                user=request.user, quiz=quiz, defaults={"started_at": timezone.now()}
            )
            if attempt.completed_at:
                return redirect("quiz:leaderboard", quiz_id=quiz.id)

            answers = [
                AttemptAnswer(
                    attempt=attempt,
                    question_id=qid,
                    selected_choice=choice_by_qid[qid],
                )
                for qid in question_ids
            ]
            AttemptAnswer.objects.bulk_create(answers)

            score = sum(1 for qid in question_ids if choice_by_qid[qid].is_correct)
            attempt.score = score
            attempt.completed_at = timezone.now()
            attempt.save(update_fields=["score", "completed_at"])

        logger.info(
            "[take_quiz] SQL transaction committed ok | attempt.pk=%s user_id=%s quiz_id=%s score=%s | "
            "Next: optional Mongo append-only event log (%s)",
            attempt.pk,
            request.user.pk,
            quiz.pk,
            attempt.score,
            mongo_diagnostics_summary(),
        )

        if mongo_enabled():
            logger.info(
                "[take_quiz] mongo_enabled=True → building BSON document "
                "(Django stays source of truth; Mongo is analytics only)."
            )
            payload = build_attempt_log_document(
                django_attempt_id=attempt.pk,
                user=request.user,
                quiz=quiz,
                score=attempt.score if attempt.score is not None else score,
                choice_by_qid=choice_by_qid,
                ordered_question_ids=question_ids,
                quiz_question_rows=quiz_questions,
            )
            mongo_id = log_attempt(payload)
            if mongo_id is not None:
                QuizAttempt.objects.filter(pk=attempt.pk).update(
                    mongo_log_id=str(mongo_id)
                )
                logger.info(
                    "[take_quiz] mongo_log_id stored on QuizAttempt | attempt.pk=%s mongo_log_id=%s",
                    attempt.pk,
                    mongo_id,
                )
            else:
                logger.warning(
                    "[take_quiz] Mongo insert returned None → attempt.pk=%s still saved in SQL. "
                    "Scroll up for analytics.mongo_client lines; Compass DB must be %r.",
                    attempt.pk,
                    get_mongo_db_name(),
                )
        else:
            logger.warning(
                "[take_quiz] Mongo analytics disabled — skipping log_attempt | attempt.pk=%s | %s",
                attempt.pk,
                mongo_diagnostics_summary(),
            )

        return redirect("quiz:leaderboard", quiz_id=quiz.id)

    return render(
        request,
        "quiz/take_quiz.html",
        {"quiz": quiz, "quiz_questions": quiz_questions},
    )


def results(request, attempt_id: int):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related("quiz", "user"),
        pk=attempt_id,
    )
    answers = (
        AttemptAnswer.objects.filter(attempt=attempt)
        .select_related("question", "selected_choice")
        .order_by("question_id")
    )
    return render(
        request,
        "quiz/results.html",
        {"attempt": attempt, "answers": answers},
    )


@login_required
def leaderboard(request, quiz_id: int):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    attempts = (
        QuizAttempt.objects.filter(quiz=quiz, completed_at__isnull=False)
        .select_related("user")
        .order_by("-score", "completed_at")
    )
    my_attempt = attempts.filter(user=request.user).first()

    return render(
        request,
        "quiz/leaderboard.html",
        {"quiz": quiz, "attempts": attempts, "my_attempt": my_attempt},
    )


@login_required
def submit_question(request):
    question = Question(created_by=request.user, is_approved=False)

    if request.method == "POST":
        form = QuestionSubmitForm(request.POST, instance=question)
        formset = ChoiceFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            question = form.save()
            formset.instance = question
            formset.save()
            return redirect("quiz:list")
    else:
        form = QuestionSubmitForm(instance=question)
        formset = ChoiceFormSet(instance=question)

    return render(
        request,
        "quiz/submit_question.html",
        {"form": form, "formset": formset},
    )
