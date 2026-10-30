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

def get_group_summary_data(share_code):
    connection = get_connection()
    try:
        group = connection.execute(
            "SELECT * FROM group_orders WHERE share_code = ?",
            (share_code,)
        ).fetchone()
        if group is None:
            return None
         # Expire an OPEN group after two hours of inactivity.
        if group["status"] == "OPEN":
            current_time = datetime.now(timezone.utc)
            last_activity = datetime.fromisoformat(
                group["last_activity_at"]
            )

            if current_time >= last_activity + timedelta(hours=2):
                connection.execute(
                    """
                    UPDATE group_orders
                    SET status = 'EXPIRED'
                    WHERE id = ? AND status = 'OPEN'
                    """,
                    (group["id"],)
                )
                connection.commit()

                # Read the updated status for the summary.
                group = connection.execute(
                    "SELECT * FROM group_orders WHERE id = ?",
                    (group["id"],)
                ).fetchone()

        members = connection.execute(
            """
            SELECT
                gm.id AS member_id,
                gm.name AS name,
                COALESCE(
                    SUM(goi.quantity * mi.price_cents), 0
                ) AS food_subtotal_cents
            FROM group_members AS gm
            LEFT JOIN group_order_items AS goi
                ON goi.member_id = gm.id
                AND goi.group_order_id = gm.group_order_id
            LEFT JOIN menu_items AS mi
                ON mi.id = goi.menu_item_id
            WHERE gm.group_order_id = ?
            GROUP BY gm.id, gm.name
            ORDER BY gm.id
            """,
            (group["id"],)
        ).fetchall() # The SQLite function mutiplies each item's quantity by it's price then uses Sum() to calculate the member's subtotal. Left Join is important as it includes people who HAVEN'T ordered anything with COALESE(..., 0) gives those members a total of 0.

        return {
            "group": dict(group),
            "members": [dict(member) for member in members]
        }

    finally:
        connection.close()

def lock_group_order(share_code, credential_hash, updated_at):
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        group = connection.execute("SELECT id, status, last_activity_at FROM group_orders WHERE share_code = ?", (share_code,)).fetchone()
        if group is None:
            raise ValueError("GROUP_NOT_FOUND")
        if group["status"] != "OPEN":
            raise ValueError("GROUP_NOT_OPEN")
        current_time = datetime.fromisoformat(updated_at)
        last_activity = datetime.fromisoformat(group["last_activity_at"])
        if current_time >= last_activity + timedelta(hours=2):
            connection.execute("UPDATE group_orders SET status = 'EXPIRED' WHERE id = ?", (group["id"],))
            connection.commit()
            raise ValueError("GROUP_EXPIRED")
        host = connection.execute( #Only the host's credentials can lock the group.
        "SELECT id FROM group_members WHERE group_order_id = ? AND credential_hash = ? AND is_host = 1", (group["id"], credential_hash)
        ).fetchone()
        if host is None:
            raise ValueError("HOST_CREDENTIAL_REQUIRED")
        connection.execute(
            "UPDATE group_orders SET status = 'LOCKED', last_activity_at = ? WHERE id = ?",
            (updated_at, group["id"])
        )
        connection.commit()
        return {
            "group_order_id": group["id"],
            "share_code": share_code,
            "status": "LOCKED"
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def checkout_group_order(share_code, credential_hash, address, checked_out_at):
    connection = get_connection()
    try: 
        connection.execute("BEGIN IMMEDIATE")
        group = connection.execute(
            "SELECT * FROM group_orders WHERE share_code = ?",
            (share_code,)
        ).fetchone()
        if group is None:
            raise ValueError("GROUP_NOT_FOUND")
        if group["status"] != "LOCKED":
            raise ValueError("GROUP_NOT_LOCKED")
        host = connection.execute( # Only the host can check out the order
            "SELECT id FROM group_members WHERE group_order_id = ? AND credential_hash = ? AND is_host = 1", (group["id"], credential_hash)
            ).fetchone()
        if host is None:
            raise ValueError("HOST_CREDENTIAL_REQUIRED")
        items = connection.execute( # Retrieve the items and their current prices.
            """
            SELECT
                goi.menu_item_id,
                goi.quantity,
                mi.price_cents
            FROM group_order_items AS goi
            JOIN menu_items AS mi
                ON mi.id = goi.menu_item_id
            WHERE goi.group_order_id = ?
            """,
            (group["id"],)
        ).fetchall()
        if not items:
            raise ValueError("GROUP_EMPTY")
        food_subtotal = sum(
            item["quantity"] * item["price_cents"]
            for item in items
        )
        delivery_fee_cents = 1595
        total_cents = food_subtotal + delivery_fee_cents
        # Create the normal MiniDash order.
        cursor = connection.execute(
            """
            INSERT INTO orders
            (restaurant_id, status, total_cents, address, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                group["restaurant_id"],
                "PLACED",
                total_cents,
                address,
                checked_out_at
            )
        )
        normal_order_id = cursor.lastrowid
        # Copy every group item into the normal order.
        for item in items:
            connection.execute(
                """
                INSERT INTO order_items
                (order_id, menu_item_id, quantity)
                VALUES (?, ?, ?)
                """,
                (
                    normal_order_id,
                    item["menu_item_id"],
                    item["quantity"]
                )
            )
        # Mark the group as checked out.
        connection.execute(
            """
            UPDATE group_orders
            SET status = 'CHECKED_OUT',
                normal_order_id = ?,
                last_activity_at = ?
            WHERE id = ?
            """,
            (
                normal_order_id,
                checked_out_at,
                group["id"]
            )
        )
        connection.commit()
        return {
            "group_order_id": group["id"],
            "normal_order_id": normal_order_id,
            "status": "CHECKED_OUT",
            "food_subtotal_cents": food_subtotal,
            "delivery_fee_cents": delivery_fee_cents,
            "total_cents": total_cents
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
