
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