from fastapi.testclient import TestClient
from src.main import app
from src.repository import database
from src.repository.schema import create_tables
from src.services.group_order_utils import hash_credential

def test_join_group_success(tmp_path, monkeypatch):
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()
    connection = database.get_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO restaurants (name, cuisine, opens_at, closes_at, avg_prep_minutes) VALUES (?, ?, ?, ?, ?)",
            ("Pizza Place", "Italian", "10:00:00", "22:00:00", 25))
        restaurant_id = cursor.lastrowid
        connection.commit()
    finally:
        connection.close()
    client = TestClient(app)
    create_response = client.post( # Create the group with host
        "/group-orders",
        json={
            "restaurant_id": restaurant_id,
            "host_name": "Stacy"
        }
    )
    assert create_response.status_code == 201
    group = create_response.json()
    share_code = group["share_code"]
    # Join as another member.
    response = client.post(
        f"/group-orders/{share_code}/join",
        json={"name": "Alex"}
    )
    assert create_response.status_code == 201
    data = response.json()
    assert data["group_order_id"] == group["group_order_id"]
    assert data["member_id"] > 0
    assert data["member_name"] == "Alex"
    assert data["member_credential"]
    connection = database.get_connection() # Confirm member was stored correctly.
    try: 
        member = connection.execute(
            "SELECT * FROM group_members WHERE id = ?", (data["member_id"],)
        ).fetchone()
        assert member is not None
        assert member["name"] == "Alex"
        assert member["is_host"] == 0
        assert member["credential_hash"] == hash_credential(data["member_credential"])
        count = connection.execute(
            "SELECT COUNT(*) FROM group_members WHERE group_order_id = ?", (group["group_order_id"],)
        ).fetchone()[0]
        assert count == 2 # Host and Alex
    finally:
        connection.close()

from datetime import datetime, timedelta, timezone
import pytest

@pytest.fixture
def existing_group(tmp_path, monkeypatch):
    # Create an isolated database.
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()
    connection = database.get_connection()
    try:
        restaurant = connection.execute(
            """
            INSERT INTO restaurants
            (name, cuisine, opens_at, closes_at, avg_prep_minutes)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Pizza Palace", "Italian", "10:00", "22:00", 25)
        )
        connection.commit()
        restaurant_id = restaurant.lastrowid
    finally:
        connection.close()
    client = TestClient(app)
    response = client.post(
        "/group-orders",
        json={
            "restaurant_id": restaurant_id,
            "host_name": "Stacy"
        }
    )
    assert response.status_code == 201
    return client, response.json()


def test_join_invalid_share_code(existing_group):
    client, group = existing_group
    response = client.post(
        "/group-orders/INVALIDCODE/join",
        json={"name": "Alex"}
    )
    assert response.status_code == 404


def test_join_locked_group(existing_group):
    client, group = existing_group
    connection = database.get_connection()
    try:
        connection.execute(
            "UPDATE group_orders SET status = 'LOCKED' WHERE id = ?",
            (group["group_order_id"],)
        )
        connection.commit()
    finally:
        connection.close()
    response = client.post(
        f"/group-orders/{group['share_code']}/join",
        json={"name": "Alex"}
    )
    assert response.status_code == 409

def test_join_expired_group(existing_group):
    client, group = existing_group
    three_hours_ago = (
        datetime.now(timezone.utc) - timedelta(hours=3)
    ).isoformat()
    connection = database.get_connection()
    try:
        connection.execute(
            """
            UPDATE group_orders
            SET last_activity_at = ?
            WHERE id = ?
            """,
            (three_hours_ago, group["group_order_id"])
        )
        connection.commit()
    finally:
        connection.close()
    response = client.post(
        f"/group-orders/{group['share_code']}/join",
        json={"name": "Alex"}
    )
    assert response.status_code == 410
    # Confirm that the group is now marked EXPIRED.
    connection = database.get_connection()
    try:
        row = connection.execute(
            "SELECT status FROM group_orders WHERE id = ?",
            (group["group_order_id"],)
        ).fetchone()
        assert row["status"] == "EXPIRED"
    finally:
        connection.close()
def test_join_full_group(existing_group):
    client, group = existing_group
    # The host already occupies one of the ten spots.
    for i in range(9):
        response = client.post(
            f"/group-orders/{group['share_code']}/join",
            json={"name": f"Member {i + 1}"}
        )
        assert response.status_code == 201
    # The eleventh person should be rejected.
    response = client.post(
        f"/group-orders/{group['share_code']}/join",
        json={"name": "Extra Member"}
    )
    assert response.status_code == 409
    connection = database.get_connection()
    try:
        count = connection.execute(
            """
            SELECT COUNT(*)
            FROM group_members
            WHERE group_order_id = ?
            """,
            (group["group_order_id"],)
        ).fetchone()[0]
        assert count == 10
    finally:
        connection.close()
from src.repository.group_order_repository import add_group_member
def test_join_expires_at_exactly_two_hours(tmp_path, monkeypatch):
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()
    created_at = datetime(
        2026, 10, 30, 12, 0, tzinfo=timezone.utc
    )
    connection = database.get_connection()
    try:
        restaurant = connection.execute(
            """
            INSERT INTO restaurants
            (name, cuisine, opens_at, closes_at, avg_prep_minutes)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Pizza Palace", "Italian", "10:00", "22:00", 25)
        )
        restaurant_id = restaurant.lastrowid
        group = connection.execute(
            """
            INSERT INTO group_orders
            (restaurant_id, share_code, status,
             created_at, last_activity_at)
            VALUES (?, ?, 'OPEN', ?, ?)
            """,
            (
                restaurant_id,
                "BOUND123",
                created_at.isoformat(),
                created_at.isoformat()
            )
        )
        group_id = group.lastrowid
        connection.commit()
    finally:
        connection.close()
    # Exactly two hours after the group's last activity.
    joined_at = (
        created_at + timedelta(hours=2)
    ).isoformat()
    with pytest.raises(ValueError, match="GROUP_EXPIRED"):
        add_group_member(
            group_id=group_id,
            name="Alex",
            credential_hash="test_hash",
            joined_at=joined_at
        )
    # Confirm expiration was saved and no member joined.
    connection = database.get_connection()
    try:
        group_row = connection.execute(
            "SELECT status FROM group_orders WHERE id = ?",
            (group_id,)
        ).fetchone()
        assert group_row["status"] == "EXPIRED"
        member_count = connection.execute(
            """
            SELECT COUNT(*) FROM group_members
            WHERE group_order_id = ?
            """,
            (group_id,)
        ).fetchone()[0]
        assert member_count == 0
    finally:
        connection.close()