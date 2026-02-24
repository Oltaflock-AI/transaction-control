class TestHealthPublic:
    def test_health_no_auth(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["ok"] is True


class TestLogin:
    def test_login_valid(self, client, seed_user):
        creds = {"email": "admin@test.local", "password": "password123"}
        r = client.post("/api/v1/auth/login", json=creds)
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client, seed_user):
        creds = {"email": "admin@test.local", "password": "wrong"}
        r = client.post("/api/v1/auth/login", json=creds)
        assert r.status_code == 401

    def test_login_unknown_email(self, client, seed_user):
        creds = {"email": "nobody@test.local", "password": "x"}
        r = client.post("/api/v1/auth/login", json=creds)
        assert r.status_code == 401


class TestDevToken:
    def test_dev_token_ok(self, client, seed_user):
        r = client.post("/api/v1/auth/dev-token", json={"email": "admin@test.local"})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_dev_token_unknown_user(self, client, seed_user):
        r = client.post("/api/v1/auth/dev-token", json={"email": "ghost@test.local"})
        assert r.status_code == 404


class TestProtectedEndpoints:
    def test_transactions_requires_auth(self, client):
        r = client.get("/api/v1/transactions")
        assert r.status_code == 401

    def test_transactions_with_valid_token(self, client, auth_header, seed_user):
        r = client.get("/api/v1/transactions", headers=auth_header)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_transactions_with_garbage_token(self, client):
        r = client.get("/api/v1/transactions", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401

    def test_transactions_with_expired_token(self, client, seed_user):
        from datetime import UTC, datetime, timedelta

        from jose import jwt

        from tc.core.config import settings

        user, _ = seed_user
        exp = datetime.now(UTC) - timedelta(hours=1)
        payload = {"sub": str(user.id), "exp": int(exp.timestamp()), "iat": int(exp.timestamp())}
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
        r = client.get("/api/v1/transactions", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401


class TestTokenFromLogin:
    """End-to-end: login then use token to call a protected endpoint."""

    def test_login_then_call_transactions(self, client, seed_user):
        login_r = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@test.local", "password": "password123"},
        )
        token = login_r.json()["access_token"]

        txn_r = client.get("/api/v1/transactions", headers={"Authorization": f"Bearer {token}"})
        assert txn_r.status_code == 200
