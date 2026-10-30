from src.repository.database import get_connection

def get_order_by_id(order_id):
    connection = get_connection()
    try:
        order = connection.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,)
        ).fetchone()
        if order is None:
            return None
        items = connection.execute(
            """
            SELECT
                oi.id,
                oi.menu_item_id,
                mi.name,
                mi.price_cents,
                oi.quantity
            FROM order_items AS oi
            JOIN menu_items AS mi
                ON mi.id = oi.menu_item_id
            WHERE oi.order_id = ?
            ORDER BY oi.id
            """,
            (order_id,)
        ).fetchall()
        result = dict(order)
        result["items"] = [dict(item) for item in items]
        return result
    finally:
        connection.close()

def create_normal_order(restaurant_id, address, items, created_at):
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        restaurant = connection.execute(
            "SELECT id FROM restaurants WHERE id = ?",
            (restaurant_id,)
        ).fetchone()
        if restaurant is None:
            raise ValueError("RESTAURANT_NOT_FOUND")
        food_subtotal = 0
        for item in items:
            menu_item = connection.execute(
                """
                SELECT price_cents
                FROM menu_items
                WHERE id = ? AND restaurant_id = ?
                """,
                (item["menu_item_id"], restaurant_id)
            ).fetchone()
            if menu_item is None:
                raise ValueError("INVALID_MENU_ITEM")
            food_subtotal += (
                menu_item["price_cents"] * item["quantity"]
            )
        total_cents = food_subtotal + 1595
        cursor = connection.execute(
            """
            INSERT INTO orders
            (restaurant_id, status, total_cents, address, created_at)
            VALUES (?, 'PLACED', ?, ?, ?)
            """,
            (restaurant_id, total_cents, address, created_at)
        )
        order_id = cursor.lastrowid
        for item in items:
            connection.execute(
                """
                INSERT INTO order_items
                (order_id, menu_item_id, quantity)
                VALUES (?, ?, ?)
                """,
                (
                    order_id,
                    item["menu_item_id"],
                    item["quantity"]
                )
            )
        connection.commit()
        return {
            "order_id": order_id,
            "status": "PLACED",
            "food_subtotal_cents": food_subtotal,
            "delivery_fee_cents": 1595,
            "total_cents": total_cents
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def update_order_status(order_id, new_status):
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            UPDATE orders
            SET status = ?
            WHERE id = ?
            """,
            (new_status, order_id)
        )
        if cursor.rowcount == 0:
            raise ValueError("ORDER_NOT_FOUND")
        connection.commit()
        return {
            "order_id": order_id,
            "status": new_status
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
