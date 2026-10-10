# Blog Backend

A blog backend API built with Django and Django REST Framework. It uses SQLite for development and JWT authentication for API login.

## Technologies

- Python 3.12+
- Django 6.1
- Django REST Framework 3.18
- Simple JWT for authentication
- `django-cors-headers` for frontend cross-origin requests
- SQLite

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
├── db.sqlite3
├── requirements.txt
└── venv/
```

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

Neither reset request requires a JWT. Runtime settings are loaded from the ignored `.env` file; `.env.example` lists the available options. To send reset messages to real inboxes using Gmail, enable 2-Step Verification on the sender account and create a Google App Password. Enter the sender account and App Password into `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in `.env` (never commit the app password). Django automatically uses Gmail SMTP when both values are filled; otherwise it prints mail to the server console.

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
