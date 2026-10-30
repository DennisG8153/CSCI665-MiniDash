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
        
        CREATE TABLE IF NOT EXISTS group_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id INTEGER NOT NULL,
        share_code TEXT UNIQUE NOT NULL,
        status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'LOCKED', 'CHECKED_OUT', 'EXPIRED')),
        created_at TEXT NOT NULL,
        last_activity_at TEXT NOT NULL,
        normal_order_id INTEGER UNIQUE,
        FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),
        FOREIGN KEY (normal_order_id) REFERENCES orders(id));

        CREATE TABLE IF NOT EXISTS group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_order_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        is_host INTEGER NOT NULL DEFAULT 0 CHECK (is_host IN (0,1)),
        credential_hash TEXT NOT NULL, 
        joined_at TEXT NOT NULL,
        FOREIGN KEY (group_order_id) REFERENCES group_orders(id)
        );

        CREATE UNIQUE INDEX IF NOT EXISTS one_host_per_group ON group_members(group_order_id) WHERE is_host = 1;

        CREATE TABLE IF NOT EXISTS group_order_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_order_id INTEGER NOT NULL,
        member_id INTEGER NOT NULL,
        menu_item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        FOREIGN KEY (group_order_id) REFERENCES group_orders(id),
        FOREIGN KEY (member_id) REFERENCES group_members(id),
        FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
        );
        """)
        connection.commit()
    finally:
        connection.close()