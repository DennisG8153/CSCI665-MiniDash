from fastapi import APIRouter
from src.services.restaurant_service import (list_restaurants, list_restaurant_menu)

router = APIRouter() # Router for the restaurant's endpoints.

@router.get("/restaurants")
def get_restaurants():
    return list_restaurants()

@router.get("/restaurants/{restaurant_id}/menu")
def get_menu(restaurant_id: int): # Validates if the restaurant_id is an integer.
    return list_restaurant_menu(restaurant_id)