# Blog Backend

A blog backend API built with Django and Django REST Framework. It uses SQLite for development and JWT authentication for API login.

## Technologies

- Python 3.12+
- Django 6.1
- Django REST Framework 3.18
- Simple JWT for authentication
- `django-cors-headers` for frontend cross-origin requests
- SQLite for local development; PostgreSQL is supported through `DATABASE_URL`

## Project structure

```text
blog-backend/
├── blog/
│   ├── models.py       # Category and Post models
│   ├── serializers.py  # JSON validation and conversion
│   ├── views.py        # API views and permissions
│   └── urls.py         # Blog API routes
├── config/
│   ├── settings.py     # Django configuration
│   └── urls.py         # Project routes
├── manage.py
└── requirements.txt
```

The local `.env`, `db.sqlite3`, and virtual environment are not committed.

## Setup

Run these commands from the project root.

### Linux, macOS, or Ubuntu Codespaces

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create and apply database migrations:

```bash
python manage.py makemigrations blog
python manage.py migrate
```

Check the project:

```bash
python manage.py check
```

## Run the server

```bash
python manage.py runserver 0.0.0.0:8000
```

The development server runs on port `8000`. In GitHub Codespaces, open the forwarded port URL.

Create an admin user when needed:

```bash
python manage.py createsuperuser
```

The Django admin is available at `/admin/`.

## Store post images in Cloudinary

The default development setup stores uploads under `media/posts/`. To store new uploads in Cloudinary, install the updated requirements, create a Cloudinary account, then set these environment variables in the backend's local `.env` file or hosting-provider settings:

```dotenv
USE_CLOUDINARY=True
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

Keep the API secret on the backend only; do not commit `.env` or put the secret in frontend code. Restart Django after setting the values. New images are stored under a per-author folder in Cloudinary, for example `media/users/42/posts/photo.jpg`, where `42` is that author's database user ID. In the Cloudinary dashboard, find them in Media Library under `media` > `users` > the user ID > `posts`. The API's `image` field contains the hosted URL. These folders organize files; they do not restrict access to a public image URL. This does not move existing files from local `media/posts/`; upload those separately if you want them in Cloudinary too. Set `USE_CLOUDINARY=False` (the default) to keep using local storage.

For frontend uploads, send `FormData` rather than JSON and let the browser set the multipart content type, including its boundary:

```javascript
const formData = new FormData();
formData.append("title", title);
formData.append("content", content);
formData.append("category", String(categoryId));
formData.append("is_published", String(isPublished));
formData.append("image", imageFile);

await fetch("http://localhost:8080/api/posts/", {
	method: "POST",
	credentials: "include",
	headers: { "X-CSRFToken": csrfToken },
	body: formData,
});
```

Do not manually set the `Content-Type` header for `FormData`. For updates, send the same form data to the post URL using `PATCH` or `PUT` as appropriate.

## Authentication

### Register

```text
POST /api/register/
```

```json
{
	"username": "srilasya",
	"email": "user@example.com",
	"password": "securepassword"
}
```

The password is hashed before it is saved to Django's built-in user table.
New accounts remain inactive until their email address is verified. Registration
sends a verification link to the configured frontend at
`/verify-email?uid=<uid>&token=<token>`; the frontend should read those query
parameters and POST them to `/api/email-verification/confirm/`. Verification
tokens use Django's `PASSWORD_RESET_TIMEOUT` (three days by default).

To request another link, POST an email address to
`/api/email-verification/resend/`. The response is intentionally the same
whether or not an unverified account exists, and a matching address can receive
at most one resend per minute.

### Login

```text
POST /api/login/
```

```json
{
	"email": "user@example.com",
	"password": "securepassword"
}
```

Login sets the one-hour access and refresh JWTs in `HttpOnly` cookies; it does not return tokens in the JSON body. JavaScript cannot read these cookies. The backend accepts the access cookie automatically on protected requests.

Before login and before POST, PUT, PATCH, or DELETE requests, the frontend must obtain a CSRF cookie:

```text
GET /api/csrf/
```

Send requests with credentials enabled. The CSRF endpoint returns a token for the `X-CSRFToken` header required on login and other unsafe requests. For example, with `fetch`:

```javascript
const csrfResponse = await fetch("http://localhost:8080/api/csrf/", {
	credentials: "include",
});
const { csrfToken } = await csrfResponse.json();

await fetch("http://localhost:8080/api/login/", {
	method: "POST",
	credentials: "include",
	headers: {
		"Content-Type": "application/json",
		"X-CSRFToken": csrfToken,
	},
	body: JSON.stringify({ email, password }),
});
```

Refresh the access cookie by POSTing to `/api/token/refresh/` with credentials and the `X-CSRFToken` header. POST to `/api/logout/` to clear both token cookies. Call `GET /api/csrf/` first if the CSRF cookie has not been set.

During development (`DJANGO_DEBUG=True`), cookies are `HttpOnly` but not `Secure` so they work over local HTTP. Set `DJANGO_DEBUG=False` behind HTTPS in production; token cookies will then also use the `Secure` flag. After one hour, both tokens expire and the frontend should return to login when a protected endpoint responds with `401`. Public post and category reads remain available if an expired cookie is sent.

### Forgot password

Password reset does not require an access token. Submit the user's email address:

```text
POST /api/password-reset/
```

```json
{
	"email": "user@example.com"
}
```

The email contains a link to `/reset-password/<uid>/<token>`. Submit those `uid` and `token` values with the new password to:

```text
POST /api/password-reset/confirm/
```

```json
{
	"uid": "<uid-from-link>",
	"token": "<token-from-link>",
	"new_password": "a-new-secure-password"
}
```

Neither reset request requires a JWT. Local runtime settings are loaded from the ignored `.env` file. There is currently no `.env.example`; configure these values in the hosting provider's environment-variable settings for deployment. To send reset messages to real inboxes using Gmail, enable 2-Step Verification on the sender account and create a Google App Password. Enter the sender account and App Password into `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in `.env` (never commit the app password). Django automatically uses Gmail SMTP when both values are filled; otherwise it prints mail to the server console.

Use the App Password, not the Gmail account's normal password. Restart the Django server after changing `.env`. After setup, submit `POST /api/password-reset/` again; check the Django server output for SMTP errors and check Gmail's Spam folder if it succeeds but does not appear in the inbox.

## Blog API

| Method | URL | Authentication | Description |
| --- | --- | --- | --- |
| `POST` | `/api/email-verification/confirm/` | None | Verify an account using `uid` and `token` |
| `POST` | `/api/email-verification/resend/` | None | Resend a verification link |
| `GET` | `/api/categories/` | None | List categories |
| `GET` | `/api/posts/` | None | List published posts |
| `POST` | `/api/posts/` | Required | Create a post |
| `GET` | `/api/posts/<id>/` | None | View a published post |
| `PUT` | `/api/posts/<id>/` | Author only | Replace your post |
| `PATCH` | `/api/posts/<id>/` | Author only | Update your post |
| `DELETE` | `/api/posts/<id>/` | Author only | Delete your post |

Create a post with:

```json
{
	"title": "Django Basics",
	"content": "My post content",
	"category": 1,
	"is_published": true
}
```

The server sets `author` from the logged-in user. The `slug` is generated automatically from the title.

## Visibility rules

- Anyone can view published posts.
- A logged-in user can also view their own unpublished posts.
- Only the author can edit or delete a post.
- Unauthenticated users cannot create posts.

## Models

`Category` contains `name` and a unique slug generated from the name.

`Post` contains `title`, a unique generated slug, `content`, `author`, `category`, `created_at`, `updated_at`, and `is_published`.

Relationships:

```text
auth_user.id      -> blog_post.author_id
blog_category.id  -> blog_post.category_id
```

## Inspect the SQLite database

```bash
python manage.py dbshell
```

Inside the SQLite prompt:

```sql
.tables
.schema blog_category
.schema blog_post
.quit
```

## Deployment planning

The project already supports environment-based production settings, PostgreSQL through `DATABASE_URL`, and optional Cloudinary media storage. A production deployment is not configured yet: this repository does not contain a GitHub Actions workflow, `requirements.txt` does not include a production WSGI server, and static-file serving has not been configured. Do not use Django's development `runserver` as the production server.

### Free hosting options

These providers list free options as of October 2026. Free plans are intended for personal projects, prototypes, or learning; their limits and terms can change.

| Part | Option | Notes |
| --- | --- | --- |
| Django API | [Render Free Web Service](https://render.com/docs/free) | Supports Python web services. Free services spin down after 15 minutes without traffic and use an ephemeral filesystem. Uploaded local files and SQLite data are lost on restarts, redeploys, and spin-down. |
| PostgreSQL | [Neon Free](https://neon.com/pricing) | A separate PostgreSQL provider; its free plan currently includes 1 GB per project and 100 compute-hours, and compute scales to zero after inactivity. Set its connection URL as `DATABASE_URL`. |
| Static frontend | [Cloudflare Pages](https://developers.cloudflare.com/pages/platform/limits/) | Free static hosting with Git integration; currently limited to 500 builds per month. Suitable for a frontend that builds to static files. |
| Static/frontend app | [Vercel Hobby](https://vercel.com/pricing) or [Netlify Free](https://www.netlify.com/pricing/) | Both offer free frontend hosting with usage limits. Vercel Hobby is for personal, non-commercial use; Netlify Free uses a monthly credit allowance. |

Render also offers free PostgreSQL, but its current free database expires 30 days after creation and is limited to 1 GB. Neon is a better fit for a longer-lived learning deployment, but its free tier is not a substitute for a backed-up production database. Render's free web services cannot send outbound SMTP traffic on the usual SMTP ports (25, 465, and 587), so the current SMTP-based email configuration may not work there on the free tier. Check the provider's current restrictions before choosing a mail service.

### Production configuration

Set these values in the backend host's environment settings. Do not commit `.env` or put backend secrets in GitHub repository files or frontend environment variables.

| Variable | Production purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Required secret used by Django; generate a unique value and keep it private. |
| `DJANGO_DEBUG` | Set to `False`. The current settings default to `True` if this variable is absent. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated backend hostnames, without `https://`. |
| `DATABASE_URL` | PostgreSQL connection URL. If unset, the project falls back to SQLite, which is unsuitable on an ephemeral host. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins including scheme, such as `https://example.com`. |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted frontend origins including scheme. |
| `FRONTEND_URL` | Public frontend base URL used for verification and password-reset links. |
| `USE_CLOUDINARY` and `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` | Set `USE_CLOUDINARY=True` and provide the credentials to persist uploaded images outside the API container. Keep the API secret on the backend only. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | SMTP configuration for verification and password-reset messages. Without credentials, Django uses the console email backend. |

### Browser authentication and domains

The access and refresh JWT cookies currently use `SameSite=Lax`; in production they also use `Secure` when `DJANGO_DEBUG=False`. The browser may not send these cookies when the frontend and API use unrelated provider domains. For example, `project.vercel.app` and `project.onrender.com` are different sites. Prefer frontend and API hostnames under the same custom domain, such as `www.example.com` and `api.example.com`, and configure the exact frontend origin in both CORS and CSRF settings. If unrelated domains are required, cookie and CSRF behavior must be deliberately updated and tested over HTTPS before deployment.

### GitHub Actions status

No GitHub Actions workflow has been added. The intended deployment branch and hosting providers have not been selected, and the frontend source is not part of this backend repository. Once those choices are made, the workflow can be written and tested step by step. Store deploy tokens and other credentials as GitHub Actions secrets; keep application runtime secrets in the hosting provider's environment settings.
