from src.repository import database
from src.repository.schema import create_tables
from src.repository.group_order_repository import create_group_w_host

def test_create_group_w_host(tmp_path, monkeypatch): # Testing with temporary databases again.
    test_db = tmp_path / "test_minidash.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)
    create_tables()
    connection = database.get_connection()
    try: # Create a restaurant for the group.
        cursor = connection.execute(
            "INSERT INTO restaurants (name, cuisine, opens_at, closes_at, avg_prep_minutes) VALUES (?,?,?,?,?)", ("Pizza Palace", "Italian", "10:00", "22:00", 25))
        restaurant_id = cursor.lastrowid
        connection.commit()
    finally:
        connection.close()

    # Create group and host.
    result = create_group_w_host(restaurant_id, "Stacy", "STAYCGIRLS", "test_hash_stace","2026-10-30T12:00:00+00:00")
    assert result['group_order_id'] > 0
    assert result['host_member_id'] > 0
    assert result['share_code'] == "STAYCGIRLS"
    assert result['status'] == 'OPEN'
    connection = database.get_connection()
    try: 
        group = connection.execute(
            "SELECT * FROM group_orders WHERE id = ?", (result['group_order_id'],)
        ).fetchone()
        host = connection.execute(
            "SELECT * FROM group_members WHERE id = ?", (result['host_member_id'],)
        ).fetchone()
        assert group is not None
        assert group['restaurant_id'] == restaurant_id
        assert group['status'] == 'OPEN'
        assert host is not None
        assert host["group_order_id"] == group['id']
        assert host["name"] == "Stacy"
        assert host["is_host"] == 1

    finally:
        connection.close()

import pytest
import sqlite3
def test_group_creation_rollback(tmp_path, monkeypatch):
    # Create an isolated test database
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
        connection.commit()

    finally:
        connection.close()

    #Empty host name does not trigger the IntegrityError; passing None does.

    with pytest.raises(sqlite3.IntegrityError):
        create_group_w_host(
            restaurant_id,
            None,
            "ROLLBACK1",
            "test_hash",
            "2026-10-30T12:00:00+00:00"
        )
    # Verify the group insertion was rolled back
    connection = database.get_connection()
    try:
        group_count = connection.execute(
            "SELECT COUNT(*) FROM group_orders").fetchone()[0]
        member_count = connection.execute(
            "SELECT COUNT(*) FROM group_members").fetchone()[0]
        assert group_count == 0
        assert member_count == 0
    finally:
        connection.close()
