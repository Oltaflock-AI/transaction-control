# Contributing to Transaction Control

## Local setup

```bash
git clone <repo-url> && cd transaction-control
cp .env.example .env
cd infra && docker compose up --build -d
docker compose exec -w /app/apps/api api uv run alembic upgrade head
docker compose exec -w /app/apps/api api uv run python /app/scripts/seed_db.py
```

Verify: `curl http://localhost:8000/api/v1/health` should return `{"ok": true}`.

## Branch workflow

- **Never push directly to `main` or `dev`.** Branch protection is enforced.
- Create a feature branch from `dev`, open a PR, and wait for CI + code review.
- CODEOWNERS will auto-assign reviewers.

## Code rules

### 1. Routers never touch the database directly

Routers call **services** only. All SQL queries, ORM operations, and business logic
live in `services/`. Routers are responsible for HTTP concerns: parsing input,
calling a service, formatting the response.

```
# GOOD
@router.post("")
def create(body: CreateSchema, user: CurrentUser, db: DB):
    result = my_service.create(db, ...)
    return result

# BAD — don't do this
@router.post("")
def create(body: CreateSchema, user: CurrentUser, db: DB):
    obj = MyModel(...)
    db.add(obj)
    db.commit()
    return obj
```

### 2. Every new endpoint must have tests

At minimum:
- **Happy path** — the endpoint works with valid input and auth.
- **Auth guard** — calling without a token returns `401`.
- **Membership check** — if org-scoped, calling with a user from a different org returns `403`.

### 3. Org scoping is mandatory

Any endpoint that returns or mutates org-scoped data must validate that the
requesting user belongs to the relevant org. Use `user_belongs_to_org()` from
`transaction_service` or check membership explicitly. Never return data by ID
alone without a membership check.

### 4. Keep Celery tasks thin

Celery tasks should:
- Open their own `SessionLocal()` and close it in `finally`.
- Delegate all logic to a service function.
- Use `acks_late=True` so tasks retry on worker crash.
- Let exceptions propagate (don't catch and swallow).

## Running tests

```bash
cd apps/api
uv run pytest -v          # all tests
uv run ruff check .       # lint
uv run ruff format --check .  # format check
```

## Running the deadline checker manually

Instead of waiting for Celery Beat (every 15 min in dev):

```bash
curl -X POST http://localhost:8000/api/v1/admin/check-deadlines \
  -H "Authorization: Bearer $TOKEN"
```

Requires admin role.
