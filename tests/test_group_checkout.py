import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.repository import database
from src.repository.schema import create_tables
import sqlite3

@pytest.fixture
def checkout_group_setup(tmp_path, monkeypatch):
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
            (restaurant_id, "Drink", 299)
        )
        drink_id = drink.lastrowid
        connection.commit()
    finally:
        connection.close()
    client = TestClient(app)
    create_response = client.post(
        "/group-orders",
        json={"restaurant_id": restaurant_id, "host_name": "Stacy"}
    )
    assert create_response.status_code == 201
    group = create_response.json()
    share_code = group["share_code"]
    join_response = client.post(
        f"/group-orders/{share_code}/join",
        json={"name": "Alex"}
    )
    assert join_response.status_code == 201
    alex = join_response.json()
    # Stacy orders two pizzas.
    response = client.post(
        f"/group-orders/{share_code}/items",
        headers={
            "X-Member-Credential": group["host_credential"]
        },
        json={"menu_item_id": pizza_id, "quantity": 2}
    )
    assert response.status_code == 201
    # Alex orders one drink.
    response = client.post(
        f"/group-orders/{share_code}/items",
        headers={
            "X-Member-Credential": alex["member_credential"]
        },
        json={"menu_item_id": drink_id, "quantity": 1}
    )
    assert response.status_code == 201
    return {
        "client": client,
        "group": group,
        "alex": alex,
        "restaurant_id": restaurant_id,
        "pizza_id": pizza_id,
        "drink_id": drink_id
    }
def test_host_checkout_creates_normal_order(checkout_group_setup):
    setup = checkout_group_setup
    client = setup["client"]
    group = setup["group"]
    code = group["share_code"]
    # The host must lock the group first.
    lock_response = client.post(
        f"/group-orders/{code}/lock",
        headers={
            "X-Member-Credential": group["host_credential"]
        }
    )
    assert lock_response.status_code == 200
    # Host checks out with a delivery address.
    checkout_response = client.post(
        f"/group-orders/{code}/checkout",
        headers={
            "X-Member-Credential": group["host_credential"]
        },
        json={"address": "123 Main Street"}
    )
    assert checkout_response.status_code == 200
    data = checkout_response.json()
    # Food: (2 * 1299) + 299 = 2897 cents.
    # Delivery: 1595 cents.
    # Total: 4492 cents.
    assert data["status"] == "CHECKED_OUT"
    assert data["food_subtotal_cents"] == 2897
    assert data["delivery_fee_cents"] == 1595
    assert data["total_cents"] == 4492
    order_id = data["normal_order_id"]
    assert order_id > 0
    connection = database.get_connection()
    try:
        order = connection.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,)
        ).fetchone()
        assert order is not None
        assert order["restaurant_id"] == setup["restaurant_id"]
        assert order["status"] == "PLACED"
        assert order["total_cents"] == 4492
        assert order["address"] == "123 Main Street"
        items = connection.execute(
            """
            SELECT menu_item_id, quantity
            FROM order_items
            WHERE order_id = ?
            """,
            (order_id,)
        ).fetchall()
        saved_items = {
            row["menu_item_id"]: row["quantity"]
            for row in items
        }
        assert saved_items == {
            setup["pizza_id"]: 2,
            setup["drink_id"]: 1
        }
        saved_group = connection.execute(
            "SELECT * FROM group_orders WHERE id = ?",
            (group["group_order_id"],)
        ).fetchone()
        assert saved_group["status"] == "CHECKED_OUT"
        assert saved_group["normal_order_id"] == order_id
    finally:
        connection.close()

    # Checkout cannot happen twice.
    second_response = client.post(
        f"/group-orders/{code}/checkout",
        headers={
            "X-Member-Credential": group["host_credential"]
        },
        json={"address": "123 Main Street"}
    )
    assert second_response.status_code == 409

def test_non_host_cannot_checkout(checkout_group_setup):
    setup = checkout_group_setup
    client = setup["client"]
    group = setup["group"]
    alex = setup["alex"]
    code = group["share_code"]
    # Lock the group using Stacy's credential.
    lock_response = client.post(
        f"/group-orders/{code}/lock",
        headers={
            "X-Member-Credential": group["host_credential"]
        }
    )
    assert lock_response.status_code == 200
    # Alex attempts checkout.
    response = client.post(
        f"/group-orders/{code}/checkout",
        headers={
            "X-Member-Credential": alex["member_credential"]
        },
        json={"address": "123 Main Street"}
    )
    assert response.status_code == 403
    # Rejected checkout must not create a normal order.
    connection = database.get_connection()
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]
        assert count == 0
        saved_group = connection.execute(
            "SELECT status FROM group_orders WHERE id = ?",
            (group["group_order_id"],)
        ).fetchone()
        assert saved_group["status"] == "LOCKED"
    finally:
        connection.close()

# Test Empty-Group-Checkout
def test_cannot_checkout_empty_group(tmp_path, monkeypatch):
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
    headers = {
        "X-Member-Credential": group["host_credential"]
    }
    code = group["share_code"]
    response = client.post(
        f"/group-orders/{code}/lock",
        headers=headers
    )
    assert response.status_code == 200
    response = client.post(
        f"/group-orders/{code}/checkout",
        headers=headers,
        json={"address": "123 Main Street"}
    )
    assert response.status_code == 422
    connection = database.get_connection()
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        group_row = connection.execute(
            """
            SELECT status, normal_order_id
            FROM group_orders
            WHERE id = ?
            """,
            (group["group_order_id"],)
        ).fetchone()
        assert count == 0
        assert group_row["status"] == "LOCKED"
        assert group_row["normal_order_id"] is None
    finally:
        connection.close()

# Transitional Rollback
def test_checkout_rolls_back_on_item_failure(checkout_group_setup):
    setup = checkout_group_setup
    client = setup["client"]
    group = setup["group"]
    code = group["share_code"]
    headers = {
        "X-Member-Credential": group["host_credential"]
    }
    response = client.post(
        f"/group-orders/{code}/lock",
        headers=headers
    )
    assert response.status_code == 200
    # Make normal order-item insertion fail.
    connection = database.get_connection()
    try:
        connection.execute(
            """
            CREATE TRIGGER reject_order_item_insert
            BEFORE INSERT ON order_items
            BEGIN
                SELECT RAISE(ABORT, 'Simulated item insertion failure');
            END;
            """
        )
        connection.commit()
    finally:
        connection.close()
    # Database errors should propagate in TestClient.
    with pytest.raises(
        sqlite3.IntegrityError,
        match="Simulated item insertion failure"
    ):
        client.post(
            f"/group-orders/{code}/checkout",
            headers=headers,
            json={"address": "123 Main Street"}
        )
    # The transaction must leave no partial order behind.
    connection = database.get_connection()
    try:
        order_count = connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]
        item_count = connection.execute(
            "SELECT COUNT(*) FROM order_items"
        ).fetchone()[0]
        group_row = connection.execute(
            """
            SELECT status, normal_order_id
            FROM group_orders
            WHERE id = ?
            """,
            (group["group_order_id"],)
        ).fetchone()
        assert order_count == 0
        assert item_count == 0
        assert group_row["status"] == "LOCKED"
        assert group_row["normal_order_id"] is None
    finally:
        connection.close()

# Testing Ordering Functionality
def test_checked_out_order_can_be_retrieved(checkout_group_setup):
    setup = checkout_group_setup
    client = setup["client"]
    group = setup["group"]
    code = group["share_code"]
    headers = {
        "X-Member-Credential": group["host_credential"]
    }
    # Lock and check out the group.
    lock_response = client.post(
        f"/group-orders/{code}/lock",
        headers=headers
    )
    assert lock_response.status_code == 200
    checkout_response = client.post(
        f"/group-orders/{code}/checkout",
        headers=headers,
        json={"address": "123 Main Street"}
    )
    assert checkout_response.status_code == 200

    order_id = checkout_response.json()["normal_order_id"]

    # Retrieve the resulting normal order.
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    order = response.json()
    assert order["id"] == order_id
    assert order["status"] == "PLACED"
    assert order["total_cents"] == 4492
    assert order["address"] == "123 Main Street"
    assert len(order["items"]) == 2
    quantities = {
        item["menu_item_id"]: item["quantity"]
        for item in order["items"]
    }
    assert quantities == {
        setup["pizza_id"]: 2,
        setup["drink_id"]: 1
    }

def test_get_nonexistent_order_returns_404(checkout_group_setup):
    client = checkout_group_setup["client"]
    response = client.get("/orders/999999")
    assert response.status_code == 404
