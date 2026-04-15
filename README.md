# Article API

A simple REST API for managing articles and users, built with FastAPI and SQLite.

## Features

- User registration and JWT authentication
- Full CRUD for articles (create, read, update, delete)
- Subscribe to new article notifications
- Bulk import articles from an external source (JSONPlaceholder)
- HTTPS via self-signed TLS certificate
- Dockerized for easy deployment

## Running with Docker

```bash
docker compose up --build
```

The API will be available at `https://localhost:8443`.

Interactive docs: `https://localhost:8443/docs`

> Note: The self-signed certificate will trigger a browser warning - you can safely bypass it locally, or use `curl -k`.

## Running locally (without Docker)

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` (no TLS in dev mode).

## API Overview

### Users

| Method | Endpoint          | Auth | Description                 |
| ------ | ----------------- | ---- | --------------------------- |
| POST   | `/users/register` | NO   | Register a new user         |
| POST   | `/users/login`    | NO   | Login and receive JWT token |
| GET    | `/users/me`       | YES  | Get current user info       |
| DELETE | `/users/me`       | YES  | Delete account              |

### Articles

| Method | Endpoint                | Auth | Description                      |
| ------ | ----------------------- | ---- | -------------------------------- |
| POST   | `/articles/`            | YES  | Create article                   |
| GET    | `/articles/`            | NO   | List articles (paginated)        |
| GET    | `/articles/{id}`        | NO   | Get single article               |
| PUT    | `/articles/{id}`        | YES  | Update article (owner only)      |
| DELETE | `/articles/{id}`        | YES  | Delete article (owner only)      |
| POST   | `/articles/import/bulk` | YES  | Bulk import from external source |

### Subscriptions & Notifications

| Method | Endpoint                                 | Auth | Description                     |
| ------ | ---------------------------------------- | ---- | ------------------------------- |
| POST   | `/subscriptions/`                        | YES  | Subscribe to new article alerts |
| DELETE | `/subscriptions/`                        | YES  | Unsubscribe                     |
| GET    | `/subscriptions/notifications`           | YES  | List your notifications         |
| POST   | `/subscriptions/notifications/{id}/read` | YES  | Mark notification as read       |

## Authentication

1. Register: `POST /users/register`
2. Login: `POST /users/login` -> receive `access_token`
3. Use `Authorization: Bearer <token>` header on protected endpoints

## Design Decisions

- **SQLite** - simple, zero-config, appropriate for this scope
- **JWT** - stateless auth, standard approach
- **Self-signed TLS** - satisfies HTTPS requirement without external cert authority
- **JSONPlaceholder** - used as the external article source for bulk import
- **Notifications** - stored in DB; subscribers receive a record per new article
