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

### Login

```text
POST /api/login/
```

```json
{
	"username": "srilasya",
	"password": "securepassword"
}
```

The response contains `access` and `refresh` tokens. Send the access token with protected requests:

```text
Authorization: Bearer <access-token>
```

Refresh an expired access token at:

```text
POST /api/login/refresh/
```

```json
{
	"refresh": "<refresh-token>"
}
```

## Blog API

| Method | URL | Authentication | Description |
| --- | --- | --- | --- |
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
