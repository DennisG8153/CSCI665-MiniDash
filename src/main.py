from fastapi import FastAPI
from src.routes.restaurant_routes import router as restaurant_router # Importing the restaurant router.
from src.routes.group_order_routes import router as group_order_router # Importing group order router.
from src.routes.order_routes import router as order_router # Importing regular ordering router.

app = FastAPI(title = "MiniDash API", description = "CSCI 665 Fall 2026 Project for DGrigory - 1307769")
app.include_router(restaurant_router) # Including main restaurant router for the application.
app.include_router(group_order_router)
app.include_router(order_router)
@app.get("/")
def home():
    return {"message": "Welcome to MiniDash!"} # Return welcome message for root endpoint.
