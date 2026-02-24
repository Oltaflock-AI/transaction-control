"""Seed the database with a dev org and user.

Run from the apps/api directory:
    uv run python -m scripts.seed_db
Or via the project root:
    docker compose -f infra/docker-compose.yml exec api \
        uv run python /app/apps/api/../../scripts/seed_db.py

This script is intentionally standalone so it works outside the app too.
"""

import sys
from pathlib import Path

# Ensure the api src is on the path when running standalone
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api" / "src"))

import bcrypt

from tc.core.config import settings  # noqa: E402
from tc.db.base import Base  # noqa: E402
from tc.db.models import Membership, Org, User  # noqa: E402
from tc.db.session import SessionLocal, engine  # noqa: E402


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing = db.query(Org).filter_by(slug="dev-org").first()
        if existing:
            print(f"Seed already applied — org '{existing.name}' exists. Skipping.")
            return

        org = Org(name="Dev Organisation", slug="dev-org")
        db.add(org)
        db.flush()

        user = User(
            email="admin@dev.local",
            full_name="Dev Admin",
            hashed_password=_hash_password("password123"),
        )
        db.add(user)
        db.flush()

        membership = Membership(org_id=org.id, user_id=user.id, role="admin")
        db.add(membership)

        db.commit()
        print(f"Seeded org='{org.name}' (id={org.id})")
        print(f"Seeded user='{user.email}' (id={user.id}) with role=admin")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"DATABASE_URL = {settings.DATABASE_URL}")
    seed()
    print("Done.")
