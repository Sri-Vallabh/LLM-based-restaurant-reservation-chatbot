import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("restaurant_reservation.db")
cursor = conn.cursor()

# Function to print table contents
def print_table_contents(table_name):
    print(f"Contents of the {table_name} table:")
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    print("\n")

# Print contents of all the tables
print_table_contents("restaurants")
print_table_contents("tables")
print_table_contents("slots")
print_table_contents("reservations")
print_table_contents("reservation_tables")

# Close the database connection
conn.close()
