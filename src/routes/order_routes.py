from fastapi import APIRouter, status
from src.services.order_services import get_order
from src.models import OrderCreate, OrderStatusUpdate
from src.services.order_services import (create_order, change_order_status)
router = APIRouter()

@router.get("/orders/{order_id}")
def retrieve_order(order_id: int):
    return get_order(order_id)

@router.post("/orders", status_code=status.HTTP_201_CREATED)
def place_order(request: OrderCreate):
    return create_order(request)

@router.patch("/orders/{order_id}/status")
def change_status(order_id: int, request: OrderStatusUpdate):
    return change_order_status(
        order_id=order_id,
        new_status=request.status
    )