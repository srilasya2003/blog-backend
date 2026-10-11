# Brightline Blog API

A Django REST API for a blog platform. It provides account lifecycle and session endpoints alongside category and post management, with author-based permissions and optional cloud image storage.

## Technology Stack

| Area | Technology |
| --- | --- |
| Language | Python 3.12+ |
| Web framework | Django 6.1 |
| API | Django REST Framework 3.18 |
| Authentication | Simple JWT in HttpOnly cookies, with CSRF protection |
| Database | SQLite for local development; PostgreSQL via `DATABASE_URL` |
| Image handling | Pillow, with optional Cloudinary storage |
| Production server and static files | Gunicorn and WhiteNoise |
| CI/CD | GitHub Actions; Render deployment hook for the `development` branch |

## Features

- Register accounts with email verification and rate-limited verification resends.
- Sign in with email and password; access and refresh JWTs are stored in HttpOnly cookies.
- Refresh and revoke cookie-based sessions, with CSRF checks on unsafe requests.
- Request and confirm password resets using time-limited Django tokens.
- Browse categories and published posts; authenticated authors can manage their own posts and drafts.
- Upload validated JPG, JPEG, and PNG images. Images can be stored locally or in Cloudinary under author-specific paths.
- Run automated tests in GitHub Actions. Pull requests to `development` and `main` run tests; pushes to `development` run tests and can trigger the Render development service.

## API Overview

All endpoints are under `/api/`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/register/` | Create an account and send a verification email |
| `POST` | `/email-verification/confirm/` | Activate an account with its verification token |
| `POST` | `/email-verification/resend/` | Request another verification email |
| `POST` | `/login/` | Authenticate and set JWT cookies |
| `POST` | `/token/refresh/` | Refresh the access cookie |
| `POST` | `/logout/` | Clear authentication cookies |
| `GET` | `/csrf/` | Set the CSRF cookie and return a CSRF token |
| `GET` | `/profile/` | Return the authenticated user's profile |
| `POST` | `/password-reset/` | Request a password-reset email |
| `POST` | `/password-reset/confirm/` | Set a new password using the reset token |
| `GET` | `/categories/` | List categories |
| `GET` | `/posts/` | List published posts and the authenticated author's posts |
| `POST` | `/posts/create/` | Create a post for the authenticated user |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/posts/<id>/` | Retrieve or manage a post; edits and deletion are author-only |

Cookie-authenticated browser clients should call `/csrf/` before login and other `POST`, `PUT`, `PATCH`, or `DELETE` requests. Include credentials on requests and send the returned token in the `X-CSRFToken` header. File uploads use `multipart/form-data` (`FormData` in a browser); let the client set the multipart content type and boundary.

## Run Locally

Requirements: Python 3.12 or later and pip.

Create and activate a virtual environment from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create an ignored `.env` file in the project root. Generate a Django key with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`, then configure at least:

```dotenv
DJANGO_SECRET_KEY=replace-with-a-generated-development-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
FRONTEND_URL=http://localhost:5173
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173
```

For local development, omit `DATABASE_URL` to use SQLite. To use PostgreSQL, set `DATABASE_URL` to a development database connection string. Never commit `.env` or use a production database for tests.

Apply migrations and start the development server:

```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

The API is available at `http://localhost:8000/api/`; the Django admin is at `http://localhost:8000/admin/`.

## Run Tests

```bash
python manage.py test
```

The test suite covers API access rules, registration and email verification, password reset, cookie-based authentication, token expiry, and image upload paths. Run tests against SQLite or a disposable test database, never a production database.

## Deployment

The application is configured for a native Python web service; a Dockerfile is not required. For the current Render setup:

- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
- Database: PostgreSQL configured through `DATABASE_URL`.
- Uploaded images: set `USE_CLOUDINARY=True` and configure the Cloudinary credentials when persistent image storage is needed.
- Runtime configuration: set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, and `FRONTEND_URL` in the hosting provider's environment settings.

The GitHub Actions workflow runs tests for pull requests to `development` and `main`. A push to `development` runs tests and then calls the Render deploy hook. The hook URL belongs in the GitHub Actions secret `RENDER_DEV_DEPLOY_HOOK`; application runtime secrets belong in the hosting provider, not in the repository.

## Project Structure

```text
blog-backend/
|-- .github/workflows/backend.yml  # CI and development deployment
|-- blog/                          # Models, API views, serializers, and tests
|-- config/                        # Django project settings and URL routing
|-- manage.py
|-- requirements.txt
`-- README.md
```
