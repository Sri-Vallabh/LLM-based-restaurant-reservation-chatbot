import sqlite3

def reset_reservations():
    sql_statements = [
        "UPDATE slots SET is_reserved = 0;",
        "DELETE FROM reservation_tables;",
        "DELETE FROM reservations;"
    ]

    try:
        conn = sqlite3.connect("restaurant_reservation.db")
        cursor = conn.cursor()

        cursor.execute("BEGIN TRANSACTION;")
        for stmt in sql_statements:
            cursor.execute(stmt)
        conn.commit()
        conn.close()
        return "✅ All slots marked as reserved and reservations cleared."
    except Exception as e:
        conn.rollback()
        conn.close()
        return f"❌ Error during reset: {e}"

# Call this function
result = reset_reservations()
print(result)
