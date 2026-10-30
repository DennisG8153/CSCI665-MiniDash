from fastapi import APIRouter, status, Header
from src.models import GroupOrderCreate,GroupJoinRequest, GroupItemAdd
from src.services.group_order_service import create_group_order, join_group_order, add_item_to_group, remove_item_from_group
from src.services.group_order_service import get_group_order_summary, lock_group
from src.models import GroupCheckoutRequest
from src.services.group_order_service import checkout_group

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

@router.delete("/group-orders/{share_code}/items/{item_id}")
def delete_item(share_code: str, item_id: int, member_credential: str = Header(alias = "X-Member-Credential")):
    return remove_item_from_group(
        share_code=share_code,
        credential=member_credential,
        item_id=item_id
    )

@router.get("/group-orders/{share_code}/summary")
def group_summary(share_code: str):
    return get_group_order_summary(share_code)

@router.post("/group-orders/{share_code}/lock")
def lock_group_endpoint(
    share_code: str,
    host_credential: str = Header(
        alias="X-Member-Credential"
    )
):
    return lock_group(
        share_code=share_code,
        credential=host_credential
    )

@router.post("/group-orders/{share_code}/checkout")
def checkout_group_endpoint(
    share_code: str,
    request: GroupCheckoutRequest,
    host_credential: str = Header(
        alias="X-Member-Credential"
    )
):
    return checkout_group(
        share_code=share_code,
        credential=host_credential,
        address=request.address
    )