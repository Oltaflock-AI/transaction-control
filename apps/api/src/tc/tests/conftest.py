import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tc.core.security import create_access_token, hash_password
from tc.db.base import Base
from tc.db.models.membership import Membership
from tc.db.models.org import Org
from tc.db.models.user import User
from tc.db.session import get_db
from tc.main import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def db():
    Base.metadata.create_all(bind=engine)
    session = TestSession()
    app.dependency_overrides[get_db] = lambda: session
    yield session
    session.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def seed_user(db):
    org = Org(id=uuid.uuid4(), name="Test Org", slug="test-org")
    db.add(org)
    db.flush()

    user = User(
        id=uuid.uuid4(),
        email="admin@test.local",
        full_name="Test Admin",
        hashed_password=hash_password("password123"),
    )
    db.add(user)
    db.flush()

    membership = Membership(id=uuid.uuid4(), org_id=org.id, user_id=user.id, role="admin")
    db.add(membership)
    db.commit()

    return user, org


@pytest.fixture()
def auth_header(seed_user):
    user, _ = seed_user
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}
