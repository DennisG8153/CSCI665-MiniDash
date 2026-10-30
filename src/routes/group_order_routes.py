from fastapi import APIRouter, status, Header
from src.models import GroupOrderCreate,GroupJoinRequest, GroupItemAdd
from src.services.group_order_service import create_group_order, join_group_order, add_item_to_group
router = APIRouter()
@router.post("/group-orders", status_code=status.HTTP_201_CREATED)
def create_group(request: GroupOrderCreate):
    return create_group_order(
        restaurant_id=request.restaurant_id,
        host_name=request.host_name
    )
@router.post("/group-orders/{share_code}/join", status_code=status.HTTP_201_CREATED)
def join_group(share_code: str, request: GroupJoinRequest):
    return join_group_order(
        share_code=share_code,
        name=request.name
    )
@router.post("/group-orders/{share_code}/items", status_code=status.HTTP_201_CREATED)
def add_item(share_code: str, request: GroupItemAdd, member_credential: str = Header(alias = "X-Member-Credential")):
    return add_item_to_group(
        share_code=share_code,
        credential=member_credential,
        menu_item_id=request.menu_item_id,
        quantity=request.quantity
    )