from django.contrib.auth import get_user_model
from django.test import TestCase

from analytics.attempt_log_document import build_attempt_log_document
from quiz.models import (
    Category,
    Choice,
    Question,
    Quiz,
    QuizQuestion,
)


User = get_user_model()


class AttemptLogDocumentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="docuser", password="x")
        self.cat = Category.objects.create(name="Python")
        self.quiz = Quiz.objects.create(title="Sample quiz", description="")
        self.question = Question.objects.create(
            category=self.cat,
            text="What is 2+2?",
            is_approved=True,
            created_by=self.user,
        )
        self.choice = Choice.objects.create(
            question=self.question, text="4", is_correct=True
        )
        Choice.objects.create(
            question=self.question, text="3", is_correct=False
        )
        QuizQuestion.objects.create(
            quiz=self.quiz, question=self.question, order_num=0
        )

    def test_document_has_expected_structure(self):
        choice_by_qid = {self.question.id: self.choice}
        rows = QuizQuestion.objects.filter(quiz=self.quiz).select_related(
            "question__category"
        ).order_by("order_num")

        payload = build_attempt_log_document(
            django_attempt_id=111,
            user=self.user,
            quiz=self.quiz,
            score=1,
            choice_by_qid=choice_by_qid,
            ordered_question_ids=[self.question.id],
            quiz_question_rows=rows,
        )
        self.assertEqual(payload["django_attempt_id"], 111)
        self.assertEqual(payload["user_id"], self.user.id)
        self.assertEqual(payload["username"], "docuser")
        self.assertEqual(payload["quiz_id"], self.quiz.id)
        self.assertEqual(payload["quiz_title"], "Sample quiz")
        self.assertEqual(payload["primary_category"], "Python")
        self.assertEqual(payload["categories"], ["Python"])
        self.assertEqual(payload["score"], 1)
        self.assertTrue(payload["completed"])
        self.assertEqual(
            payload["answers"][str(self.question.id)]["question_text"], "What is 2+2?"
        )
