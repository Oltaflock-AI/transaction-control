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

### GET `/transactions`

Returns transactions belonging to organisations the caller is a member of.

**Response (200):**
```json
[
  {
    "id": "uuid",
    "title": "...",
    "status": "draft",
    "org_id": "uuid",
    "created_at": "2026-02-21T..."
  }
]
```

### `/tasks`, `/timeline`

Protected by `require_user`. Endpoints TBD (stubs registered).

### `/audit`

Protected by `require_role("admin")`. Requires the caller to have at least one
membership with `role = "admin"`. Returns `403` otherwise. Endpoints TBD.

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
