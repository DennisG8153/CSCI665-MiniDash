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

def add_group_item(share_code, credential_hash, menu_item_id, quantity, updated_at):
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE") # Used to make sure the group does not become locked or expire between our validation checks and inserting.
        group = connection.execute( #Locate group with share code
            "SELECT * FROM group_orders WHERE share_code = ?", (share_code,)
        ).fetchone()
        if group is None:
            raise ValueError("GROUP_NOT_FOUND")
        if group['status'] != "OPEN": #Reject inactive groups and expire idle open ones
            raise ValueError("GROUP_NOT_OPEN")
        current_time = datetime.fromisoformat(updated_at)
        last_activity_at = datetime.fromisoformat(group["last_activity_at"])
        if current_time >= last_activity_at + timedelta(hours=2): # If more than 2 hours have passed since the last activity...
            connection.execute(
                "UPDATE group_orders SET status = 'EXPIRED' WHERE id = ?", (group["id"],)
            )
            connection.commit()
            raise ValueError("GROUP_EXPIRED")
         # Authenticate the participant using the credential hash.
        member = connection.execute(
            """
            SELECT id
            FROM group_members
            WHERE group_order_id = ? AND credential_hash = ?
            """,
            (group["id"], credential_hash)
        ).fetchone()

        if member is None:
            raise ValueError("INVALID_CREDENTIAL")

        # Check that the item belongs to this restaurant.
        menu_item = connection.execute(
            """
            SELECT id
            FROM menu_items
            WHERE id = ? AND restaurant_id = ?
            """,
            (menu_item_id, group["restaurant_id"])
        ).fetchone()

        if menu_item is None:
            raise ValueError("INVALID_MENU_ITEM")

        # Add an item owned by the authenticated member.
        cursor = connection.execute(
            """
            INSERT INTO group_order_items
            (group_order_id, member_id, menu_item_id, quantity)
            VALUES (?, ?, ?, ?)
            """,
            (group["id"], member["id"], menu_item_id, quantity)
        )

        item_id = cursor.lastrowid

        connection.execute(
            """
            UPDATE group_orders
            SET last_activity_at = ?
            WHERE id = ?
            """,
            (updated_at, group["id"])
        )

        connection.commit()

        return {
            "item_id": item_id,
            "group_order_id": group["id"],
            "member_id": member["id"],
            "menu_item_id": menu_item_id,
            "quantity": quantity
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def remove_group_item(share_code, credential_hash, item_id, updated_at):
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        group = connection.execute(
            "SELECT * FROM group_orders WHERE share_code = ?",
            (share_code,)
        ).fetchone()
        if group is None:
            raise ValueError("GROUP_NOT_FOUND")
        if group["status"] != "OPEN":
            raise ValueError("GROUP_NOT_OPEN")
        current_time = datetime.fromisoformat(updated_at)
        last_activity = datetime.fromisoformat(group["last_activity_at"])
        if current_time >= last_activity + timedelta(hours=2):
            connection.execute(
                "UPDATE group_orders SET status = 'EXPIRED' WHERE id = ?",
                (group["id"],)
            )
            connection.commit()
            raise ValueError("GROUP_EXPIRED")
        # Authenticate the person making the request.
        member = connection.execute(
            """
            SELECT id
            FROM group_members
            WHERE group_order_id = ? AND credential_hash = ?
            """,
            (group["id"], credential_hash)
        ).fetchone()
        if member is None:
            raise ValueError("INVALID_CREDENTIAL")
        # Only find items belonging to this member and group.
        item = connection.execute(
            """
            SELECT id
            FROM group_order_items
            WHERE id = ? AND group_order_id = ? AND member_id = ?
            """,
            (item_id, group["id"], member["id"])
        ).fetchone()
        if item is None:
            raise ValueError("ITEM_NOT_FOUND")
        connection.execute(
            "DELETE FROM group_order_items WHERE id = ?",
            (item_id,)
        )
        connection.execute(
            """
            UPDATE group_orders
            SET last_activity_at = ?
            WHERE id = ?
            """,
            (updated_at, group["id"])
        )
        connection.commit()
        return {
            "message": "Item removed successfully",
            "item_id": item_id
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()