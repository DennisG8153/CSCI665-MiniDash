from src.repository.restaurant_repository import (get_all_restaurants, get_restaurant_menu, restaurant_exists)
from fastapi import HTTPException # Importing HTTPExceptions for error handling.

def list_restaurants():
    return get_all_restaurants() # Return a list of all restaurants from the repository.

def list_restaurant_menu(restaurant_id):
    if not restaurant_exists(restaurant_id):
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return get_restaurant_menu(restaurant_id)