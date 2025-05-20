import streamlit as st
from openai import OpenAI
import sqlite3
import pandas as pd
import re
import json
from ui_utils import st_fixed_container
from sticky import sticky_container
# Set your Groq API key
GROQ_API_KEY = "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"

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

# Function to query the SQLite database
def execute_query(sql_query):
    query_conn = None
    try:
        query_conn = sqlite3.connect("db/restaurant_reservation.db")
        cursor = query_conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        return f"❌ Error executing query: {e}"
    finally:
        if query_conn:
            query_conn.close()

    
def execute_transaction(sql_statements):
    txn_conn = None
    try:
        txn_conn = sqlite3.connect("db/restaurant_reservation.db")
        cursor = txn_conn.cursor()
        for stmt in sql_statements:
            cursor.execute(stmt)
        txn_conn.commit()
        return "✅ Booking Executed"
    except Exception as e:
        if txn_conn:
            txn_conn.rollback()
        return f"❌ Booking failed: {e}"
    finally:
        if txn_conn:
            txn_conn.close()


    
def interpret_sql_result(user_query, sql_query, result):
    if isinstance(result, pd.DataFrame):
        # Convert DataFrame to list of dicts
        result_dict = result.to_dict(orient="records")
    else:
        # Fall back to raw string if not a DataFrame
        result_dict = result

    prompt = interpret_sql_result_prompt.format(
        user_query=user_query,
        sql_query=sql_query,
        result_str=json.dumps(result_dict, indent=2)  # Pass as formatted JSON string
    )

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You summarize database query results for a restaurant reservation assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()
def generate_reservation_conversation(user_query, history_prompt, sql_summary, user_data):
    words = history_prompt.split() if history_prompt else []
    if len(words) > 25:
        history_prompt_snippet = " ".join(words[:15]) + " ... " + " ".join(words[-10:])
    else:
        history_prompt_snippet = " ".join(words)

    # Serialize user_data as pretty JSON for readability in prompt
    user_data_json = json.dumps(user_data, indent=2)

    prompt = generate_reservation_conversation_prompt.format(
        user_query=user_query,
        user_data=user_data_json,
        sql_summary=sql_summary,
        history_prompt_snippet=history_prompt_snippet
    )

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful restaurant reservation assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )

    if not response.choices:
        return "Sorry, I couldn't generate a response right now."

    return response.choices[0].message.content.strip()

 
# --- Helper Functions ---

def determine_intent(user_input):
    prompt = determine_intent_prompt.format(user_input=user_input)
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "Classify user intent into SELECT, STORE, BOOK, GREET, or RUBBISH based on message content."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip().upper()



def store_user_info(user_input,history_prompt):
    words = history_prompt.split()
    if len(words) > 25:
        history_prompt_snippet = " ".join(words[:15]) + " ... " + " ".join(words[-10:])
    else:
        history_prompt_snippet = " ".join(words)
    previous_info = json.dumps(st.session_state.user_data)
    st.json(previous_info)
    prompt = store_user_info_prompt.format(previous_info=previous_info,user_input=user_input,history_prompt_snippet=history_prompt_snippet)
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "system", "content": "Extract or update user booking info in JSON."},
                  {"role": "user", "content": prompt}],
        temperature=0.3
    )


    try:
        # Print raw LLM output for inspection
        raw_output = response.choices[0].message.content
        # st.subheader("🧠 Raw LLM Response")
        # st.write(raw_output)

        # Extract JSON substring from anywhere in the response
        json_match = re.search(r'{[\s\S]*?}', raw_output)
        if not json_match:
            raise ValueError("No JSON object found in response.")

        json_str = json_match.group()

        # Show the extracted JSON string
        # st.subheader("📦 Extracted JSON String")
        # st.code(json_str, language="json")

        # Safely parse using json.loads
        parsed = json.loads(json_str)

        # Display the parsed result
        st.subheader("✅ Parsed JSON Object")
        st.json(parsed)

        return parsed

    except Exception as e:
        st.error(f"⚠️ Failed to parse JSON: {e}")
        return {}
    
def generate_sql_query(user_input,restaurant_name,party_size,time, history_prompt, schema_prompt, client):
    words = history_prompt.split()
    if len(words) > 25:
        history_prompt_snippet = " ".join(words[:15]) + " ... " + " ".join(words[-10:])
    else:
        history_prompt_snippet = " ".join(words)
    prompt = schema_prompt.format(
        history_prompt=history_prompt,
        user_input=user_input
    )

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that only returns SQL queries."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    raw_sql = response.choices[0].message.content.strip()
    extracted_sql = re.findall(r"(SELECT[\s\S]+?)(?:;|$)", raw_sql, re.IGNORECASE)
    sql_query = extracted_sql[0].strip() + ";" if extracted_sql else raw_sql
       
    return sql_query
def render_reservation_box():
    reservation_box = sticky_container(mode="top", border=False)

    with reservation_box:
        st.text("")
        st.text("")
        st.title("🍽️ FoodieSpot Assistant")
        st.markdown("### Reservation Details")
        cols = st.columns([3, 3, 3, 2, 2])

        with cols[0]:
            restaurant_name = st.text_input(
                "Restaurant Name",
                value=st.session_state.user_data.get("restaurant_name") or "",
                key="restaurant_name_input"
            )
            if restaurant_name != "":
                st.session_state.user_data["restaurant_name"] = restaurant_name

        with cols[1]:
            user_name = st.text_input(
                "Your Name",
                value=st.session_state.user_data.get("user_name") or "",
                key="user_name_input"
            )
            if user_name != "":
                st.session_state.user_data["user_name"] = user_name

        with cols[2]:
            contact = st.text_input(
                "Contact",
                value=st.session_state.user_data.get("contact") or "",
                key="contact_input"
            )
            if contact != "":
                st.session_state.user_data["contact"] = contact

        with cols[3]:
            party_size = st.number_input(
                "Party Size",
                value=st.session_state.user_data.get("party_size") or 0,
                key="party_size_input"
            )
            if party_size != 0:
                st.session_state.user_data["party_size"] = party_size

        with cols[4]:
            time = st.number_input(
                "Time(24hr form, 9-20, 8 ~ null)",
                min_value=8,
                max_value=20,
                value=st.session_state.user_data.get("time") or 8,
                key="time_input"
            )
            if time != 8:
                st.session_state.user_data["time"] = time


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
# Track last assistant reply for context
if 'last_assistant_reply' not in st.session_state:
    st.session_state.last_assistant_reply = ""
# Fixed container at top for title + reservation
reservation_box = sticky_container(mode="top", border=False,z=z_index)

with reservation_box:
    st.text("")
    st.text("")
    st.title("🍽️ FoodieSpot Assistant")
    st.markdown("### Reservation Details")
    cols = st.columns([3, 3, 3, 2, 2])

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
with st.container():
    st.markdown("### 📋 Available Restaurants and Features")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🍽️ Restaurants")
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
        st.markdown("#### 🌎 Cuisines")
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
        st.markdown("#### ✨ Special Features")
        st.markdown("""
        - Pet-Friendly  
        - Live Music  
        - Rooftop View  
        - Outdoor Seating  
        - Private Dining
        """)


# --- Display previous chat history (before new input) ---
for msg in st.session_state.chat_history:
    with st.chat_message(msg['role']):
        st.markdown(msg['message'])

user_input = st.chat_input("Ask something about restaurants or reservations(eg. Tell me some best rated Italian cuisine restaurants)...")
if user_input:
    st.write(user_input)
    # Show user message instantly
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append({'role': 'user', 'message': user_input})

    # Prepare conversation context
    history_prompt = st.session_state.last_assistant_reply

     # Store possible user info
    user_info = store_user_info(user_input,history_prompt)
    st.session_state.user_data.update(user_info)
    # st.rerun()

    # Detect intent
    intent = determine_intent(user_input)
    st.write(intent)
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
        # Display user data for confirmation instead of invoking LLM
        with st.chat_message("assistant"):
            st.markdown("✅ I have all the details needed for your reservation:")
            st.json(st.session_state.user_data)
            st.markdown("If everything looks good, please type **`book`** to confirm the reservation.")
        st.session_state.chat_history.append({
            'role': 'assistant',
            'message': "✅ I have all the details needed for your reservation. Please type **`book`** to confirm."
        })
        st.session_state.last_assistant_reply = "I have all the reservation details. Waiting for confirmation..."
        st.stop()
    
   

    response_summary = None

    if intent == "SELECT":
        user_data = st.session_state.user_data
        restaurant_name = user_data["restaurant_name"]
        party_size=user_data["party_size"]
        time=user_data['time']
        st.write(restaurant_name)
        sql_query=generate_sql_query(user_input,restaurant_name,party_size,time, history_prompt, schema_prompt, client)
        result = execute_query(sql_query)
        st.subheader("Generated SQL Query")
        st.code(sql_query, language='sql')

        # Display the result
        st.subheader("Query Result")

        if isinstance(result, pd.DataFrame):
            if result.empty:
                st.info("Query executed successfully, but returned no results.")
            else:
                st.dataframe(result)
        else:
            # Handle plain string or error
            st.text(result)
        if isinstance(result, pd.DataFrame):
            response_summary = interpret_sql_result(user_input, sql_query, result)
    
    elif intent == "BOOK":
        required_keys = ["restaurant_name", "user_name", "contact", "party_size", "time"]
        if all(k in st.session_state.user_data for k in required_keys):
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
        json.dumps(st.session_state.user_data)
    )
    else:
        follow_up="Thanks for booking with FoodieSpot restaurant chain, I could assist you in new booking, also I could tell about restaurant features, pricing, etc... "

    # Show assistant reply instantly
    with st.chat_message("assistant"):
        st.markdown(follow_up)
    
    st.session_state.chat_history.append({'role': 'assistant', 'message': follow_up})
    # Update it after assistant speaks
    st.session_state.last_assistant_reply = follow_up

    # Reset if booking done
    

