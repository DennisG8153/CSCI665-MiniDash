import pytest
import sqlite3
from unittest.mock import patch
from fastapi import HTTPException
from src.repository import database
from src.repository.schema import create_tables
from src.services.group_order_service import create_group_order
from src.services.group_order_utils import hash_credential

def test_invalid_restaurant(tmp_path, monkeypatch):
    test_db = tmp_path / "test_minidash.db"
    monkeypatch.setattr(database, "DB_PATH",test_db)
    create_tables() # Create without adding any initial data
    with pytest.raises(HTTPException) as exc_info: # Attempt to create a group for nonexistent restaurants.
        create_group_order(restaurant_id=999, host_name="Sarah")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Restaurant not found" # Verifying correct HTTP Error

    
@pytest.mark.parametrize("host_name", [
    "",
    " ",
    "   ",
    "\t"
]) # Test with 4 different invalid host names.
def test_invalid_host_name(tmp_path, monkeypatch, host_name):
    # Create an isolated database
    test_db = tmp_path / "test_minidash.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()
    connection = database.get_connection()
    try:
        # Create a valid restaurant this time.
        cursor = connection.execute(
            "INSERT INTO restaurants (name, cuisine, opens_at, closes_at, avg_prep_minutes) VALUES (?, ?, ?, ?, ?)",("Pizza Palace", "Italian", "10:00", "22:00", 25)
        )
        restaurant_id = cursor.lastrowid
        assert restaurant_id is not None # Verify that SQLite generated a successful ID.
        connection.commit()

    finally:
        connection.close()

    # Attempt creation with an invalid host name.
    with pytest.raises(HTTPException) as error:
        create_group_order(restaurant_id, host_name)

    assert error.value.status_code == 422
    assert error.value.detail == "Host name cannot be empty"

# Test 3
def test_successful_group_creation(tmp_path, monkeypatch):
    test_db = tmp_path / "test_minidash.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()
    connection = database.get_connection()
    try: # Make a valid restaurant again.
        cursor = connection.execute(
            "INSERT INTO restaurants (name, cuisine, opens_at, closes_at, avg_prep_minutes) VALUES (?, ?, ?, ?, ?)",
            ("Pizza Palace", "Italian", "10:00", "22:00", 25)
        )
        restaurant_id = cursor.lastrowid
        assert restaurant_id is not None # Verify that SQLite generated a successful ID.
        connection.commit()
    finally:
        connection.close()
# Create group order
    result = create_group_order(restaurant_id, "Sarah")
    assert result['group_order_id'] > 0
    assert result['host_member_id'] > 0
    assert result["status"] == "OPEN"
    assert len(result["share_code"]) == 8
    assert result["host_credential"]
    connection = database.get_connection() # Verifying records are in SQLite.
    try: 
        group = connection.execute(
            "SELECT * FROM group_orders WHERE id = ?",
            (result['group_order_id'],)).fetchone()
        host = connection.execute(
            "SELECT * FROM group_members WHERE id = ?",
            (result['host_member_id'],)).fetchone()
        assert group is not None
        assert group["restaurant_id"] == restaurant_id
        assert group["share_code"] == result["share_code"]
        assert group["status"] == "OPEN"
        assert group["created_at"] == group["last_activity_at"] #Testing the host is the first member to join the open group.
        assert host is not None
        assert host["group_order_id"] == group['id']
        assert host["name"] == "Sarah"
        assert host["is_host"] == 1
        assert host["credential_hash"] == hash_credential(result["host_credential"]) # Database stores a hash, not the raw credential.
        assert host["credential_hash"] != result["host_credential"] # Ensuring the raw credential is not stored directly.

    finally:
        connection.close()

# test 4
def test_share_code_collision_retry(tmp_path, monkeypatch):
    test_db = tmp_path / "test_minidash.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()
    connection = database.get_connection()
    try: 
        cursor = connection.execute(
            "INSERT INTO restaurants (name, cuisine, opens_at, closes_at, avg_prep_minutes) VALUES (?, ?, ?, ?, ?)",
            ("Pizza Palace", "Italian", "10:00", "22:00", 25)
        )
        restaurant_id = cursor.lastrowid
        assert restaurant_id is not None # Verify that SQLite generated a successful ID.
        connection.execute("INSERT INTO group_orders (restaurant_id, share_code, status, created_at, last_activity_at) VALUES (?,?, 'OPEN', ?, ?)", (restaurant_id, "DupliCAT", "2026-10-30T12:00:00+00:00","2026-10-30T12:00:00+00:00")) #Reserve share code that already exists
        connection.commit()
    finally:
        connection.close()

    # Attempt #1 collides, 2nd generates a new valid code.
    with patch( # makes predictable bhvr.
        "src.services.group_order_service.generate_share_code",
        side_effect=["DupliCAT", "NewCode1"]
    ) as mock_generator:
        result = create_group_order(restaurant_id, "Samuel")
    assert result["share_code"] == "NewCode1"
    assert result["status"] == "OPEN"
    assert mock_generator.call_count == 2
    connection = database.get_connection() # Confirm two distinct group codes exist.
    try:
        codes = [
            row["share_code"]
            for row in connection.execute("SELECT share_code FROM group_orders").fetchall()
        ]
        assert sorted(codes) == ["DupliCAT", "NewCode1"]
    finally:
        connection.close()


def test_share_code_collision_exhausted(tmp_path, monkeypatch):
    # Create a temporary SQLite database
    test_db = tmp_path / "test_minidash.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()
    connection = database.get_connection()
    try:
        # Create a valid restaurant
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
        # Reserve a share code
        connection.execute(
            """
            INSERT INTO group_orders
            (restaurant_id, share_code, status,
             created_at, last_activity_at)
            VALUES (?, ?, 'OPEN', ?, ?)
            """,
            (
                restaurant_id,
                "DUPLICAT",
                "2026-10-30T12:00:00+00:00",
                "2026-10-30T12:00:00+00:00"
            )
        )
        connection.commit()
    finally:
        connection.close()

    # Force every generated share code to collide
    with patch(
        "src.services.group_order_service.generate_share_code",
        return_value="DUPLICAT"
    ) as mock_generator:
        with pytest.raises(HTTPException) as error:
            create_group_order(restaurant_id, "Stacy")

    # Verify the expected error
    assert error.value.status_code == 503
    assert error.value.detail == (
        "Failed to generate unique share code after multiple attempts")
    # Verify exactly five attempts occurred
    assert mock_generator.call_count == 5
    # Verify no additional group was created
    connection = database.get_connection()
    try:
        group_count = connection.execute(
            "SELECT COUNT(*) FROM group_orders"
        ).fetchone()[0]

        assert group_count == 1
    finally:
        connection.close()