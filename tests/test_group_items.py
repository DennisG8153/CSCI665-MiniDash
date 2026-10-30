from fastapi.testclient import TestClient
from src.main import app
from src.repository import database
from src.repository.schema import create_tables
import pytest

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


def test_only_owner_can_remove_item(tmp_path, monkeypatch):
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
    join_response = client.post(
        f"/group-orders/{group['share_code']}/join",
        json={"name": "Alex"}
    )
    assert join_response.status_code == 201
    alex = join_response.json()
    # Stacy adds one item.
    add_response = client.post(
        f"/group-orders/{group['share_code']}/items",
        headers={
            "X-Member-Credential": group["host_credential"]
        },
        json={"menu_item_id": menu_item_id, "quantity": 1}
    )
    assert add_response.status_code == 201
    item_id = add_response.json()["item_id"]
    # Alex tries to remove Stacy's item.
    forbidden_response = client.delete(
        f"/group-orders/{group['share_code']}/items/{item_id}",
        headers={
            "X-Member-Credential": alex["member_credential"]
        }
    )
    assert forbidden_response.status_code == 404
    # Stacy removes her own item.
    owner_response = client.delete(
        f"/group-orders/{group['share_code']}/items/{item_id}",
        headers={
            "X-Member-Credential": group["host_credential"]
        }
    )
    assert owner_response.status_code == 200
    # Confirm the item no longer exists.
    connection = database.get_connection()
    try:
        row = connection.execute(
            "SELECT id FROM group_order_items WHERE id = ?",
            (item_id,)
        ).fetchone()
        assert row is None
    finally:
        connection.close()

@pytest.fixture
def group_with_menu(tmp_path, monkeypatch):
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
        other_restaurant = connection.execute(
            """
            INSERT INTO restaurants
            (name, cuisine, opens_at, closes_at, avg_prep_minutes)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Taco Shop", "Mexican", "10:00", "22:00", 20)
        )
        other_item = connection.execute(
            """
            INSERT INTO menu_items
            (restaurant_id, name, price_cents)
            VALUES (?, ?, ?)
            """,
            (other_restaurant.lastrowid, "Taco", 399)
        )
        other_menu_item_id = other_item.lastrowid
        connection.commit()
    finally:
        connection.close()
    client = TestClient(app)
    response = client.post(
        "/group-orders",
        json={"restaurant_id": restaurant_id, "host_name": "Stacy"}
    )
    assert response.status_code == 201
    return client, response.json(), menu_item_id, other_menu_item_id


@pytest.mark.parametrize(
    "quantity, expected_status",
    [
        (0, 422),
        (-1, 422),
        (2, 201),
    ]
)
def test_item_quantity_validation(
    group_with_menu, quantity, expected_status
):
    client, group, menu_item_id, _ = group_with_menu
    response = client.post(
        f"/group-orders/{group['share_code']}/items",
        headers={
            "X-Member-Credential": group["host_credential"]
        },
        json={"menu_item_id": menu_item_id, "quantity": quantity}
    )
    assert response.status_code == expected_status

def test_wrong_credential_cannot_add_item(group_with_menu):
    client, group, menu_item_id, _ = group_with_menu
    response = client.post(
        f"/group-orders/{group['share_code']}/items",
        headers={"X-Member-Credential": "incorrect-credential"},
        json={"menu_item_id": menu_item_id, "quantity": 1}
    )

    assert response.status_code == 401


def test_cannot_add_item_from_other_restaurant(group_with_menu):
    client, group, _, other_menu_item_id = group_with_menu
    response = client.post(
        f"/group-orders/{group['share_code']}/items",
        headers={
            "X-Member-Credential": group["host_credential"]
        },
        json={"menu_item_id": other_menu_item_id, "quantity": 1}
    )
    assert response.status_code == 422

def test_cannot_add_to_locked_group(group_with_menu):
    client, group, menu_item_id, _ = group_with_menu
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
        f"/group-orders/{group['share_code']}/items",
        headers={
            "X-Member-Credential": group["host_credential"]
        },
        json={"menu_item_id": menu_item_id, "quantity": 1}
    )
    assert response.status_code == 409
