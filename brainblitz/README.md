# BrainBlitz

Django quiz app: browse quizzes, take them (one question at a time), submit answers once per quiz, view per-quiz leaderboards, submit new questions for admin approval, and manage users via signup/login/profile.

## Documentation

- **[SETUP.md](SETUP.md)** — environment setup, database, first run, and test data for new contributors.

## Requirements

- Python 3.9+ (matches project virtualenv)
- Dependencies: see the repo root [`requirements.txt`](../requirements.txt) (Django 4.2, optional Postgres/Mongo libraries).

## Quick start

From this directory (`brainblitz/`, next to `manage.py`):

```bash
# Use the project venv from the repo root, or create your own.
../venv/bin/python manage.py migrate
../venv/bin/python manage.py createsuperuser
../venv/bin/python manage.py seed_test_questions   # optional: Python + DSA sample quizzes
../venv/bin/python manage.py runserver
```

Then open **http://127.0.0.1:8000/** — quiz list is at **/quizzes/**.

## Running tests

```bash
../venv/bin/python manage.py test quiz.tests -v 2
```

The suite covers:

- Home and quiz list
- Auth (signup, login, profile redirect)
- Take quiz (login required), submit answers, score + redirect to leaderboard
- Single attempt per user per quiz (redirect after completion)
- Leaderboard and results pages
- Submit question form (unapproved question + choices)
- Choice formset validation (min choices, exactly one correct)
- DB uniqueness constraint on attempts
- `seed_test_questions` management command

## Main URLs

| Path | Purpose |
|------|---------|
| `/` | Home |
| `/quizzes/` | Quiz list |
| `/quizzes/<id>/` | Take quiz (logged in) |
| `/quizzes/<id>/leaderboard/` | Leaderboard for that quiz |
| `/quizzes/results/<attempt_id>/` | Attempt review |
| `/quizzes/submit/` | Submit a new question (logged in) |
| `/accounts/signup/`, `/accounts/login/`, `/accounts/logout/` | Auth |
| `/accounts/profile/` | Profile (logged in) |
| `/admin/` | Django admin (approve questions, build quizzes) |

## Configuration

See `brainblitz/settings.py`. Optional Postgres via `POSTGRES_*` env vars; otherwise SQLite is used. `ALLOWED_HOSTS` includes localhost for development.
