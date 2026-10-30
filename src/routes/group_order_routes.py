from fastapi import APIRouter, status
from src.models import GroupOrderCreate
from src.services.group_order_service import create_group_order
router = APIRouter()
@router.post("/group-orders", status_code=status.HTTP_201_CREATED)
def create_group(request: GroupOrderCreate):
    return create_group_order(
        restaurant_id=request.restaurant_id,
        host_name=request.host_name
    )
