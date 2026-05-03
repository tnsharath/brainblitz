from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return f"Profile: {self.user}"

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name

class ApprovedQuestionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_approved=True)


class UnapprovedQuestionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_approved=False)


class Question(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="questions"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="submitted_questions",
    )
    text = models.TextField()
    is_approved = models.BooleanField(default=False)

    objects = models.Manager()
    approved = ApprovedQuestionManager()
    unapproved = UnapprovedQuestionManager()

    def __str__(self) -> str:
        return self.text[:80]

class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.text[:80]

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    questions = models.ManyToManyField(
        Question, through="QuizQuestion", related_name="quizzes"
    )

    def __str__(self) -> str:
        return self.title

class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order_num = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order_num"]


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_attempts")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    score = models.IntegerField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "quiz"], name="unique_attempt_per_user_per_quiz"
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} · {self.quiz} · {self.score if self.score is not None else '-'}"


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"], name="unique_answer_per_question_per_attempt"
            )
        ]