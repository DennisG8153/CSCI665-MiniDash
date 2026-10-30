from fastapi.testclient import TestClient
from src.main import app
from src.repository import database
from src.repository.schema import create_tables

def test_normal_order_creation_and_status_update(tmp_path, monkeypatch):
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
        connection.commit()
    finally:
        connection.close()
    client = TestClient(app)
    response = client.post(
        "/orders",
        json={
            "restaurant_id": restaurant_id,
            "address": "123 Main Street",
            "items": [
                {
                    "menu_item_id": pizza_id,
                    "quantity": 2
                }
            ]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PLACED"
    assert data["food_subtotal_cents"] == 2598
    assert data["delivery_fee_cents"] == 1595
    assert data["total_cents"] == 4193
    order_id = data["order_id"]

    # Verify the order can be retrieved.
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["total_cents"] == 4193
    assert len(response.json()["items"]) == 1

    # Update its status.
    response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "PREPARING"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "PREPARING"

    # Verify the change persisted.
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "PREPARING"


def test_updating_nonexistent_order_returns_404(tmp_path, monkeypatch):
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()
    client = TestClient(app)
    response = client.patch(
        "/orders/999999/status",
        json={"status": "PREPARING"}
    )
    assert response.status_code == 404
