from django.urls import path

from . import views

app_name = "quiz"

urlpatterns = [
    path("", views.quiz_list, name="list"),
    path("submit/", views.submit_question, name="submit_question"),
    path("<int:quiz_id>/", views.take_quiz, name="take"),
    path("<int:quiz_id>/leaderboard/", views.leaderboard, name="leaderboard"),
    path("results/<int:attempt_id>/", views.results, name="results"),
]

