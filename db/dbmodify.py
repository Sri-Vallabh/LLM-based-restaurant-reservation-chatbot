# import sqlite3

# conn = sqlite3.connect("restaurant_reservation.db")
# cursor = conn.cursor()

# # Drop the existing empty tables
# cursor.execute("DROP TABLE IF EXISTS reservations;")
# cursor.execute("DROP TABLE IF EXISTS reservation_tables;")

# # Recreate the tables with AUTOINCREMENT for `id`
# cursor.execute("""
# CREATE TABLE reservations (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     restaurant_id TEXT,
#     user_name TEXT,
#     contact TEXT,
#     date TEXT,          -- Hard coded to 2025-05-12
#     time TEXT,
#     party_size INTEGER
# );
# """)

# cursor.execute("""
# CREATE TABLE reservation_tables (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     reservation_id TEXT,
#     table_id TEXT
# );
# """)

# conn.commit()
# conn.close()

# print("Tables recreated successfully with AUTOINCREMENT ids.")

import sqlite3

conn = sqlite3.connect("restaurant_reservation.db")
cursor = conn.cursor()

try:
    cursor.execute("""
        UPDATE restaurants
        SET name = 'Street Tacos Co'
        WHERE name = 'Street Tacos Co.';
    """)
    conn.commit()
    print("✅ Restaurant name updated successfully.")
except Exception as e:
    conn.rollback()
    print(f"❌ Update failed: {e}")
finally:
    conn.close()

