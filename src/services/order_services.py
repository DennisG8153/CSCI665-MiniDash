from fastapi import HTTPException
from src.repository.order_repository import get_order_by_id
from datetime import datetime, timezone
from src.repository.order_repository import (create_normal_order,update_order_status)

def get_order(order_id: int):
    order = get_order_by_id(order_id)
    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )
    return order

def create_order(request):
    address = request.address.strip()
    if not address:
        raise HTTPException(422, "Delivery address cannot be empty")
    items = [
        {
            "menu_item_id": item.menu_item_id,
            "quantity": item.quantity
        }
        for item in request.items
    ]
    created_at = datetime.now(timezone.utc).isoformat()
    try:
        return create_normal_order(
            restaurant_id=request.restaurant_id,
            address=address,
            items=items,
            created_at=created_at
        )
    except ValueError as error:
        reason = str(error)
        if reason == "RESTAURANT_NOT_FOUND":
            raise HTTPException(404, "Restaurant not found")
        if reason == "INVALID_MENU_ITEM":
            raise HTTPException(
                422,
                "Menu item does not belong to this restaurant"
            )
        raise

def change_order_status(order_id: int, new_status: str):
    try:
        return update_order_status(order_id, new_status)
    except ValueError as error:
        if str(error) == "ORDER_NOT_FOUND":
            raise HTTPException(404, "Order not found")
        raise

