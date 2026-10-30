from fastapi.testclient import TestClient
from src.main import app
from src.repository import database
from src.repository.schema import create_tables

def test_member_can_add_item(tmp_path, monkeypatch):
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
        menu_item = connection.execute(
            """
            INSERT INTO menu_items
            (restaurant_id, name, price_cents)
            VALUES (?, ?, ?)
            """,
            (restaurant_id, "Pepperoni Pizza", 1299)
        )
        menu_item_id = menu_item.lastrowid
        connection.commit()
    finally:
        connection.close()
    client = TestClient(app)
    create_response = client.post(
        "/group-orders",
        json={
            "restaurant_id": restaurant_id,
            "host_name": "Stacy"
        }
    )
    assert create_response.status_code == 201
    group = create_response.json()
# Join the group as Alex.
    join_response = client.post(
        f"/group-orders/{group['share_code']}/join",
        json={"name": "Alex"}
    )

    assert join_response.status_code == 201
    member = join_response.json()

    # Alex adds two pizzas using their own credential.
    response = client.post(
        f"/group-orders/{group['share_code']}/items",
        headers={
            "X-Member-Credential": member["member_credential"]
        },
        json={
            "menu_item_id": menu_item_id,
            "quantity": 2
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["group_order_id"] == group["group_order_id"]
    assert data["member_id"] == member["member_id"]
    assert data["menu_item_id"] == menu_item_id
    assert data["quantity"] == 2
    assert data["item_id"] > 0
    # Verify that SQLite saved the correct item owner.
    connection = database.get_connection()
    try:
        saved_item = connection.execute(
            """
            SELECT *
            FROM group_order_items
            WHERE id = ?
            """,
            (data["item_id"],)
        ).fetchone()
        assert saved_item is not None
        assert saved_item["group_order_id"] == group["group_order_id"]
        assert saved_item["member_id"] == member["member_id"]
        assert saved_item["menu_item_id"] == menu_item_id
        assert saved_item["quantity"] == 2
    finally:
        connection.close()
