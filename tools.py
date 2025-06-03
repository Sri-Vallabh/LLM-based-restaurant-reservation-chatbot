import sqlite3
import inspect
import pandas as pd
import json
import re
import streamlit as st
def log_groq_token_usage(response, prompt=None, function_name=None, filename="efficiency_log.txt"):
    usage = response.usage
    log_message = (
        f"Function: {function_name or 'unknown'}\n"
        f"Prompt tokens: {usage.prompt_tokens}\n"
        f"Completion tokens: {usage.completion_tokens}\n"
        f"Total tokens: {usage.total_tokens}\n"
        f"Prompt: {prompt}\n"
        "---\n"
    )
    with open(filename, "a", encoding="utf-8") as f:  # ← THIS LINE
        f.write(log_message)

import pandas as pd
# --- Database Execution ---    
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


def execute_query(sql_query, db_path="db/restaurant_reservation.db"):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        return f"❌ Error executing query: {e}"
    finally:
        if conn:
            conn.close()
def generate_sql_query_v2(user_input,SCHEMA_DESCRIPTIONS,history_prompt, vector_db, client, use_cache=False):
    # Get relevant schema elements
    relevant_tables = vector_db.get_relevant_schema(user_input)
    schema_prompt = "\n".join([f"Table {table}:\n{SCHEMA_DESCRIPTIONS[table]}" for table in relevant_tables])
    # Cache check
    cache_key = f"query:{user_input[:50]}"
    if use_cache and (cached := cache.get(cache_key)):
        return cached.decode()
    # Generate SQL with Groq
    prompt = f"""Based on these tables:
{schema_prompt}
Previous assistant reply:
{history_prompt}
Convert this request to SQL: {user_input}

Only return the SQL query, nothing else."""
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that only returns SQL queries."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=200
    )
    log_groq_token_usage(response,prompt, function_name=inspect.currentframe().f_code.co_name)
    sql = response.choices[0].message.content.strip()
    if use_cache:
        cache.setex(cache_key, 3600, sql)
    return sql
def interpret_result_v2(result, user_query, sql_query,client):
    if isinstance(result, str):
        return result
    try:
        # Compress to essential columns if possible
        cols = [c for c in result.columns if c in ['name', 'cuisine', 'location', 'seating_capacity', 'rating', 'address', 'contact', 'price_range', 'special_features', 'capacity', 'date', 'hour']]
        if cols:
            compressed = result[cols]
        else:
            compressed = result
        json_data = compressed.to_json(orient='records', indent=2)
        # Summarize with Groq
        prompt = f"""User query: {user_query}
SQL query: {sql_query}
Result data (JSON): {json_data}

Summarize the results for the user."""
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Summarize database query results for a restaurant reservation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        log_groq_token_usage(response,prompt, function_name=inspect.currentframe().f_code.co_name)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error interpreting results: {e}"
    
def handle_query(user_input, vector_db, client):
    try:
        # First try semantic search
        semantic_results = {}
        
        # Search across all collections
        restaurant_results = vector_db.semantic_search(user_input, "restaurants")
        table_results = vector_db.semantic_search(user_input, "tables")
        slot_results = vector_db.semantic_search(user_input, "slots")
        
        if any([restaurant_results, table_results, slot_results]):
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
            
            return "\n".join(summary)
        else:
            # Fall back to SQL generation
            sql = generate_sql_query_v2(user_input, vector_db, client)
            result = execute_query(sql)
            return interpret_result_v2(result, user_input, sql,client)
            
    except Exception as e:
        return f"Error: {e}"


def is_large_output_request(query):
    query = query.lower()
    # List of single words and multi-word phrases (as lists)
    triggers = [
        ['all'], ['every'], ['entire'], ['complete'], ['full'], ['each'],
        ['list'], ['show'], ['display'], ['give', 'me'], ['get'],
        ['every', 'single'], ['each', 'and', 'every'],
        ['whole'], ['total'], ['collection'], ['set'],
        ['no', 'filters'], ['without', 'filters'],
        ['everything'], ['entirety'],
        ['comprehensive'], ['exhaustive'], ['record'],
        ['don\'t', 'filter'], ['without', 'limitations']
    ]
    query_words = query.split()
    for trigger in triggers:
        if all(word in query_words for word in trigger):
            return True
    return False


def generate_reservation_conversation(user_query, history_prompt, sql_summary, user_data,generate_reservation_conversation_prompt,client):
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
    log_groq_token_usage(response,prompt, function_name=inspect.currentframe().f_code.co_name)

    return response.choices[0].message.content.strip()

 
# --- Helper Functions ---

def determine_intent(user_input,determine_intent_prompt,client):
    prompt = determine_intent_prompt.format(user_input=user_input)
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "Classify user intent into SELECT, STORE, BOOK, GREET, or RUBBISH based on message content."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    log_groq_token_usage(response,prompt, function_name=inspect.currentframe().f_code.co_name)
    return response.choices[0].message.content.strip().upper()



def store_user_info(user_input,history_prompt,store_user_info_prompt, client):
    # words = history_prompt.split()
    # if len(words) > 25:
    #     history_prompt_snippet = " ".join(words[:15]) + " ... " + " ".join(words[-10:])
    # else:
    #     history_prompt_snippet = " ".join(words)
    previous_info = json.dumps(st.session_state.user_data)
    # st.json(previous_info)
    prompt = store_user_info_prompt.format(previous_info=previous_info,user_input=user_input)
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "system", "content": "Extract or update user booking info in JSON."},
                  {"role": "user", "content": prompt}],
        temperature=0.3
    )
    log_groq_token_usage(response,prompt, function_name=inspect.currentframe().f_code.co_name)

    try:
        # Print raw LLM output for inspection
        raw_output = response.choices[0].message.content
        # st.subheader("🧠 Raw LLM Response")
        # st.write(raw_output)

        # Extract JSON substring from anywhere in the response
        json_match = re.search(r'{[\s\S]*?}', raw_output)
        if not json_match:
            return None
            # raise ValueError("No JSON object found in response.")

        json_str = json_match.group()

        # Show the extracted JSON string
        # st.subheader("📦 Extracted JSON String")
        # st.code(json_str, language="json")

        # Safely parse using json.loads
        parsed = json.loads(json_str)

        # Display the parsed result
        # st.subheader("✅ Parsed JSON Object")
        # st.json(parsed)

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
    log_groq_token_usage(response,prompt, function_name=inspect.currentframe().f_code.co_name)
    raw_sql = response.choices[0].message.content.strip()
    extracted_sql = re.findall(r"(SELECT[\s\S]+?)(?:;|$)", raw_sql, re.IGNORECASE)
    sql_query = extracted_sql[0].strip() + ";" if extracted_sql else raw_sql
       
    return sql_query
    
def interpret_sql_result(user_query, sql_query, result,interpret_sql_result_prompt, client):
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
    log_groq_token_usage(response,prompt, function_name=inspect.currentframe().f_code.co_name)
    return response.choices[0].message.content.strip()
