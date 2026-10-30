from fastapi.testclient import TestClient
from src.main import app
from src.repository import database
from src.repository.schema import create_tables
from src.services.group_order_utils import hash_credential
import pytest

#Insert restaurant we can order from.
def test_create_group_endpoint(tmp_path, monkeypatch):
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()
    connection = database.get_connection()
    try:
        cursor = connection.execute(
            """
            INSERT INTO restaurants
            (name, cuisine, opens_at, closes_at, avg_prep_minutes)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Pizza Palace", "Italian", "10:00", "22:00", 25)
        )
        restaurant_id = cursor.lastrowid
        assert restaurant_id is not None
        connection.commit()
    finally:
            connection.close()

    # Send an HTTP request to FastAPI
    client = TestClient(app)

    response = client.post(
            "/group-orders",
            json={
                "restaurant_id": restaurant_id,
                "host_name": "Stacy"
            }
        )
    assert response.status_code == 201 # Check the response

    data = response.json()

    assert data["group_order_id"] > 0
    assert data["host_member_id"] > 0
    assert data["status"] == "OPEN"
    assert len(data["share_code"]) == 8
    assert data["host_credential"]

    # Independently verify the saved records
    connection = database.get_connection()

    try:
        group = connection.execute(
            "SELECT * FROM group_orders WHERE id = ?",
            (data["group_order_id"],)
        ).fetchone()

        host = connection.execute(
            "SELECT * FROM group_members WHERE id = ?",
            (data["host_member_id"],)
        ).fetchone()

        assert group is not None
        assert group["restaurant_id"] == restaurant_id
        assert group["share_code"] == data["share_code"]

        assert host is not None
        assert host["group_order_id"] == group["id"]
        assert host["is_host"] == 1
        assert host["credential_hash"] == hash_credential(
            data["host_credential"]
        )

    finally:
        connection.close()
#Test 2-7
@pytest.mark.parametrize(
    "request_data",
    [
        {"restaurant_id": 0, "host_name": "Stacy"},
        {"restaurant_id": -1, "host_name": "Stacy"},
        {"restaurant_id": 1, "host_name": ""},
        {"restaurant_id": 1, "host_name": "A" * 101},
        {"restaurant_id": 1},
        {"host_name": "Stacy"}
    ]
)
def test_invalid_group_creation_requests(tmp_path, monkeypatch, request_data):
    # Use a fresh temporary database
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()
    client = TestClient(app)
    response = client.post(
        "/group-orders",
        json=request_data
    )
    # Pydantic should reject invalid request bodies
    assert response.status_code == 422
    # Invalid requests must not create group records
    connection = database.get_connection()
    try:
        group_count = connection.execute(
            "SELECT COUNT(*) FROM group_orders"
        ).fetchone()[0]

        assert group_count == 0
    finally:
        connection.close()