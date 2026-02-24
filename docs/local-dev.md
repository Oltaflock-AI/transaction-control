# Local Dev

```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml up --build
```

API: http://localhost:8000/api/v1/health

Common:

```bash
docker compose -f infra/docker-compose.yml logs -f api
```

```bash
docker compose -f infra/docker-compose.yml exec api bash
```
