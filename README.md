# transactional-control

First layer of Doma: Transaction Control.

## Quickstart (local)

1. Copy env:

```bash
cp .env.example .env
```

2. Start everything:

```bash
docker compose -f infra/docker-compose.yml up --build
```

3. API health:

```
http://localhost:8000/api/v1/health
```

## Dev workflow

- **API code:** `apps/api`
- **Worker/Beat:** `apps/api/src/tc/workers`
- **Web app:** `apps/web`

## Git workflow

Interns:

1. `feature branch` -> PR to `dev`
2. `dev` -> PR to `main`

## Commands (API container)

```bash
pytest
ruff check .
ruff format .
```
