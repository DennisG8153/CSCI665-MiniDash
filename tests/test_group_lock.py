from fastapi.testclient import TestClient
from src.main import app
from src.repository import database
from src.repository.schema import create_tables

def test_host_locking_and_member_restrictions(tmp_path, monkeypatch):
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()
    # Create a restaurant.
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
        connection.commit()
    finally:
        connection.close()
    client = TestClient(app)
    # Stacy creates the group.
    response = client.post(
        "/group-orders",
        json={
            "restaurant_id": restaurant_id,
            "host_name": "Stacy"
        }
    )
    assert response.status_code == 201
    group = response.json()
    share_code = group["share_code"]
    # Alex joins as a regular member.
    response = client.post(
        f"/group-orders/{share_code}/join",
        json={"name": "Alex"}
    )
    assert response.status_code == 201
    alex = response.json()
    # Alex cannot lock the group.
    response = client.post(
        f"/group-orders/{share_code}/lock",
        headers={
            "X-Member-Credential": alex["member_credential"]
        }
    )
    assert response.status_code == 403
    # Stacy can lock the group.
    response = client.post(
        f"/group-orders/{share_code}/lock",
        headers={
            "X-Member-Credential": group["host_credential"]
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "LOCKED"
    # Locking the group a second time is not allowed.
    response = client.post(
        f"/group-orders/{share_code}/lock",
        headers={
            "X-Member-Credential": group["host_credential"]
        }
    )
    assert response.status_code == 409
    # Additional participants cannot join.
    response = client.post(
        f"/group-orders/{share_code}/join",
        json={"name": "Jordan"}
    )
    assert response.status_code == 409
    # Verify the group status was saved.
    connection = database.get_connection()
    try:
        saved_group = connection.execute(
            """
            SELECT status
            FROM group_orders
            WHERE id = ?
            """,
            (group["group_order_id"],)
        ).fetchone()

        assert saved_group["status"] == "LOCKED"
    finally:
        connection.close()
