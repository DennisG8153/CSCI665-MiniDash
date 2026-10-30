import sqlite3
from datetime import datetime, timezone
from fastapi import HTTPException
from src.repository.restaurant_repository import restaurant_exists
from src.services.group_order_utils import (generate_share_code, generate_member_credential, hash_credential)
from src.repository.group_order_repository import (create_group_w_host, get_group_by_code, add_group_member, add_group_item, remove_group_item)
from src.repository.group_order_repository import get_group_summary_data
from src.services.group_order_utils import split_delivery_fee

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

def join_group_order(share_code: str, name: str):
    group = get_group_by_code(share_code)

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Reject names containing only whitespace or empty strings.
    name = name.strip()

    if not name:
        raise HTTPException(status_code=422, detail="Name cannot be empty")

    # Generate private credentials for member.
    credential = generate_member_credential()
    credential_hash = hash_credential(credential)
    joined_at = datetime.now(timezone.utc).isoformat()  # Record join time in UTC.
    try:
        member_id = add_group_member(
            group_id=group["id"],
            name=name,
            credential_hash=credential_hash,
            joined_at=joined_at
        )
        return {
            "group_order_id": group["id"],
            "member_id": member_id,
            "member_name": name,
            "member_credential": credential
        } # Return Values
    except ValueError as error: #Error Handling
        reason = str(error)
        if reason == "GROUP_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail="Group not found"
            )
        elif reason == "GROUP_NOT_OPEN":
            raise HTTPException(
                status_code=409,
                detail="Group is not open for joining"
            )
        elif reason == "GROUP_EXPIRED":
            raise HTTPException(
                status_code=410,
                detail="Group has expired"
            )
        elif reason == "GROUP_FULL":
            raise HTTPException(
                status_code=409,
                detail="Group is full"
            )
        else:
            raise

def add_item_to_group(share_code: str, credential: str, menu_item_id: int, quantity: int):
    if not credential:
        raise HTTPException(status_code=401, detail="Member credential required")
    credential_hash = hash_credential(credential)
    updated_at = datetime.now(timezone.utc).isoformat()
    try: 
        return add_group_item(
            share_code=share_code,
            credential_hash=credential_hash,
            menu_item_id=menu_item_id,
            quantity=quantity,
            updated_at=updated_at
        )
    except ValueError as error:
        reason = str(error)
        if reason == "GROUP_NOT_FOUND":
            raise HTTPException(404, "Group not found")
        if reason == "GROUP_EXPIRED":
            raise HTTPException(410, "Group has expired")
        if reason == "GROUP_NOT_OPEN":
            raise HTTPException(409, "Group is not open")
        if reason == "INVALID_CREDENTIAL":
            raise HTTPException(401, "Invalid member credential")
        if reason == "INVALID_MENU_ITEM":
            raise HTTPException(422,"Menu item does not belong to this restaurant")
        raise

def remove_item_from_group(share_code: str, credential: str, item_id: int):
    if not credential:
        raise HTTPException(status_code=401, detail="Member credential required")
    credential_hash = hash_credential(credential)
    updated_at = datetime.now(timezone.utc).isoformat()
    try:
        return remove_group_item(
            share_code=share_code,
            credential_hash=credential_hash,
            item_id=item_id,
            updated_at=updated_at
        )
    except ValueError as error:
        reason = str(error)
        if reason == "GROUP_NOT_FOUND":
            raise HTTPException(404, "Group not found")
        if reason == "GROUP_EXPIRED":
            raise HTTPException(410, "Group has expired")
        if reason == "GROUP_NOT_OPEN":
            raise HTTPException(409, "Group is not open")
        if reason == "INVALID_CREDENTIAL":
            raise HTTPException(401, "Invalid member credential")
        if reason == "ITEM_NOT_FOUND":
            raise HTTPException(404, "Item not found")
        raise

DELIVERY_FEE = 1595 #Price
def get_group_order_summary(share_code: str):
    data = get_group_summary_data(share_code)
    if data is None:
        raise HTTPException(status_code=404, detail="Group not found")
    group = data["group"]
    members = data["members"]
    member_ids = [member["member_id"] for member in members]
    fee_shares = split_delivery_fee(DELIVERY_FEE, member_ids)
    summary_members = []
    for member in members:
        member_id = member["member_id"]
        subtotal = member["food_subtotal_cents"]
        fee_share = fee_shares[member_id]

        summary_members.append({
            "member_id": member_id,
            "name": member["name"],
            "food_subtotal_cents": subtotal,
            "delivery_fee_cents": fee_share,
            "total_cents": subtotal + fee_share
        })

    food_subtotal = sum(
        member["food_subtotal_cents"]
        for member in summary_members
    )

    return {
        "group_order_id": group["id"],
        "share_code": group["share_code"],
        "status": group["status"],
        "delivery_fee_cents": DELIVERY_FEE,
        "food_subtotal_cents": food_subtotal,
        "grand_total_cents": food_subtotal + DELIVERY_FEE,
        "members": summary_members
    }