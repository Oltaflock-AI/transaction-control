from unittest.mock import patch


class TestCreateTransaction:
    @patch("tc.workers.tasks.generate_timeline.delay")
    def test_create_success(self, mock_delay, client, auth_header, seed_user):
        _, org = seed_user
        body = {"org_id": str(org.id), "title": "123 Main St"}
        r = client.post("/api/v1/transactions", json=body, headers=auth_header)
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "123 Main St"
        assert data["status"] == "draft"
        assert data["org_id"] == str(org.id)
        mock_delay.assert_called_once()

    @patch("tc.workers.tasks.generate_timeline.delay")
    def test_create_with_optional_fields(self, mock_delay, client, auth_header, seed_user):
        _, org = seed_user
        body = {
            "org_id": str(org.id),
            "title": "456 Oak Ave",
            "description": "Residential sale",
            "property_address": "456 Oak Ave, Springfield",
            "close_date": "2026-04-15",
        }
        r = client.post("/api/v1/transactions", json=body, headers=auth_header)
        assert r.status_code == 201
        data = r.json()
        assert data["description"] == "Residential sale"
        assert data["property_address"] == "456 Oak Ave, Springfield"
        assert data["close_date"] == "2026-04-15"

    def test_create_wrong_org(self, client, auth_header, seed_user):
        import uuid

        body = {"org_id": str(uuid.uuid4()), "title": "No access"}
        r = client.post("/api/v1/transactions", json=body, headers=auth_header)
        assert r.status_code == 403

    def test_create_requires_auth(self, client):
        body = {"org_id": "00000000-0000-0000-0000-000000000000", "title": "x"}
        r = client.post("/api/v1/transactions", json=body)
        assert r.status_code == 401


class TestGetTransaction:
    @patch("tc.workers.tasks.generate_timeline.delay")
    def test_get_by_id(self, mock_delay, client, auth_header, seed_user):
        _, org = seed_user
        create_r = client.post(
            "/api/v1/transactions",
            json={"org_id": str(org.id), "title": "Test Txn"},
            headers=auth_header,
        )
        txn_id = create_r.json()["id"]

        r = client.get(f"/api/v1/transactions/{txn_id}", headers=auth_header)
        assert r.status_code == 200
        assert r.json()["id"] == txn_id
        assert r.json()["title"] == "Test Txn"
        assert "tasks" in r.json()

    def test_get_not_found(self, client, auth_header, seed_user):
        import uuid

        r = client.get(f"/api/v1/transactions/{uuid.uuid4()}", headers=auth_header)
        assert r.status_code == 404

    def test_get_requires_auth(self, client):
        import uuid

        r = client.get(f"/api/v1/transactions/{uuid.uuid4()}")
        assert r.status_code == 401


class TestListTransactions:
    @patch("tc.workers.tasks.generate_timeline.delay")
    def test_list_returns_created(self, mock_delay, client, auth_header, seed_user):
        _, org = seed_user
        client.post(
            "/api/v1/transactions",
            json={"org_id": str(org.id), "title": "Txn A"},
            headers=auth_header,
        )
        client.post(
            "/api/v1/transactions",
            json={"org_id": str(org.id), "title": "Txn B"},
            headers=auth_header,
        )

        r = client.get("/api/v1/transactions", headers=auth_header)
        assert r.status_code == 200
        titles = {t["title"] for t in r.json()}
        assert titles == {"Txn A", "Txn B"}

    def test_list_empty_when_no_transactions(self, client, auth_header, seed_user):
        r = client.get("/api/v1/transactions", headers=auth_header)
        assert r.status_code == 200
        assert r.json() == []


class TestTimelineService:
    """Verify that generate_default_timeline produces tasks + timeline items."""

    def test_generates_five_tasks(self, db, seed_user):
        import uuid

        from tc.db.models.task import Task
        from tc.db.models.timeline import TimelineItem
        from tc.db.models.transaction import Transaction
        from tc.services.timeline_service import generate_default_timeline

        _, org = seed_user
        txn = Transaction(id=uuid.uuid4(), org_id=org.id, title="Timeline Test")
        db.add(txn)
        db.commit()

        tasks = generate_default_timeline(db, txn.id)
        assert len(tasks) == 5

        db_tasks = db.query(Task).filter(Task.transaction_id == txn.id).all()
        assert len(db_tasks) == 5

        db_items = db.query(TimelineItem).filter(TimelineItem.transaction_id == txn.id).all()
        assert len(db_items) == 5

    def test_tasks_have_staggered_due_dates(self, db, seed_user):
        import uuid

        from tc.db.models.task import Task
        from tc.db.models.transaction import Transaction
        from tc.services.timeline_service import generate_default_timeline

        _, org = seed_user
        txn = Transaction(id=uuid.uuid4(), org_id=org.id, title="Due Date Test")
        db.add(txn)
        db.commit()

        generate_default_timeline(db, txn.id)
        tasks = db.query(Task).filter(Task.transaction_id == txn.id).order_by(Task.due_at).all()
        due_dates = [t.due_at for t in tasks]
        assert all(a < b for a, b in zip(due_dates, due_dates[1:], strict=False))


class TestGetTasks:
    """GET /transactions/{id}/tasks sub-endpoint."""

    def test_tasks_endpoint_empty_before_timeline(self, db, client, auth_header, seed_user):
        import uuid

        from tc.db.models.transaction import Transaction

        _, org = seed_user
        txn = Transaction(id=uuid.uuid4(), org_id=org.id, title="No tasks yet")
        db.add(txn)
        db.commit()

        r = client.get(f"/api/v1/transactions/{txn.id}/tasks", headers=auth_header)
        assert r.status_code == 200
        assert r.json() == []

    def test_tasks_endpoint_after_timeline(self, db, client, auth_header, seed_user):
        import uuid

        from tc.db.models.transaction import Transaction
        from tc.services.timeline_service import generate_default_timeline

        _, org = seed_user
        txn = Transaction(id=uuid.uuid4(), org_id=org.id, title="With tasks")
        db.add(txn)
        db.commit()

        generate_default_timeline(db, txn.id)

        r = client.get(f"/api/v1/transactions/{txn.id}/tasks", headers=auth_header)
        assert r.status_code == 200
        tasks = r.json()
        assert len(tasks) == 5
        assert tasks[0]["status"] == "todo"
        assert tasks[0]["due_at"] is not None

    def test_tasks_not_found(self, client, auth_header, seed_user):
        import uuid

        r = client.get(f"/api/v1/transactions/{uuid.uuid4()}/tasks", headers=auth_header)
        assert r.status_code == 404

    def test_tasks_requires_auth(self, client):
        import uuid

        r = client.get(f"/api/v1/transactions/{uuid.uuid4()}/tasks")
        assert r.status_code == 401


class TestEndToEnd:
    """Create a transaction, run timeline generation synchronously, verify tasks appear."""

    def test_create_then_tasks_appear(self, db, client, auth_header, seed_user):
        from tc.services.timeline_service import generate_default_timeline

        _, org = seed_user

        with patch("tc.workers.tasks.generate_timeline.delay") as mock_delay:
            r = client.post(
                "/api/v1/transactions",
                json={"org_id": str(org.id), "title": "E2E Test"},
                headers=auth_header,
            )
            assert r.status_code == 201
            txn_id = r.json()["id"]
            mock_delay.assert_called_once_with(txn_id)

        import uuid

        generate_default_timeline(db, uuid.UUID(txn_id))

        r = client.get(f"/api/v1/transactions/{txn_id}", headers=auth_header)
        assert r.status_code == 200
        data = r.json()
        assert len(data["tasks"]) == 5
        assert data["tasks"][0]["status"] == "todo"
