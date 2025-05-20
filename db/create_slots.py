import sqlite3
import uuid
from datetime import datetime

# Connect to your SQLite DB
conn = sqlite3.connect("restaurant_reservation.db")
cursor = conn.cursor()

# Get all table IDs
cursor.execute("SELECT id FROM tables")
table_ids = [row[0] for row in cursor.fetchall()]

# Define the time range and current date
start_hour = 9  # 9AM
end_hour = 21   # 9PM

# Prepare slot entries
slot_entries = []
for table_id in table_ids:
    for hour in range(start_hour, end_hour):
        slot_id = str(uuid.uuid4())
        slot_entries.append((slot_id, table_id, "2025-05-12", hour, 0))  # is_reserved = 0

# Insert into slots table
cursor.executemany("""
    INSERT INTO slots (id, table_id, date, hour, is_reserved)
    VALUES (?, ?, ?, ?, ?)
""", slot_entries)

conn.commit()
conn.close()

print("✅ Slots successfully added for all tables for today.")
