import uuid
import random
import sqlite3

# ---------------------------
# Data Classes
# ---------------------------
class Restaurant:
    def __init__(self, restaurant_id, name, cuisine, location, seating_capacity, rating, address, contact, price_range, special_features):
        self.restaurant_id = restaurant_id
        self.name = name
        self.cuisine = cuisine
        self.location = location
        self.seating_capacity = seating_capacity
        self.rating = rating
        self.address = address
        self.contact = contact
        self.price_range = price_range
        self.special_features = special_features
        self.tables = []

class Table:
    def __init__(self, table_id, restaurant_id, capacity=4):
        self.table_id = table_id
        self.restaurant_id = restaurant_id
        self.capacity = capacity

# ---------------------------
# Sample Data
# ---------------------------
restaurant_names = [
    "Bella Italia", "Spice Symphony", "Tokyo Ramen House", "Saffron Grill", "El Toro Loco",
    "Noodle Bar", "Le Petit Bistro", "Tandoori Nights", "Green Leaf Cafe", "Ocean Pearl",
    "Mama Mia Pizza", "The Dumpling Den", "Bangkok Express", "Curry Kingdom", "The Garden Table",
    "Skyline Dine", "Pasta Republic", "Street Tacos Co", "Miso Hungry", "Chez Marie"
]

locations = ['Downtown', 'Uptown', 'Midtown', 'Suburbs']
special_features_list = ['Outdoor Seating', 'Pet-Friendly', 'Live Music', 'Rooftop View', 'Private Dining']

def infer_cuisine(name):
    name = name.lower()
    if "italia" in name or "pasta" in name or "mama mia" in name:
        return "Italian"
    elif "tokyo" in name or "ramen" in name or "miso" in name:
        return "Japanese"
    elif "saffron" in name or "tandoori" in name or "curry" in name:
        return "Indian"
    elif "dumpling" in name or "noodle" in name:
        return "Chinese"
    elif "bistro" in name or "chez" in name or "marie" in name:
        return "French"
    elif "bangkok" in name:
        return "Thai"
    elif "el toro" in name or "tacos" in name:
        return "Mexican"
    elif "green" in name or "garden" in name:
        return random.choice(["Multi-Cuisine", "Healthy", "Fusion"])
    elif "skyline" in name or "ocean" in name:
        return random.choice(["Multi-Cuisine", "Seafood", "Fusion"])
    else:
        return random.choice(["Italian", "Mexican", "Indian", "Japanese", "Chinese", "Thai", "French", "Multi-Cuisine"])

# Create restaurant objects
restaurants = []

for i in range(20):
    rest_id = str(uuid.uuid4())
    name = restaurant_names[i]
    cuisine = infer_cuisine(name)
    if cuisine == "Multi-Cuisine":
        cuisine = random.sample(["Italian", "Chinese", "Indian", "Mexican", "French"], k=2)

    location = random.choice(locations)
    num_tables = random.randint(10, 20)
    seating_capacity = num_tables * 4
    rating = round(random.uniform(3.5, 5.0), 1)
    address = f"{100 + i} Main Street, {location}"
    contact = f"555-{1000 + i}"
    price_range = random.choice(['$', '$$', '$$$'])
    features = random.sample(special_features_list, k=2)

    restaurant = Restaurant(
        restaurant_id=rest_id,
        name=name,
        cuisine=cuisine,
        location=location,
        seating_capacity=seating_capacity,
        rating=rating,
        address=address,
        contact=contact,
        price_range=price_range,
        special_features=features
    )

    for _ in range(num_tables):
        table_id = str(uuid.uuid4())
        table = Table(table_id=table_id, restaurant_id=rest_id)
        restaurant.tables.append(table)

    restaurants.append(restaurant)

# ---------------------------
# Insert into SQLite Database
# ---------------------------
conn = sqlite3.connect("restaurant_reservation.db")
cursor = conn.cursor()

for r in restaurants:
    cuisine_str = ", ".join(r.cuisine) if isinstance(r.cuisine, list) else r.cuisine
    features_str = ", ".join(r.special_features)
    
    cursor.execute("""
        INSERT INTO restaurants (id, name, cuisine, location, seating_capacity, rating, address, contact, price_range, special_features)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        r.restaurant_id,
        r.name,
        cuisine_str,
        r.location,
        r.seating_capacity,
        r.rating,
        r.address,
        r.contact,
        r.price_range,
        features_str
    ))

    for t in r.tables:
        cursor.execute("""
            INSERT INTO tables (id, restaurant_id, capacity)
            VALUES (?, ?, ?)
        """, (
            t.table_id,
            t.restaurant_id,
            t.capacity
        ))

conn.commit()
conn.close()
print("✅ Restaurants and tables successfully added to the database.")
