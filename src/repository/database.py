import sqlite3
from pathlib import Path 

DB_PATH = Path(__file__).resolve().parents[2] / "minidash.db" 

def get_connection(): # Returning a connection object to the SQLite database.
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON") # Enabling foreign key support in SQLite.
    return connection
