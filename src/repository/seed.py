from src.repository.database import get_connection # Importing function to create database tables.

def seed_restaurants():
    connection = get_connection() # Getting connection to the database.
    restaurants = [
        ("Pizza Palace", "Italian", "10:00", "22:00", 25),
        ("Bob's Daughter", "American", "12:00", "23:00", 20),
        ("Nozu", "Japanese", "11:00", "21:00", 30),
        ("Taco Bell", "Mexican", "08:00", "23:00", 15),
        ("Courier Curry", "Indian", "10:00", "22:00", 35)
    ]

    try: # Prevent dulipcation when seeding again
        existing = connection.execute("SELECT COUNT(*) FROM restaurants").fetchone()[0] # Checks if the restaurant record already exists. 
        if existing == 0:
            connection.executemany( # Using executemany to insert multiple rows at once. ? are placeholder values into our SQL statement.
                """INSERT INTO restaurants (name, cuisine, opens_at, closes_at, avg_prep_minutes) VALUES (?,?,?,?,?)""", restaurants
            )
            connection.commit() # If the resaturants don't exist, add them to the database with the seed information.
            print("Five restaurants added successfully!")
        else:
            print("Restaurants already exist, skipping seeding process.")
    finally:
        connection.close() # Closing the connection to the database.

def seed_menu_items():
    connection = get_connection()
    menu_items = [ # We are adding 3 options per restaurant. Each item: restaurant_id, item name, and price in USD.
        (1, "Cheese Pizza", 1099),
        (1, "Pepperoni Pizza", 1499),
        (1, "Margherita Pizza", 1299),
        (2, "Classic Burger", 899),
        (2, "Cheeseburger", 999),
        (2, "French Fries", 499), # Adjusted for inflation prices.
        (3, "California Roll", 599),
        (3, "Salmon Nigiri", 699),
        (3, "Dragon Roll", 1299),
        (4, "Chicken Taco", 399),
        (4, "Beef Taco", 499),
        (4, "Chips & Salsa", 399), # Again, adjusted for inflation.
        (5, "Chicken Curry", 1599),
        (5, "Lamb over Rice", 1899),
        (5, "Garlic Naan", 499)
    ]
    try: # Prevent duplication of menu items
        existing = connection.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0]
        if existing == 0: #If no menu items exist, insert seed data.
            connection.executemany(
                """INSERT INTO menu_items (restaurant_id, name, price_cents) VALUES (?,?,?)""", menu_items
            )
            connection.commit() #Commit if the items did not originally exist for the resturants.
            print("Menu items added successfully!")
        else:
            print("Menu items already exist, skipping process.")
    finally:
        connection.close()
    