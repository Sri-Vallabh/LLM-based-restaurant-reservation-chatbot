import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("restaurant_reservation.db")
cursor = conn.cursor()

# Execute the query
cursor.execute("SELECT name FROM restaurants;")
restaurant_names = cursor.fetchall()

# Format and print the names side by side
names_list = [name[0] for name in restaurant_names]
print("📋 Restaurant Names:", ", ".join(names_list))

# Close the connection
conn.close()
