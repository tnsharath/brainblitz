from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from quiz.models import (
    AttemptAnswer,
    Category,
    Choice,
    Question,
    Quiz,
    QuizAttempt,
    QuizQuestion,
)

User = get_user_model()


class QuizFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="student", password="testpass123")
        self.cat = Category.objects.create(name="Test Category")
        self.quiz = Quiz.objects.create(title="Unit Test Quiz", description="For tests")
        self.questions = []
        for i in range(2):
            q = Question.objects.create(
                category=self.cat,
                text=f"Question {i}?",
                is_approved=True,
                created_by=self.user,
            )
            self.questions.append(q)
            for j, label in enumerate(["A", "B", "C", "D"]):
                Choice.objects.create(
                    question=q,
                    text=label,
                    is_correct=(j == 0),
                )
            QuizQuestion.objects.create(
                quiz=self.quiz, question=q, order_num=i
            )

    def _post_data_for_full_quiz(self):
        data = {}
        for q in self.questions:
            correct = q.choices.filter(is_correct=True).first()
            data[f"q_{q.id}"] = str(correct.id)
        return data

    def test_home_returns_200(self):
        r = self.client.get(reverse("home"))
        self.assertEqual(r.status_code, 200)

    def test_quiz_list_anonymous_200(self):
        r = self.client.get(reverse("quiz:list"))
        self.assertEqual(r.status_code, 200)

    def test_take_quiz_redirects_when_not_logged_in(self):
        url = reverse("quiz:take", kwargs={"quiz_id": self.quiz.id})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/accounts/login/", r.url)

    def test_take_quiz_get_ok_when_logged_in(self):
        self.client.login(username="student", password="testpass123")
        url = reverse("quiz:take", kwargs={"quiz_id": self.quiz.id})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.quiz.title)

    def test_take_quiz_submit_creates_attempt_and_redirects_leaderboard(self):
        self.client.login(username="student", password="testpass123")
        url = reverse("quiz:take", kwargs={"quiz_id": self.quiz.id})
        r = self.client.post(url, self._post_data_for_full_quiz(), follow=False)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, reverse("quiz:leaderboard", kwargs={"quiz_id": self.quiz.id}))

        attempt = QuizAttempt.objects.get(user=self.user, quiz=self.quiz)
        self.assertIsNotNone(attempt.completed_at)
        self.assertEqual(attempt.score, 2)
        self.assertEqual(AttemptAnswer.objects.filter(attempt=attempt).count(), 2)

    def test_completed_quiz_redirects_to_leaderboard_on_get(self):
        self.client.login(username="student", password="testpass123")
        url = reverse("quiz:take", kwargs={"quiz_id": self.quiz.id})
        self.client.post(url, self._post_data_for_full_quiz())
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, reverse("quiz:leaderboard", kwargs={"quiz_id": self.quiz.id}))

    def test_leaderboard_requires_login(self):
        r = self.client.get(
            reverse("quiz:leaderboard", kwargs={"quiz_id": self.quiz.id})
        )
        self.assertEqual(r.status_code, 302)

    def test_leaderboard_shows_completed_attempt(self):
        self.client.login(username="student", password="testpass123")
        self.client.post(
            reverse("quiz:take", kwargs={"quiz_id": self.quiz.id}),
            self._post_data_for_full_quiz(),
        )
        r = self.client.get(
            reverse("quiz:leaderboard", kwargs={"quiz_id": self.quiz.id})
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "student")
        self.assertContains(r, "Leaderboard")

    def test_results_page_shows_attempt(self):
        self.client.login(username="student", password="testpass123")
        self.client.post(
            reverse("quiz:take", kwargs={"quiz_id": self.quiz.id}),
            self._post_data_for_full_quiz(),
        )
        attempt = QuizAttempt.objects.get(user=self.user, quiz=self.quiz)
        r = self.client.get(reverse("quiz:results", kwargs={"attempt_id": attempt.id}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Unit Test Quiz")

    def test_submit_question_requires_login(self):
        r = self.client.get(reverse("quiz:submit_question"))
        self.assertEqual(r.status_code, 302)

    def test_submit_question_post_creates_unapproved_question(self):
        self.client.login(username="student", password="testpass123")
        post_data = {
            "category": str(self.cat.id),
            "text": "New submitted question?",
            "choices-TOTAL_FORMS": "4",
            "choices-INITIAL_FORMS": "0",
            "choices-MIN_NUM_FORMS": "0",
            "choices-MAX_NUM_FORMS": "1000",
            "choices-0-text": "Opt A",
            "choices-0-is_correct": "on",
            "choices-1-text": "Opt B",
            "choices-2-text": "Opt C",
            "choices-3-text": "Opt D",
        }
        r = self.client.post(reverse("quiz:submit_question"), post_data)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, reverse("quiz:list"))
        q = Question.objects.get(text="New submitted question?")
        self.assertFalse(q.is_approved)
        self.assertEqual(q.choices.count(), 4)


class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup_creates_user_and_redirects(self):
        r = self.client.post(
            reverse("signup"),
            {
                "username": "newuser",
                "password1": "complex_pass_123",
                "password2": "complex_pass_123",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_login_page_200(self):
        r = self.client.get(reverse("login"))
        self.assertEqual(r.status_code, 200)

    def test_profile_requires_login(self):
        r = self.client.get(reverse("profile"))
        self.assertEqual(r.status_code, 302)


class SeedCommandTests(TestCase):
    def test_seed_command_runs(self):
        from django.core.management import call_command

        call_command("seed_test_questions")
        self.assertTrue(Quiz.objects.filter(title="Python Fundamentals (Seed)").exists())
        self.assertTrue(Quiz.objects.filter(title="DSA Fundamentals (Seed)").exists())
