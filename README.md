# FlyRank Backend Track — W2 A4: FastAPI + Supabase Authentication

A FastAPI backend that implements user signup, login, logout, and JWT-protected
routes using Supabase Auth. Built as Assignment 4 (Week 2) of the FlyRank
Backend Track.

## Tech Stack

- **Python**
- **FastAPI** — web framework
- **Supabase Auth** — user management and JWT issuance/verification
- **JWT (JSON Web Tokens)** — bearer token authentication
- **Pydantic** — request body validation
- **python-dotenv** — environment variable loading
- **Uvicorn** — ASGI server
- **Swagger UI** — interactive API documentation

## Features

- User signup via Supabase Auth
- User login that returns an access token and refresh token
- Public routes accessible without authentication
- Protected routes that require a valid Bearer JWT
- Reusable FastAPI authentication dependency built on `HTTPBearer`
- JWT verification delegated to Supabase (`supabase.auth.get_user`)
- Logout endpoint (authenticated)
- Health check endpoint
- Swagger UI with an **Authorize** button for testing Bearer auth directly in the browser

## Project Structure

```
.
├── main.py            # FastAPI app: routes, auth dependency, Supabase client
├── .env                # Local environment variables (NOT committed)
├── .env.example        # Placeholder template for required environment variables
├── requirements.txt    # Python dependencies
└── README.md
```

## Authentication Flow

1. **Signup** — the user registers with an email and password via `POST /auth/signup`. FastAPI forwards these credentials to Supabase Auth (`supabase.auth.sign_up`).
2. **Login** — the user logs in via `POST /auth/login`. Supabase validates the credentials and returns a session containing an `access_token` and `refresh_token`.
3. **Requesting protected resources** — the client sends the `access_token` as a `Bearer` token in the `Authorization` header.
4. **Token extraction** — FastAPI's `HTTPBearer` security scheme extracts the credentials from the `Authorization` header via the `get_current_user` dependency.
5. **Token verification** — the token is passed to `supabase.auth.get_user(token)`, which verifies it against Supabase and returns the associated user.
6. **Access decision**:
   - No token → `401 Unauthorized` ("Access token required")
   - Invalid, tampered, or expired token → `401 Unauthorized` ("Invalid or expired token")
   - Valid token → the route executes and the authenticated user is available as `current_user`

## Setup Instructions (Ubuntu / Linux)

### 1. Clone the project and enter the directory

```bash
git clone <your-repo-url>
cd <project-folder>
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not yet present, install the core packages directly:

```bash
pip install fastapi uvicorn python-dotenv supabase pydantic
```

### 4. Configure Supabase

1. Create a project at [supabase.com](https://supabase.com).
2. In your Supabase project dashboard, go to **Project Settings → API**.
3. Copy the **Project URL** and the **publishable/anon key** (the client-safe key — never use the `service_role` key in this app).

### 5. Configure environment variables

Copy the example file and fill in your own values:

```bash
cp .env.example .env
```

`.env.example`:

```
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_publishable_or_anon_key_here
```

> `.env` is listed in `.gitignore` and must never be committed. Only
> `.env.example`, containing placeholders, should be tracked in version
> control.

### 6. Run the FastAPI server

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### 7. Open Swagger UI

```
http://127.0.0.1:8000/docs
```

Use the **Authorize** button in Swagger UI and paste in an `access_token`
obtained from `POST /auth/login` to test the protected routes.

## API Reference

| Method | Endpoint               | Auth Required | Description                                              |
|--------|-------------------------|:-------------:|------------------------------------------------------------|
| GET    | `/`                     | No            | Basic root message confirming the API is running          |
| GET    | `/health`               | No            | Health check                                               |
| POST   | `/auth/signup`          | No            | Registers a new user with Supabase Auth                    |
| POST   | `/auth/login`           | No            | Authenticates a user and returns access/refresh tokens     |
| POST   | `/auth/logout`          | Yes           | Signs the current user out                                 |
| GET    | `/public/info`          | No            | Publicly accessible sample route                            |
| GET    | `/protected/profile`    | Yes           | Returns the authenticated user's profile (id, email, created_at) |
| GET    | `/protected/dashboard`  | Yes           | Returns a welcome message with the authenticated user's id and email |

## Authentication

Protected routes are secured using FastAPI's `HTTPBearer` security scheme
combined with a reusable dependency, `get_current_user`:

- The `Authorization` header must be in the form `Bearer <access_token>`.
- The dependency extracts the token and verifies it against Supabase using
  `supabase.auth.get_user(token)`.
- If verification succeeds, the resolved user object is injected into the
  route via `Security(get_current_user)`.
- If verification fails (missing, invalid, or expired token), the dependency
  raises `401 Unauthorized` before the route body ever executes.

This means any new route can be protected simply by adding
`current_user = Security(get_current_user)` as a parameter.

### Example: Login Request / Response

**Request** — `POST /auth/login`

```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response — 200 OK**

```json
{
  "message": "Login successful",
  "access_token": "<jwt_access_token>",
  "refresh_token": "<jwt_refresh_token>"
}
```

### Example: Protected Route Response

**Request** — `GET /protected/profile`
Header: `Authorization: Bearer <access_token>`

**Response — 200 OK**

```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "created_at": "2026-01-01T00:00:00Z"
}
```

**Response — 401 Unauthorized** (missing/invalid/expired token)

```json
{
  "detail": "Invalid or expired token"
}
```

## HTTP Status Codes

| Code | Meaning               | Used When                                                        |
|------|------------------------|--------------------------------------------------------------------|
| 200  | OK                     | Successful login, or successful access to a public/protected route |
| 201  | Created                | Successful signup                                                  |
| 204  | No Content             | Successful logout                                                  |
| 400  | Bad Request            | Missing email/password, or signup failure                          |
| 401  | Unauthorized           | Missing token, invalid/expired token, invalid login credentials, or logout failure |

## Security

- `.env` contains sensitive credentials (Supabase URL and key) and **must
  never be committed to version control**. It is listed in `.gitignore`.
- `.env.example` is committed instead, containing only placeholder values, so
  other developers know which variables are required without exposing real
  secrets.
- Only the **publishable/anon key** is used in this application — the
  Supabase `service_role` key should never be used or exposed here.
- All protected routes reject requests without a valid Bearer token,
  returning `401 Unauthorized`.
- Token verification is delegated entirely to Supabase (`get_user`), so no
  custom JWT decoding/secret handling is done in application code.

## Testing

The following authentication behaviors were manually tested via Swagger UI:

- Signing up a new user with valid email/password (`201 Created`)
- Logging in with valid credentials and receiving `access_token` /
  `refresh_token` (`200 OK`)
- Logging in with invalid credentials and receiving `401 Unauthorized`
- Accessing `/public/info` without any token (succeeds)
- Accessing `/protected/profile` and `/protected/dashboard` **without** a
  token (`401 Unauthorized` — "Access token required")
- Accessing `/protected/profile` and `/protected/dashboard` with a
  **tampered/invalid** token (`401 Unauthorized` — "Invalid or expired token")
- Accessing `/protected/profile` and `/protected/dashboard` **with** a valid
  token obtained from login (`200 OK`, returns user data)
- Logging out with a valid token (`204 No Content`)

## Learning Outcomes

- Implementing user authentication using a managed auth provider (Supabase)
  instead of building password hashing and JWT signing from scratch
- Designing a reusable FastAPI dependency (`Security`/`HTTPBearer`) to
  protect multiple routes without duplicating auth logic
- Understanding the full JWT lifecycle: issuance at login, transmission via
  the `Authorization` header, and verification on each protected request
- Differentiating between public and protected routes at the route-definition
  level
- Managing secrets safely using `.env` / `.gitignore` and `.env.example`
- Using Swagger UI's Authorize flow to test Bearer-token-protected APIs
  interactively