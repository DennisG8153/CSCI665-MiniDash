import sqlite3
import pytest
from src.repository.schema import create_tables
from src.repository import database ## EVERY TEST USES A SEPARATE TEMPORARY DATABASE TO TEST FUNCTIONS BUT DOES NOT AFFECT THE REAL DATABASE. THE DATABASES HOWEVER, ARE BASED ON THE SCHEMA DEFINED IN schema.py 

def test_invalid_group_status(tmp_path, monkeypatch): # Uses a temporary database to avoid modifying the real data.
    test_db = tmp_path / "test_minidash.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()  # Initialize the database schema in the temporary database.
    connection = database.get_connection() # Get connection to our temporary database.
    try: # Creating a restaurant for the foreign key.
        connection.execute(
            """
            INSERT INTO restaurants (name, cuisine, opens_at, closes_at, avg_prep_minutes) VALUES (?,?,?,?,?)""",
            ("Test Restaurant", "Middle Eastern", "10:00", "22:00", 30)
        )
        restaurant_id = connection.execute(
            "SELECT id FROM restaurants"
        ).fetchone()[0]
        # Any invalid status SHOULD be rejected.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO group_orders (restaurant_id, share_code, status, created_at, last_activity_at) VALUES (?,?,?,?,?)",
                (restaurant_id, "ABCDNAYEON", "INVALID_STATUS", "2026-10-30T12:00:00", "2026-10-30T12:00:00")
            )
    finally:
        connection.close()

def test_duplicate_share_code(tmp_path, monkeypatch): # Creating an isolated test database.
    test_db = tmp_path / "test_minidash.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()
    connection = database.get_connection()
    try: #Inserting test restaurant.
        connection.execute(
            "INSERT INTO restaurants (name, cuisine, opens_at, closes_at, avg_prep_minutes) VALUES (?,?,?,?,?)", ("Test Restaurant", "Middle Eastern", "10:00", "22:00", 30)
        )
        restaurant_id = connection.execute(
            "SELECT id FROM restaurants"
        ).fetchone()[0]
        #Creating first group order
        connection.execute(
            "INSERT INTO group_orders (restaurant_id, share_code, status, created_at, last_activity_at) VALUES (?,?,?,?,?)",
            (restaurant_id, "ABCDNAYEON", "OPEN", "2026-10-30T12:00:00", "2026-10-30T12:00:00")
        )
        # Attempting to create another group with the SAME code.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO group_orders (restaurant_id, share_code, status, created_at, last_activity_at) VALUES (?,?,?,?,?)",
                (restaurant_id, "ABCDNAYEON", "OPEN", "2026-10-30T12:00:00", "2026-10-30T12:00:00")
            )
    finally:
        connection.close()

def test_invalid_restaurant_FK(tmp_path, monkeypatch):
        test_db = tmp_path / "test_minidash.db"
        monkeypatch.setattr(database, "DB_PATH", test_db)
        create_tables()
        connection = database.get_connection()
        try:
            # Attempting to insert a group order with a non-existent restaurant_id
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO group_orders (restaurant_id, share_code, status, created_at, last_activity_at) VALUES (?,?,?,?,?)",
                    (9999, "INVALIDFK", "OPEN", "2026-10-30T12:00:00", "2026-10-30T12:00:00")
                )
        finally:
            connection.close()

def test_one_host_per_group(tmp_path, monkeypatch):
    test_db = tmp_path / "test_minidash.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()
    connection = database.get_connection()
    try: # Creating Restaurant
        cursor = connection.execute(
            "INSERT INTO restaurants (name, cuisine, opens_at, closes_at, avg_prep_minutes) VALUES (?,?,?,?,?)", ("Test Restaurant", "Middle Eastern", "10:00", "22:00", 30)
        )
        restaurant_id  = cursor.lastrowid
        # Creating a group order
        cursor = connection.execute(
            "INSERT INTO group_orders (restaurant_id, share_code, status, created_at, last_activity_at) VALUES (?,?,?,?,?)",
            (restaurant_id, "SLAYCODE", "OPEN", "2026-10-30T12:00:00", "2026-10-30T12:00:00")
        )
        group_id = cursor.lastrowid
        # Creating first host
        connection.execute(
            "INSERT INTO group_members (group_order_id, name, is_host, credential_hash, joined_at) VALUES (?,?,?,?,?)",
            (group_id, "Stacy", 1, "stayc_girls", "2026-10-30T12:00:00")
        )
        # 2nd Host in the same group has to be rejected.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO group_members (group_order_id, name, is_host, credential_hash, joined_at) VALUES (?,?,?,?,?)",
                (group_id, "John", 1, "John_DOe", "2026-10-30T12:00:00")
            )
    finally:
        connection.close()


def test_invalid_item_quantity(tmp_path, monkeypatch):
    # Create an isolated test database
    test_db = tmp_path / "test_minidash.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    create_tables()
    connection = database.get_connection()

    try:
        # Create a restaurant
        cursor = connection.execute(
            """
            INSERT INTO restaurants
            (name, cuisine, opens_at, closes_at, avg_prep_minutes)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Test Restaurant", "Italian", "10:00", "22:00", 20)
        )
        restaurant_id = cursor.lastrowid

        # Create a menu item
        cursor = connection.execute(
            """
            INSERT INTO menu_items
            (restaurant_id, name, price_cents)
            VALUES (?, ?, ?)
            """,
            (restaurant_id, "Cheese Pizza", 1099)
        )
        menu_item_id = cursor.lastrowid

        # Create a group order
        cursor = connection.execute(
            """
            INSERT INTO group_orders
            (restaurant_id, share_code, status,
             created_at, last_activity_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                restaurant_id, "TEST123", "OPEN",
                "2026-10-30T12:00:00+00:00",
                "2026-10-30T12:00:00+00:00"
            )
        )
        group_id = cursor.lastrowid

        # Create a group member
        cursor = connection.execute(
            """
            INSERT INTO group_members
            (group_order_id, name, is_host,
             credential_hash, joined_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                group_id, "Stacy", 1, "stayc_girls",
                "2026-10-30T12:00:00+00:00"
            )
        )
        member_id = cursor.lastrowid

        # Test zero and negative quantities
        for invalid_quantity in (0, -1):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(
                    """
                    INSERT INTO group_order_items
                    (group_order_id, member_id,
                     menu_item_id, quantity)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        group_id, member_id,
                        menu_item_id, invalid_quantity
                    )
                )

    finally:
        connection.close()