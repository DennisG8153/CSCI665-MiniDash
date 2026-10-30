import sqlite3
from datetime import datetime, timezone
from fastapi import HTTPException
from src.repository.restaurant_repository import restaurant_exists
from src.repository.group_order_repository import create_group_w_host
from src.services.group_order_utils import (generate_share_code, generate_member_credential, hash_credential)

def create_group_order(restaurant_id: int, host_name: str):
    if not restaurant_exists(restaurant_id):
        raise HTTPException(status_code=404, detail= "Restaurant not found") #Verify the restaurant exists before creating order.
    #Reject names only containing whitespaces/empty strings.
    host_name = host_name.strip()
    if not host_name:
        raise HTTPException(status_code=422, detail="Host name cannot be empty")
    #Generate private credentials for host
    credential = generate_member_credential()
    credential_hash = hash_credential(credential)
    created_at = datetime.now(timezone.utc).isoformat() # Record creation time in UTC
    for attempt in range(5): # Retry if somehow randomly generated code exists
        share_code = generate_share_code()
        try:
            result = create_group_w_host(restaurant_id, host_name, share_code, credential_hash, created_at)
            return {
                **result, "host_credential": credential
            }
        except sqlite3.IntegrityError as error:
            # Retrying ONLY if shared code is duped.
            if "group_orders.share_code" not in str(error):
                raise
    raise HTTPException(status_code = 503, detail="Failed to generate unique share code after multiple attempts")