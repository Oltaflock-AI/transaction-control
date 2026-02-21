# API Reference

Base URL: `/api/v1`

## Authentication

All endpoints except `/health` and `/auth/*` require a Bearer token in the
`Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens are JWTs signed with HS256. They expire after 60 minutes (configurable
via `ACCESS_TOKEN_EXPIRE_MINUTES`).

### POST `/auth/login`

Exchange email + password for a JWT.

**Request:**
```json
{ "email": "admin@dev.local", "password": "password123" }
```

**Response (200):**
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

**Errors:** `401` — invalid credentials.

### POST `/auth/dev-token`

Issue a JWT without a password. Only available when `APP_ENV` is `local` or
`test`. Useful for local development and testing.

**Request:**
```json
{ "email": "admin@dev.local" }
```

**Response (200):** same shape as `/auth/login`.

**Errors:** `404` — user not found or endpoint disabled in non-local envs.

---

## Public Endpoints

### GET `/health`

Returns `{ "ok": true }`. No authentication required.

---

## Protected Endpoints

All of the following require `Authorization: Bearer <token>`.

### POST `/transactions`

Create a new transaction. Automatically enqueues a Celery task
(`generate_timeline`) that creates 5 starter tasks with staggered due dates.

**Request:**
```json
{
  "org_id": "uuid",
  "title": "123 Main St",
  "description": "Residential sale",
  "property_address": "123 Main St, Springfield",
  "close_date": "2026-04-15"
}
```

Only `org_id` and `title` are required. The caller must be a member of the org.

**Response (201):**
```json
{
  "id": "uuid",
  "org_id": "uuid",
  "title": "123 Main St",
  "description": "Residential sale",
  "status": "draft",
  "property_address": "123 Main St, Springfield",
  "close_date": "2026-04-15",
  "created_at": "2026-02-21T..."
}
```

**Errors:** `401` — not authenticated. `403` — not a member of the org.

### GET `/transactions/{id}`

Fetch a single transaction with its tasks.

**Response (200):**
```json
{
  "id": "uuid",
  "org_id": "uuid",
  "title": "...",
  "status": "draft",
  "description": null,
  "property_address": null,
  "close_date": null,
  "created_at": "2026-02-21T...",
  "tasks": [
    { "id": "uuid", "title": "Review contract", "status": "todo", "due_at": "..." },
    { "id": "uuid", "title": "Order inspection", "status": "todo", "due_at": "..." }
  ]
}
```

**Errors:** `404` — not found. `403` — not a member of the org.

### GET `/transactions/{id}/tasks`

List tasks belonging to a transaction. Tasks are created asynchronously by the
`generate_timeline` Celery job after transaction creation.

**Response (200):**
```json
[
  {
    "id": "uuid",
    "transaction_id": "uuid",
    "title": "Review contract",
    "status": "todo",
    "due_at": "2026-02-24T...",
    "assignee_id": null,
    "created_at": "2026-02-21T..."
  }
]
```

**Errors:** `404` — transaction not found. `403` — not a member of the org.

### GET `/transactions`

List all transactions belonging to the caller's organisations.

**Response (200):** array of transaction objects (without nested tasks).

### `/tasks`, `/timeline`

Protected by `require_user`. Endpoints TBD (stubs registered).

### `/audit`

Protected by `require_role("admin")`. Requires the caller to have at least one
membership with `role = "admin"`. Returns `403` otherwise. Endpoints TBD.

---

## Background Jobs (Celery)

| Task | Trigger | Effect |
|---|---|---|
| `tc.generate_timeline` | `POST /transactions` | Creates 5 default tasks + timeline items for the new transaction |

Default tasks created: Review contract (3d), Order inspection (7d),
Appraisal review (14d), Title search (21d), Final walkthrough (28d).

---

## RBAC Model

| Dependency | Effect |
|---|---|
| `require_user` | Validates JWT, loads user from DB, rejects inactive users. Returns `401` on failure. |
| `require_role(role)` | Wraps `require_user`, additionally checks the user has a `Membership` with the required role. Returns `403` on failure. |

Convenience type aliases in `tc.core.security`:
- `CurrentUser` — `Annotated[..., Depends(require_user)]`
- `AdminUser` — `Annotated[..., Depends(require_role("admin"))]`

---

## Dev Credentials (seed)

After running `scripts/seed_db.py`:

| Field | Value |
|---|---|
| Email | `admin@dev.local` |
| Password | `password123` |
| Org | Dev Organisation (`dev-org`) |
| Role | `admin` |
