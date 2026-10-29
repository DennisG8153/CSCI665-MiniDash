from fastapi.testclient import TestClient 
from src.main import app # This is for testing purposes.

client = TestClient(app)
def test_list_restaurants():
    response = client.get("/restaurants")
    assert response.status_code == 200
    assert len(response.json()) == 5

def test_restaurant_menu(): 
    response = client.get("/restaurants/1/menu") # Testing with restaurant 1 AKA Pizza Palace.
    assert response.status_code == 200 # Ensure that the response status code is 200 OK to make sure the request succeeded.
    menu = response.json()
    assert len(menu) == 3
    assert menu[0]["name"] == "Cheese Pizza" # Assumes the first item is cheese pizza and checks if it is.
    assert menu[1]["name"] == "Pepperoni Pizza"
    assert menu[2]["name"] == "Margherita Pizza" # Tests the other two items.

def test_restaurant_not_found():
    response = client.get("/restaurants/999/menu") # Testing with a currently non-existent restaurant's menu.
    assert response.status_code == 404 # Expecting a 404 Error for something that doesn't exist.
    assert response.json()["detail"] == "Restaurant not found" # Expected message.