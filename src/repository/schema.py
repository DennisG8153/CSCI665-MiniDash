from src.repository.database import get_connection # Importing function to get connection to the database.

def create_tables(): 
    connection = get_connection() # Getting connection
    try: # Create tables if they do not exist
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS restaurants(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        cuisine TEXT NOT NULL, 
        opens_at TEXT NOT NULL,
        closes_at TEXT NOT NULL,
        avg_prep_minutes INTEGER NOT NULL);
        
        CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        price_cents INTEGER NOT NULL,
        FOREIGN KEY (restaurant_id) REFERENCES restaurants(id));

        CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        total_cents INTEGER NOT NULL,
        address TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (restaurant_id) REFERENCES restaurants(id));

        CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        menu_item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (menu_item_id) REFERENCES menu_items(id));
        """)
        connection.commit()
    finally:
        connection.close()