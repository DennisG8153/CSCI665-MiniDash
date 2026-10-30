from fastapi.testclient import TestClient 
from src.main import app
from src.repository import database
from src.repository.schema import create_tables
from datetime import datetime, timedelta, timezone

def test_group_summary_with_two_members(tmp_path, monkeypatch):
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
        restaurant_id = restaurant.lastrowid
        pizza = connection.execute(
            """
            INSERT INTO menu_items
            (restaurant_id, name, price_cents)
            VALUES (?, ?, ?)
            """,
            (restaurant_id, "Pizza", 1299)
        )
        pizza_id = pizza.lastrowid
        drink = connection.execute(
            """
            INSERT INTO menu_items
            (restaurant_id, name, price_cents)
            VALUES (?, ?, ?)
            """,
            (restaurant_id, "Drink", 899)
        )
        drink_id = drink.lastrowid
        connection.commit()
    finally:
        connection.close()
    client = TestClient(app)
    
    # Stacy creates a group.
    response = client.post(
        "/group-orders",
        json={
            "restaurant_id": restaurant_id,
            "host_name": "Stacy"
        }
    )
    assert response.status_code == 201
    group = response.json()

    # Alex joins.
    response = client.post(
        f"/group-orders/{group['share_code']}/join",
        json={"name": "Alex"}
    )
    assert response.status_code == 201
    alex = response.json()

    # Stacy orders one pizza.
    response = client.post(
        f"/group-orders/{group['share_code']}/items",
        headers={
            "X-Member-Credential": group["host_credential"]
        },
        json={"menu_item_id": pizza_id, "quantity": 1}
    )
    assert response.status_code == 201

    # Alex orders one drink.
    response = client.post(
        f"/group-orders/{group['share_code']}/items",
        headers={
            "X-Member-Credential": alex["member_credential"]
        },
        json={"menu_item_id": drink_id, "quantity": 1}
    )
    assert response.status_code == 201
    # Request the group summary.
    response = client.get(
        f"/group-orders/{group['share_code']}/summary"
    )
    assert response.status_code == 200
    summary = response.json()
    members = {
        member["name"]: member
        for member in summary["members"]
    }
    assert summary["status"] == "OPEN"
    assert summary["delivery_fee_cents"] == 1595
    assert summary["food_subtotal_cents"] == 2198
    assert summary["grand_total_cents"] == 3793
    assert members["Stacy"]["food_subtotal_cents"] == 1299
    assert members["Alex"]["food_subtotal_cents"] == 899
    # The entire delivery fee must be accounted for.
    assert sum(
        member["delivery_fee_cents"]
        for member in summary["members"]
    ) == 1595
    # Every member's total must match their subtotal plus fee.
    for member in summary["members"]:
        assert member["total_cents"] == (
            member["food_subtotal_cents"]
            + member["delivery_fee_cents"]
        )
    assert sum(
        member["total_cents"]
        for member in summary["members"]
    ) == summary["grand_total_cents"]

def test_summary_marks_inactive_group_expired(tmp_path, monkeypatch):
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
        restaurant_id = restaurant.lastrowid
        connection.commit()
    finally:
        connection.close()
    client = TestClient(app)
    response = client.post(
        "/group-orders",
        json={"restaurant_id": restaurant_id, "host_name": "Stacy"}
    )
    assert response.status_code == 201
    group = response.json()
    # Simulate three hours without activity.
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
    # Reading the summary should recognize the expiration.
    response = client.get(
        f"/group-orders/{group['share_code']}/summary"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "EXPIRED"
    # Confirm that expiration was persisted.
    connection = database.get_connection()
    try:
        saved_group = connection.execute(
            "SELECT status FROM group_orders WHERE id = ?",
            (group["group_order_id"],)
        ).fetchone()
        assert saved_group["status"] == "EXPIRED"
    finally:
        connection.close()
