from pydantic import BaseModel, Field

class OrderItemCreate(BaseModel): # Base model for ordering something.
    menu_item_id: int = Field(gt=0) # The ID of the menu item has to be greater than 0 to be a valid order.
    quantity: int = Field(gt=0) # The amount of items also has to be greater than 0 to be considered an order.

class OrderCreate(BaseModel): 
    restaurant_id: int = Field(gt=0) # Restaurant ID > 0 for a restaurant to exist.
    items: list[OrderItemCreate] = Field(min_length =1) # There has to be at least 1 item in an order.
    address: str = Field(min_length= 1) # Delivery address must be at least 1 character long.