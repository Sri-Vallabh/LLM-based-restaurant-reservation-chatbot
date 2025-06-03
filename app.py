import streamlit as st
from openai import OpenAI
import sqlite3
import pandas as pd
import re
import json
from sticky import sticky_container
import chromadb
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import hashlib
import inspect
from tools import *
from var import SCHEMA_DESCRIPTIONS, SchemaVectorDB, FullVectorDB


# Set your Groq API key
GROQ_API_KEY = "Your API Key Here"

# Initialize Groq's OpenAI-compatible client
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# --- Load prompt templates from prompts folder ---
with open("prompts/determine_intent.txt", "r", encoding="utf-8") as f:
    determine_intent_prompt = f.read()

with open("prompts/generate_reservation_conversation.txt", "r", encoding="utf-8") as f:
    generate_reservation_conversation_prompt = f.read()

with open("prompts/interpret_sql_result.txt", "r", encoding="utf-8") as f:
    interpret_sql_result_prompt = f.read()

with open("prompts/schema_prompt.txt", "r", encoding="utf-8") as f:
    schema_prompt = f.read()

with open("prompts/store_user_info.txt", "r", encoding="utf-8") as f:
    store_user_info_prompt = f.read()



st.set_page_config(page_title="FoodieSpot Assistant", layout="wide")


# --- Initialize State ---
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'user_data' not in st.session_state:
    st.session_state.user_data = {
        "restaurant_name": None,
        "user_name": None,
        "contact": None,
        "party_size": None,
        "time": None
    }
if 'vector_db' not in st.session_state:
    st.session_state.vector_db = SchemaVectorDB()
vector_db = st.session_state.vector_db
if 'full_vector_db' not in st.session_state:
    st.session_state.full_vector_db = FullVectorDB()
# Track last assistant reply for context
if 'last_assistant_reply' not in st.session_state:
    st.session_state.last_assistant_reply = ""
# Fixed container at top for title + reservation
reservation_box = sticky_container(mode="top", border=False,z=999)

with reservation_box:
    st.text("")
    st.text("")
    st.title("🍽️ FoodieSpot Assistant")
    cols = st.columns([3, 3, 3, 2, 2, 1])

    with cols[0]:
        restaurant_name = st.text_input(
            "Restaurant Name",
            value=st.session_state.user_data.get("restaurant_name") or "",
            key="restaurant_name_input"
        )
        if restaurant_name!="":
            st.session_state.user_data["restaurant_name"] = restaurant_name

    with cols[1]:
        user_name = st.text_input(
            "Your Name",
            value=st.session_state.user_data.get("user_name") or "",
            key="user_name_input"
        )
        if user_name!="":
            st.session_state.user_data["user_name"] = user_name

    with cols[2]:
        contact = st.text_input(
            "Contact",
            value=st.session_state.user_data.get("contact") or "",
            key="contact_input"
        )
        if contact!="":
            st.session_state.user_data["contact"] = contact

    with cols[3]:
        party_size = st.number_input(
            "Party Size",
            value=st.session_state.user_data.get("party_size") or 0,
            key="party_size_input"
        )
        if party_size!=0:
            st.session_state.user_data["party_size"] = party_size

    with cols[4]:
        time = st.number_input(
            "Time(24hr form, 9-20, 8 ~ null)",
            min_value=8,
            max_value=20,
            value=st.session_state.user_data.get("time") or 8,
            key="time_input"
        )
        if time!=8:
            st.session_state.user_data["time"] = time
        # Place the BOOK button in the last column
    with cols[5]:
        st.text("")
        st.text("")
        book_clicked = st.button("BOOK", type="primary")
        # Add a green BOOK button (primary style)
    # book_clicked = st.button("BOOK", type="primary")

    if book_clicked:
        # Check if all required fields are filled
        required_keys = ["restaurant_name", "user_name", "contact", "party_size", "time"]
        if all(st.session_state.user_data.get(k) not in [None, "", 0, 8] for k in required_keys):
            booking_conn = None
            try:
                user_data = st.session_state.user_data
                party_size = int(user_data["party_size"])
                tables_needed = -(-party_size // 4)

                booking_conn = sqlite3.connect("db/restaurant_reservation.db")
                booking_cursor = booking_conn.cursor()

                booking_cursor.execute("SELECT id FROM restaurants WHERE LOWER(name) = LOWER(?)", (user_data["restaurant_name"],))
                restaurant_row = booking_cursor.fetchone()
                if not restaurant_row:
                    raise Exception("Restaurant not found.")
                restaurant_id = restaurant_row[0]

                booking_cursor.execute("""
                    SELECT t.id AS table_id, s.id AS slot_id
                    FROM tables t
                    JOIN slots s ON t.id = s.table_id
                    WHERE t.restaurant_id = ?
                    AND s.hour = ?
                    AND s.date = '2025-05-12'
                    AND s.is_reserved = 0
                    LIMIT ?
                """, (restaurant_id, user_data["time"], tables_needed))
                available = booking_cursor.fetchall()

                if len(available) < tables_needed:
                    raise Exception("Not enough available tables.")

                booking_cursor.execute("""
                    INSERT INTO reservations (restaurant_id, user_name, contact, date, time, party_size)
                    VALUES (?, ?, ?, '2025-05-12', ?, ?)
                """, (restaurant_id, user_data["user_name"], user_data["contact"], user_data["time"], party_size))
                reservation_id = booking_cursor.lastrowid

                for table_id, _ in available:
                    booking_cursor.execute("INSERT INTO reservation_tables (reservation_id, table_id) VALUES (?, ?)", (reservation_id, table_id))

                slot_ids = [slot_id for _, slot_id in available]
                booking_cursor.executemany("UPDATE slots SET is_reserved = 1 WHERE id = ?", [(sid,) for sid in slot_ids])

                booking_conn.commit()

                booking_cursor.execute("SELECT name FROM restaurants WHERE id = ?", (restaurant_id,))
                restaurant_name = booking_cursor.fetchone()[0]

                confirmation_msg = (
                    f"✅ Booking processed successfully!\n\n"
                    f"📍 Restaurant: **{restaurant_name}**\n"
                    f"⏰ Time: **{user_data['time']} on 2025-05-12**\n"
                    f"🍽️ Tables Booked: **{tables_needed}**\n"
                    f"🆔 Reservation ID: **{reservation_id}**\n\n"
                    f"👉 Please mention this Reservation ID at the restaurant reception when you arrive."
                )

                st.success(confirmation_msg)
                st.session_state.chat_history.append({'role': 'assistant', 'message': confirmation_msg})
                st.session_state.user_data["restaurant_name"] = None
                st.session_state.user_data["party_size"] = None
                st.session_state.user_data["time"] = None
                st.session_state.last_assistant_reply = ""
            except Exception as e:
                if booking_conn:
                    booking_conn.rollback()
                st.error(f"❌ Booking failed: {e}")
            finally:
                if booking_conn:
                    booking_cursor = None
                    booking_conn.close()
        else:
            st.warning("⚠️ Missing user information. Please provide all booking details first.")
    st.text("")
   # Inject custom CSS for smaller font and tighter layout
    st.markdown("""
        <style>
        .element-container:has(.streamlit-expander) {
            margin-bottom: 0.5rem;
        }
        .streamlit-expanderHeader {
            font-size: 0.9rem;
        }
        .streamlit-expanderContent {
            font-size: 0.85rem;
            padding: 0.5rem 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns(3)

        with col1:
            with st.expander("🍽️ Restaurants"):
                st.markdown("""
                - Bella Italia  
                - Spice Symphony  
                - Tokyo Ramen House  
                - Saffron Grill  
                - El Toro Loco  
                - Noodle Bar  
                - Le Petit Bistro  
                - Tandoori Nights  
                - Green Leaf Cafe  
                - Ocean Pearl  
                - Mama Mia Pizza  
                - The Dumpling Den  
                - Bangkok Express  
                - Curry Kingdom  
                - The Garden Table  
                - Skyline Dine  
                - Pasta Republic  
                - Street Tacos Co  
                - Miso Hungry  
                - Chez Marie
                """)

        with col2:
            with st.expander("🌎 Cuisines"):
                st.markdown("""
                - Italian  
                - French  
                - Chinese  
                - Japanese  
                - Indian  
                - Mexican  
                - Thai  
                - Healthy  
                - Fusion
                """)

        with col3:
            with st.expander("✨ Special Features"):
                st.markdown("""
                - Pet-Friendly  
                - Live Music  
                - Rooftop View  
                - Outdoor Seating  
                - Private Dining
                """)




# --- Display previous chat history (before new input) ---

for msg in st.session_state.chat_history:
    # Check if both 'role' and 'message' are not None
    if msg['role'] is not None and msg['message'] is not None:
        with st.chat_message(msg['role']):
            st.markdown(msg['message'])

user_input = st.chat_input("Ask something about restaurants or reservations(eg. Tell me some best rated Italian cuisine restaurants)...")
if user_input:
    # Show user message instantly
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append({'role': 'user', 'message': user_input})

    # Prepare conversation context
    history_prompt = st.session_state.last_assistant_reply

     # Store possible user info
    user_info = store_user_info(user_input,history_prompt,store_user_info_prompt,client)
    st.session_state.user_data.update(user_info)
    # st.rerun()

    # Detect intent
    intent = determine_intent(user_input,determine_intent_prompt,client)
    # st.write(intent)
    if intent == "RUBBISH":
        # Display user data for confirmation instead of invoking LLM
        with st.chat_message("assistant"):
            st.markdown("❌ Sorry, I didn't understand that. Could you rephrase your request?")
        st.session_state.chat_history.append({
            'role': 'assistant',
            'message': "❌ Sorry, I didn't understand that. Could you rephrase your request?"
        })
       
        st.stop()

        # Generate assistant reply
    required_keys = ["restaurant_name", "user_name", "contact", "party_size", "time"]
    user_data_complete = all(
    k in st.session_state.user_data and st.session_state.user_data[k] not in [None, "", "NULL"]
    for k in required_keys
)


    if user_data_complete and intent != "BOOK":
       
        # Format user data as a Markdown bullet list
        user_details = "\n".join([f"- **{key.capitalize()}**: {value}" for key, value in st.session_state.user_data.items()])
        
        with st.chat_message("assistant"):
            st.markdown("✅ I have all the details needed for your reservation:")
            st.markdown(user_details)
            st.markdown("If everything looks good, please type **`book`** to confirm the reservation.")
        
        st.session_state.chat_history.append({
            'role': 'assistant',
            'message': f"✅ I have all the details needed for your reservation:\n{user_details}\nPlease type **`book`** to confirm."
        })
        st.session_state.last_assistant_reply = "I have all the reservation details. Waiting for confirmation..."
        st.rerun()
        st.stop()

    
   

    response_summary = None
       
    if intent == "SELECT":
        response_summary=handle_query(user_input, st.session_state.full_vector_db, client)
        
        # First try semantic search
        semantic_results = {}
        
        # Search across all collections
        restaurant_results = st.session_state.full_vector_db.semantic_search(user_input, "restaurants")
        table_results = st.session_state.full_vector_db.semantic_search(user_input, "tables")
        slot_results = st.session_state.full_vector_db.semantic_search(user_input, "slots")
        
        if not is_large_output_request(user_input) and any([restaurant_results, table_results, slot_results]):
            semantic_results = {
                "restaurants": restaurant_results,
                "tables": table_results,
                "slots": slot_results
            }
            # Format semantic results
            summary = []
            for category, items in semantic_results.items():
                if items:
                    summary.append(f"Found {len(items)} relevant {category}:")
                    summary.extend([f"- {item['name']}" if 'name' in item else f"- {item}" 
                                for item in items[:3]])
            st.write("### Semantic Search used")
            response_summary = "\n".join(summary)
        else:
            # Fall back to SQL generation for large or exact output requests
            sql = generate_sql_query_v2(user_input,SCHEMA_DESCRIPTIONS, history_prompt, vector_db, client)
            result = execute_query(sql)
            response_summary = interpret_result_v2(result, user_input, sql)

            
    
        # sql = generate_sql_query_v2(user_input,history_prompt, vector_db, client)
        # result = execute_query(sql)
        # response_summary=interpret_result_v2(result, user_input, sql)
        # if isinstance(result, pd.DataFrame):
        #     response_summary = interpret_sql_result(user_input, sql_query, result)

    
    elif intent == "BOOK":
        required_keys = ["restaurant_name", "user_name", "contact", "party_size", "time"]
        if all(st.session_state.user_data.get(k) is not None for k in required_keys):
            booking_conn = None
            try:
                user_data = st.session_state.user_data
                party_size = int(user_data["party_size"])
                tables_needed = -(-party_size // 4)

                booking_conn = sqlite3.connect("db/restaurant_reservation.db")
                booking_cursor = booking_conn.cursor()

                booking_cursor.execute("SELECT id FROM restaurants WHERE LOWER(name) = LOWER(?)", (user_data["restaurant_name"],))
                restaurant_row = booking_cursor.fetchone()
                if not restaurant_row:
                    raise Exception("Restaurant not found.")
                restaurant_id = restaurant_row[0]

                booking_cursor.execute("""
                    SELECT t.id AS table_id, s.id AS slot_id
                    FROM tables t
                    JOIN slots s ON t.id = s.table_id
                    WHERE t.restaurant_id = ?
                    AND s.hour = ?
                    AND s.date = '2025-05-12'
                    AND s.is_reserved = 0
                    LIMIT ?
                """, (restaurant_id, user_data["time"], tables_needed))
                available = booking_cursor.fetchall()
                # Debugging output
                
                if len(available) < tables_needed:
                    raise Exception("Not enough available tables.")

                booking_cursor.execute("""
                    INSERT INTO reservations (restaurant_id, user_name, contact, date, time, party_size)
                    VALUES (?, ?, ?, '2025-05-12', ?, ?)
                """, (restaurant_id, user_data["user_name"], user_data["contact"], user_data["time"], party_size))
                reservation_id = booking_cursor.lastrowid

                for table_id, _ in available:
                    booking_cursor.execute("INSERT INTO reservation_tables (reservation_id, table_id) VALUES (?, ?)", (reservation_id, table_id))

                slot_ids = [slot_id for _, slot_id in available]
                booking_cursor.executemany("UPDATE slots SET is_reserved = 1 WHERE id = ?", [(sid,) for sid in slot_ids])

                booking_conn.commit()
                # Fetch the restaurant name to confirm
                booking_cursor.execute("SELECT name FROM restaurants WHERE id = ?", (restaurant_id,))
                restaurant_name = booking_cursor.fetchone()[0]

                # Prepare confirmation details
                confirmation_msg = (
                    f"✅ Booking processed successfully!\n\n"
                    f"📍 Restaurant: **{restaurant_name}**\n"
                    f"⏰ Time: **{user_data['time']} on 2025-05-12**\n"
                    f"🍽️ Tables Booked: **{tables_needed}**\n"
                    f"🆔 Reservation ID: **{reservation_id}**\n\n"
                    f"👉 Please mention this Reservation ID at the restaurant reception when you arrive."
                )

                response_summary = confirmation_msg
                st.success(response_summary)
                st.session_state.chat_history.append({'role': 'assistant', 'message': response_summary})
                response_summary="✅ Booking processed successfully."
                st.session_state.user_data["restaurant_name"]=None
                st.session_state.user_data["party_size"]=None
                st.session_state.user_data["time"]=None
                st.session_state.last_assistant_reply=""
            except Exception as e:
                if booking_conn:
                    booking_conn.rollback()
                response_summary = f"❌ Booking failed: {e}"
                st.error(response_summary)
            finally:
                if booking_conn:
                    booking_cursor=None
                    booking_conn.close()
        else:
            st.markdown("⚠️ Missing user information. Please provide all booking details first.")
            response_summary = "⚠️ Missing user information. Please provide all booking details first."


    elif intent == "GREET":
        response_summary = "👋 Hello! How can I help you with your restaurant reservation today?"

    elif intent == "RUBBISH":
        response_summary = "❌ Sorry, I didn't understand that. Could you rephrase your request?"

    # Generate assistant reply
    if response_summary!="✅ Booking processed successfully.":
        follow_up = generate_reservation_conversation(
        user_input,
        history_prompt,
        response_summary or "Info stored.",
        json.dumps(st.session_state.user_data),generate_reservation_conversation_prompt,client
    )
    else:
        follow_up="Thanks for booking with FoodieSpot restaurant chain, I could assist you in new booking, also I could tell about restaurant features, pricing, etc... "

    # Show assistant reply instantly
    with st.chat_message("assistant"):
        st.markdown(follow_up)
    
    st.session_state.chat_history.append({'role': 'assistant', 'message': follow_up})
    # Update it after assistant speaks
    st.session_state.last_assistant_reply = follow_up
    st.rerun()
    # Reset if booking done
    

