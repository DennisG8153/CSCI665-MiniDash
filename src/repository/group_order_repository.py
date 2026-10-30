from datetime import datetime, timedelta, timezone
from src.repository.database import get_connection

def create_group_w_host(restaurant_id, host_name, share_code, credential_hash, created_at):
    connection = get_connection()
    try:
        cursor = connection.execute(
            "INSERT INTO group_orders (restaurant_id, share_code, status, created_at, last_activity_at) VALUES (?, ?, 'OPEN', ?, ?)",(restaurant_id, share_code, created_at, created_at)
        )
        group_id = cursor.lastrowid

        # Create host as the first member
        cursor = connection.execute(
            "INSERT INTO group_members (group_order_id, name, is_host, credential_hash, joined_at) VALUES (?, ?, 1, ?, ?)",(group_id, host_name, credential_hash, created_at)
        )
        host_id = cursor.lastrowid
        connection.commit()
        return {
            "group_order_id": group_id,
            "host_member_id": host_id,
            "share_code": share_code,
            "status": "OPEN"
        }
    except Exception:
        connection.rollback()  # Abort both insertions if anything goes wrong.
        raise
    finally:
        connection.close()

def get_group_by_code(share_code):
    connection = get_connection()
    try: 
        row = connection.execute(
            "SELECT * FROM group_orders WHERE share_code = ?", (share_code,)).fetchone()
        return dict(row) if row else None
    finally:
        connection.close()

def count_group_members(group_id):
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT COUNT(*) FROM group_members WHERE group_order_id = ?", (group_id,)
        ).fetchone()[0]
    finally:
        connection.close()

def add_group_member(group_id, name, credential_hash, joined_at):
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE") # LOCK the SQLite database during this transaction.
        group = connection.execute(
            "SELECT status, last_activity_at FROM group_orders WHERE id = ?", (group_id,)
        ).fetchone()
        if group is None:
            raise ValueError("GROUP_NOT_FOUND")
        if group["status"] != "OPEN":
            raise ValueError("GROUP_NOT_OPEN")
        current_time = datetime.fromisoformat(joined_at)
        last_activity_at = datetime.fromisoformat(group["last_activity_at"])
        if current_time >= last_activity_at + timedelta(hours=2): # If more than 2 hours have passed since the last activity...
            connection.execute(
                "UPDATE group_orders SET status = 'EXPIRED' WHERE id = ?", (group_id,)
            )
            connection.commit()
            raise ValueError("GROUP_EXPIRED")
        member_count = connection.execute(
            "SELECT COUNT(*) FROM group_members WHERE group_order_id = ?", (group_id,)
        ).fetchone()[0]
        if member_count >= 10:  # MAX 10 members allowed
            raise ValueError("GROUP_FULL")
        cursor = connection.execute( #Insert new member
            "INSERT INTO group_members (group_order_id, name, is_host, credential_hash, joined_at) VALUES (?,?,0,?,?)", (group_id, name, credential_hash, joined_at)
            )
        member_id = cursor.lastrowid
        connection.execute( # Reset inactivity timer after joining successfully.
        "UPDATE group_orders SET last_activity_at = ? WHERE id = ?", (joined_at, group_id)
        )
        connection.commit()
        return member_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()