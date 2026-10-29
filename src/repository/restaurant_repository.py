from src.repository.database import get_connection

def get_all_restaurants():
    connection = get_connection()
    try:
       cursor = connection.execute("SELECT * FROM restaurants")  # Select everything from SQL query.
       restaurants = [
           dict(row) for row in cursor.fetchall()
       ]
       return restaurants
    finally:
        connection.close()

def get_restaurant_menu(restaurant_id):
    connection = get_connection()
    try:
        cursor = connection.execute("SELECT id,name,price_cents FROM menu_items WHERE restaurant_id = ?", (restaurant_id,)) # Select all
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()

def restaurant_exists(restaurant_id): #Error Handling
    connection = get_connection()
    try:
        restuarant = connection.execute("SELECT id FROM restaurants WHERE id = ?", (restaurant_id,)).fetchone() #SQL query to find a restaurant by its ID.
        return restuarant is not None
    finally:
        connection.close()