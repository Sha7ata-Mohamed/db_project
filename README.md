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
