import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("restaurant_reservation.db")
cursor = conn.cursor()

# Create tables if they do not exist
cursor.executescript("""
CREATE TABLE IF NOT EXISTS restaurants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    cuisine TEXT,
    location TEXT,
    seating_capacity INTEGER,
    rating REAL,
    address TEXT,
    contact TEXT,
    price_range TEXT,
    special_features TEXT
);

CREATE TABLE IF NOT EXISTS tables (
    id TEXT PRIMARY KEY,
    restaurant_id TEXT,
    capacity INTEGER DEFAULT 4,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);

CREATE TABLE IF NOT EXISTS slots (
    id TEXT PRIMARY KEY,
    table_id TEXT,
    date TEXT,
    hour INTEGER,
    is_reserved INTEGER DEFAULT 0,
    FOREIGN KEY (table_id) REFERENCES tables(id)
);

CREATE TABLE IF NOT EXISTS reservations (
    id TEXT PRIMARY KEY,
    restaurant_id TEXT,
    user_name TEXT,
    contact TEXT,
    date TEXT,
    time INTEGER,
    party_size INTEGER,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);

CREATE TABLE IF NOT EXISTS reservation_tables (
    id TEXT PRIMARY KEY,
    reservation_id TEXT,
    table_id TEXT,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id),
    FOREIGN KEY (table_id) REFERENCES tables(id)
);
""")

# Commit the changes
conn.commit()

# Close the connection
conn.close()

print("Tables have been created successfully!")
