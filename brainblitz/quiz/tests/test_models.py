from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from quiz.models import Category, Choice, Question, Quiz, QuizAttempt, QuizQuestion


User = get_user_model()


class QuizAttemptConstraintTests(TestCase):
    def test_unique_attempt_per_user_per_quiz(self):
        u = User.objects.create_user(username="u1", password="pass")
        cat = Category.objects.create(name="Cat")
        q = Question.objects.create(category=cat, text="Q", is_approved=True)
        quiz = Quiz.objects.create(title="Quiz")
        QuizQuestion.objects.create(quiz=quiz, question=q, order_num=0)

        QuizAttempt.objects.create(user=u, quiz=quiz, score=1)
        with self.assertRaises(IntegrityError):
            QuizAttempt.objects.create(user=u, quiz=quiz, score=0)
