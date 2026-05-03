# BrainBlitz — setup for new developers

This guide assumes the repository root contains `venv/` and `requirements.txt`, with the Django project in `brainblitz/` (this folder), where `manage.py` lives.

## 1. Python and virtual environment

Use Python **3.9+**.

From the **repository root** (parent of this folder):

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

If you prefer a venv inside `brainblitz/` only, create it there and adjust paths below.

## 2. Environment variables (optional)

You can copy or create a `.env` file at the repo root or under `brainblitz/`. The app loads both via `python-dotenv` in `brainblitz/settings.py`.

**SQLite (default)**  
No database env vars needed. The database file is `brainblitz/db.sqlite3`.

**PostgreSQL**  
Set `POSTGRES_HOST` (and typically `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`). When `POSTGRES_HOST` is set, Django uses Postgres instead of SQLite.

**MongoDB (optional analytics logs)**  
Set `MONGO_URI` (Atlas or local connection string). Optionally set `MONGO_DB` (default `brainblitz`) — this is the Mongo database name in Compass/PyMongo `client[dbname]`. The quiz core remains on Django’s SQL database.

## 3. Migrate and superuser

From **`brainblitz/`** (same directory as `manage.py`):

```bash
# If using repo-root venv:
../venv/bin/python manage.py migrate
../venv/bin/python manage.py createsuperuser
```

Use the superuser to log into `/admin/` and approve submitted questions, attach questions to quizzes, etc.

## 4. Seed sample quizzes (recommended for testing)

Creates **Python Fundamentals (Seed)** and **DSA Fundamentals (Seed)** with 10 approved questions each:

```bash
../venv/bin/python manage.py seed_test_questions
```

Safe to run multiple times: it replaces those two seed quizzes and their questions.

## 5. Run the development server

```bash
../venv/bin/python manage.py runserver
```

Open:

- **http://127.0.0.1:8000/** — home  
- **http://127.0.0.1:8000/quizzes/** — quiz list  

Create a normal user via **Sign up** (`/accounts/signup/`) or use the admin to add users.

## 6. Allowed hosts

For local development, `ALLOWED_HOSTS` includes `localhost`, `127.0.0.1`, etc. If you access the site via another hostname or IP, add it in `brainblitz/settings.py` under `ALLOWED_HOSTS`.

## 7. Run automated tests

From `brainblitz/`:

```bash
../venv/bin/python manage.py test quiz.tests -v 2
```

All tests should pass before you open a pull request.

## 8. Troubleshooting

| Issue | What to try |
|-------|----------------|
| `DisallowedHost` | Add your host to `ALLOWED_HOSTS` or use `127.0.0.1`. |
| Quiz list empty | Ensure quizzes have at least one **approved** question linked via `QuizQuestion`. Run `seed_test_questions` or configure in admin. |
| Cannot take quiz | You must be **logged in**. Anonymous users are redirected to login. |
| Second attempt blocked | By design: one completed attempt per user per quiz. |
