# Ghargistan University PDC System

A Django-based Professional Development Center management application.

## Features
- Login required for the dashboard and PDC management pages.
- Automatic session expiration after 30 minutes without activity.
- Session cookie expires when the browser is closed.
- Responsive dashboard, login page, and PDC forms.
- Add, view, update, and delete PDC records.
- Delete actions use POST and CSRF protection.

## Setup (Windows)
1. Install Python 3.10 or newer.
2. Extract this ZIP.
3. Open a terminal in the `ghargistan_pdc_project` folder.
4. Create and activate a virtual environment:

   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

5. Install requirements:

   ```powershell
   python -m pip install -r requirements.txt
   ```

6. Create database tables:

   ```powershell
   python manage.py makemigrations enroll
   python manage.py migrate
   ```

7. Create an administrator account:

   ```powershell
   python manage.py createsuperuser
   ```

8. Start the server:

   ```powershell
   python manage.py runserver
   ```

9. Open http://127.0.0.1:8000/ — the site will send unauthenticated visitors to Login.

## Logo
Place the university logo at:

`enroll/static/enroll/images/LOGO-GHU.png`

If the logo is missing, the application still runs but the logo image will not display.

## Session behavior
A user is asked to sign in again after 30 minutes without a request to the site. The session cookie is also configured to expire when the browser closes. As with all browser session cookies, browser restore features can vary.

## Before production deployment
- Set a strong private `SECRET_KEY` using an environment variable.
- Set `DEBUG = False`.
- Configure `ALLOWED_HOSTS` for your real domain.
- Use HTTPS and configure secure cookies.
- Back up the database regularly.

## Project notes
The original model name `pdc_detials` and field names are retained to match the supplied project snippets. This project bundle was assembled from code shared in chat and may not include files or assets that were not provided.
