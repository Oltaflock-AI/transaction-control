# Architecture (Transaction Control)

- Postgres is the source of truth.
- FastAPI is the controller (HTTP).
- Celery worker runs async jobs (timeline generation, notifications).
- Celery beat runs scheduled checks (deadlines).

Boundaries:
- Routers (HTTP) call Services (business logic)
- Services use db session + domain models
- Workers are thin wrappers around services
