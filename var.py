import chromadb
import sqlite3
import hashlib
import pandas as pd
from sentence_transformers import SentenceTransformer 
#--- Initialize ChromaDB and SentenceTransformer ---
SCHEMA_DESCRIPTIONS = {
    "restaurants": """Table restaurants contains restaurant details:
    - id: unique identifier
    - name: restaurant name
    - cuisine: type of cuisine
    - location: area or neighborhood
    - seating_capacity: total seats
    - rating: average rating
    - address: full address
    - contact: phone or email
    - price_range: price category
    - special_features: amenities or highlights""",
    "tables": """Table tables contains table details:
    - id: unique identifier
    - restaurant_id: links to restaurants.id
    - capacity: number of seats (default 4)""",
    "slots": """Table slots contains reservation time slots:
    - id: unique identifier
    - table_id: links to tables.id
    - date: reservation date
    - hour: reservation hour
    - is_reserved: 0=available, 1=booked"""
}
class SchemaVectorDB:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection("schema")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        for idx, (name, desc) in enumerate(SCHEMA_DESCRIPTIONS.items()):
            self.collection.add(ids=str(idx), documents=desc, metadatas={"name": name})

    def get_relevant_schema(self, query, k=2):
        query_embedding = self.model.encode(query).tolist()
        results = self.collection.query(query_embeddings=[query_embedding], n_results=k)
        # results['metadatas'] is a list of lists: [[{...}, {...}], ...]
        # We only have one query, so grab the first list
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        return [m['name'] for m in metadatas if m and 'name' in m]






class FullVectorDB:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="db/chroma")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get existing collections or create if not exist
        self.restaurants_col = self.client.get_or_create_collection("restaurants")
        self.tables_col = self.client.get_or_create_collection("tables")
        self.slots_col = self.client.get_or_create_collection("slots")
        
        # Initialize only if collections are empty
        if len(self.restaurants_col.get()['ids']) == 0:
            self._initialize_collections()

    def _row_to_text(self, row):
        return ' '.join(str(v) for v in row.values if pd.notnull(v))

    def _row_hash(self, row):
        return hashlib.sha256(str(row.values).encode()).hexdigest()

    def _initialize_collections(self):
        conn = sqlite3.connect("db/restaurant_reservation.db")
        
        # Create external changelog table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chroma_changelog (
                id INTEGER PRIMARY KEY,
                table_name TEXT,
                record_id INTEGER,
                content_hash TEXT,
                UNIQUE(table_name, record_id)
            )
        """)
        conn.commit()

        # Process tables
        self._process_table(conn, "restaurants", self.restaurants_col)
        self._process_table(conn, "tables", self.tables_col)
        self._process_table(conn, "slots", self.slots_col)
        
        conn.close()

    def _process_table(self, conn, table_name, collection):
        # Get existing records from Chroma
        existing_ids = set(collection.get()['ids'])
        
        # Get all records from SQLite with hash
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        
        # Process each row
        for _, row in df.iterrows():
            chroma_id = f"{table_name}_{row['id']}"
            current_hash = self._row_hash(row)
            
            # Check if exists in changelog
            changelog = pd.read_sql(f"""
                SELECT content_hash 
                FROM chroma_changelog 
                WHERE table_name = ? AND record_id = ?
            """, conn, params=(table_name, row['id']))
            
            # Skip if hash matches
            if not changelog.empty and changelog.iloc[0]['content_hash'] == current_hash:
                continue
                
            # Generate embedding
            embedding = self.model.encode(self._row_to_text(row))
            
            # Update Chroma
            collection.upsert(
                ids=[chroma_id],
                embeddings=[embedding.tolist()],
                metadatas=[row.to_dict()]
            )
            
            # Update changelog
            conn.execute("""
                INSERT OR REPLACE INTO chroma_changelog 
                (table_name, record_id, content_hash)
                VALUES (?, ?, ?)
            """, (table_name, row['id'], current_hash))
            conn.commit()

    def semantic_search(self, query, collection_name, k=5):
        query_embedding = self.model.encode(query).tolist()
        collection = getattr(self, f"{collection_name}_col")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["metadatas"]
        )
        return results['metadatas'][0]
