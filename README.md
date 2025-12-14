# DB Project

Simple Django-based application that provides a global search across researchers, research, journals, conferences and keywords.

**Getting Started**
- **Prerequisites:** Python 3.10+ and pip.
- **Install:** create and activate a virtualenv, then install Django (project targets Django 6.x).

```bash
python -m venv .venv
# On Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# then
pip install Django==6.0
```

- **Run migrations & start:**

```bash
python database_project/manage.py migrate
python database_project/manage.py runserver
```

- **Open:** http://127.0.0.1:8000/ and use the search box to find records by name, title, email, journal, conference, or keyword.

**Project structure (key files)**
- **`database/views.py`**: search logic and per-entity SQL queries (populates `researchers`, `research`, `journals`, `conferences`, `keywords`).
- **`database/forms.py`**: `GlobalSearchForm` (search input placeholder and validation).
- **`database/templates/database/search.html`**: search template that renders results and loads static assets (`{% load static %}` and `<link>` for stylesheet).
- **`database/static/database/style.css`**: site styles used by the search template.

**Static files**
- During development Django serves static files automatically when `DEBUG=True`. For production, run `python manage.py collectstatic` and configure your webserver accordingly.

**Database**
- By default `database_project/settings.py` is configured to use SQLite. If you change DB backends (MySQL, etc.) ensure the DB adapter is installed (e.g., `mysql-connector-python` or `mysqlclient`).

**Connecting DB to Django FW**
Follow these steps to connect a database to this Django project:

1. Choose your database engine:
   - SQLite (default, zero-configuration)
   - PostgreSQL (`psycopg2`)
   - MySQL (`mysqlclient` or `mysql-connector-python`)

2. Install the DB adapter (example for PostgreSQL):

```bash
pip install psycopg2-binary
```

3. Update `DATABASES` in `database_project/settings.py` (example PostgreSQL):

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

4. (Optional) Use environment variables to avoid committing secrets. Example with `python-dotenv`:

```python
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASS'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

5. Apply migrations and create a superuser:

```bash
python database_project/manage.py migrate
python database_project/manage.py createsuperuser
```

6. Test the connection by running the dev server:

```bash
python database_project/manage.py runserver
```

7. Troubleshooting:
   - If you see `ModuleNotFoundError: No module named 'psycopg2'` (or `mysql`), install the proper adapter and re-run migrations.
   - Verify DB credentials and that the DB server is reachable.

**Tests**
- There are no automated tests in the repo yet. Run tests with:

```bash
python database_project/manage.py test
```

**Contributing**
- Open issues or PRs for bug fixes and improvements. If you want, I can add tests and CI next.

**Notes**
- The search supports partial matching (SQL LIKE) across multiple entities. If you want case-insensitive or fuzzy/full-text search, I can add that.

If you'd like, I can also: add a `requirements.txt`, CI, or a short CONTRIBUTING.md — which would you prefer next?