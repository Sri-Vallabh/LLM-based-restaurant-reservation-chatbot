

#  Restaurant Reservation Assistant – LLM + Streamlit App

## 🚀 Overview

This is a conversational restaurant reservation assistant built using **LLMs (llama3-8b-8192)**, **Streamlit**, and **SQLite**. The assistant interacts with users in natural language to help them book tables, answer restaurant queries, and manage reservation workflows.

---

## ⚙️ Setup Instructions

### 🛠️ Requirements

* Python 3.8+
* `streamlit`
* `pandas`
* `openai` (for LLM interface)
*  `sqlite3`


### 🧩 Installation

```bash
git clone https://github.com/Sri-Vallabh/LLM-based-restaurant-reservation-chatbot.git
cd restaurant-reservation-assistant
pip install -r requirements.txt
```

### 🔗 Running the App

```bash
streamlit run app.py
```

Ensure the `restaurant_reservation.db` is in the /db folder inside  the root directory. This contains all restaurant, table, slot, and reservation data.
---

## 🧠 Language Model


This project uses **Meta’s LLaMA 3 8B** language model (`llama3-8b-8192`) served via **Groq’s OpenAI-compatible API**, leveraging their ultra-fast **LPU (Language Processing Unit)** hardware for low-latency inference. The model is accessed using the `openai` Python library with a simple configuration that sets the base URL to Groq's endpoint.  The system employs a **RAG (Retrieval-Augmented Generation)**-like approach to extract relevant data from the reservation database, ensuring responses are grounded in real-time availability and user-specific details. It supports a context window of **8192 tokens**, allowing it to handle extended conversations, database results, and prompt history efficiently. It is used in a **modular, multi-step fashion** to handle different aspects of the reservation flow:

1. **Intent Detection**: Determines what the user wants to do—whether it's booking a table, checking availability, asking general questions, or greeting or even rubbish(handling edge cases).

2. **Information Extraction**: Parses free-form user input to extract structured fields like restaurant name, user name, contact info, party size, and reservation time.

3. **SQL Query Generation**: If the user asks about availability or restaurant details, the model generates precise `SELECT` queries based on the schema to fetch relevant data from the database.

4. **Result Interpretation**: Converts raw SQL result tables into human-readable summaries, ensuring the response is conversational and helpful.

5. **Multi-Turn Dialogue Management**: Maintains context across multiple messages, uses previous inputs and system memory to hold state, and builds a coherent and helpful conversation thread with the user.

Each of these tasks is handled through **specialized prompts**, improving modularity and reliability.

Note: Final reservation is not performed by the llm for security reasons, there is a separate logic module to do the final booking.


---
## 💬 Example User Journeys with Application Walkthrough


Below are screenshots showing the end-to-end flow of the restaurant reservation assistant in action:

---

### 🟢 Image 1: Landing Page  
![Opening](assets/opening_1.png)

The landing page welcomes users and prompts:  
**"Ask something about restaurants or reservations..."**  
This initiates a free-form, conversational interface for users to interact naturally.
Here, also names of restaurants, cuisines, special features can be seen, which also stays along with the conversation thread which is scrollable.
---

### 💬 Image 2: General Conversation  
![Step 1](assets/1.png)

The assistant engages in friendly conversation, understanding user intent like greetings, small talk, or queries about restaurants.

---

### 🔍 Image 3: Database Query + Interpretation  
![Step 2](assets/2.png)

The assistant takes a user query (e.g., " What are the available cuisines?"), generates an appropriate SQL query, executes it on the database, interprets the result, and returns a natural, conversational response.

---

### 🤝 Image 4 to 6: Information Gathering + Suggestions  
![Step 3](assets/3.png)  
![Step 4](assets/4.png)  
![Step 5](assets/5.png)

Through ongoing conversation, the assistant extracts necessary reservation information:  
- 🏨 Restaurant name  
- 🙋 User name  
- 📱 Contact  
- 👥 Party size  
- ⏰ Time

It continues to help the user by checking availability and making suggestions.

---

### ✅ Image 7: Ready for Booking Confirmation  
![Step 6](assets/6.png)

Once all required information is gathered, the assistant summarizes the reservation details and asks for user confirmation with a simple **`book`** command.

---

### 🧾 Image 8: Booking Confirmation  
![Step 7](assets/7.png)

Booking is processed successfully!

- Restaurant: **Pasta Republic**  
- Time: **20 on 2025-05-12**  
- Party size: **15**  
- Tables booked: **4** (4 tables are needed to accomodate 15 people as one table has 4 seating capacity)  
- Reservation ID: **#10** 
The system calculates the number of tables needed using `ceil(party_size / 4)`, verifies table availability, reserves the required slots, and finalizes the booking.

The assistant informs the user:


👉 Please mention this Reservation ID at the restaurant reception when you arrive.

This flow demonstrates a complete, intelligent reservation assistant that uses natural language processing, database querying, and interactive UX logic to help users make hassle-free bookings.


---
## Some other results:


![Some results](assets/some_results.png)
---
### If user enters random text:
![Some results](assets/rubbish.png)




# Database explanation
* **`restaurant_reservation.db`**:

  * This SQLite database contains the following tables:

    * **`restaurants`**:

      * Stores information about each restaurant, such as its **name**, **cuisine**, **location**, **seating capacity**, **rating**, **address**, **contact details**, **price range**, and **special features**.
      * The **`id`** field serves as a unique identifier for each restaurant.
      * **Important Note**: The **`id`** is used internally in the database and should not be exposed to the user.

    * **`tables`**:

      * Stores information about tables at each restaurant.
      * Each table is associated with a **`restaurant_id`**, linking it to a specific restaurant.
      * Each table has a **capacity** (default is 4), which indicates how many guests it can accommodate.
      * The **`id`** field uniquely identifies each table and should not be shared with the user.

    * **`slots`**:

      * Stores information about the availability of each table.
      * Each slot corresponds to a **1-hour** time block for a specific table on a particular day (e.g., a table might have slots available from **9AM to 9PM**).
      * **`is_reserved`** indicates whether the slot is booked (**1**) or available (**0**).
      * **`date`** is hardcoded to **2025-05-12**, and the **`hour`** field defines the start time for the reservation (ranging from **9** to **20**, representing 9AM to 8PM).
      * The **`slot.id`** and **`table_id`** are used to uniquely identify the slots and link them to the relevant tables.

    * **`reservations`**:

      * Stores reservation details made by the user, including:

        * **`restaurant_id`**: Links the reservation to a specific restaurant.
        * **`user_name`**: The name of the user who made the reservation.
        * **`contact`**: The contact details (e.g., phone number) of the user.
        * **`date`**: Hardcoded to **2025-05-12**, representing the reservation date.
        * **`time`**: The starting hour of the reservation, which matches a slot's **hour** field.
        * **`party_size`**: The number of people for whom the reservation is made.
      * The **`id`** is used to uniquely identify each reservation, but it is not exposed to the user.

    * **`reservation_tables`**:

      * A junction table that links reservations to tables.
      * Contains:

        * **`reservation_id`**: Links the reservation to the **`reservations`** table.
        * **`table_id`**: Links the reservation to the relevant **`tables`**.
      * This table helps associate a reservation with the actual tables that are booked for that reservation.


## 📄 Prompt Engineering Strategy

### ✨ Design Principles

1. **🔁 Separation of Concerns**
   For different purposes, I have engineered different prompts that are modular, making the assistant easier to debug, maintain, and enhance:

   * **Intent classification** (`determine_intent.txt`)
   * **Information extraction** (`store_user_info.txt`)
   * **SQL query generation** (`schema_prompt.txt`)
   * **SQL result interpretation** (`interpret_sql_result.txt`)
   * **Natural reply generation** (`generate_reservation_conversation.txt`)

2. **🧠 Context-Aware Memory Management**

   * Maintains `chat_history`, `user_data`, and `last_reply` using Streamlit session state.
   * Tracks conversation context across turns to avoid repetition, keep interactions natural, and gracefully handle incomplete data.

3. **✅ Controlled Confirmation Flow**

   * Prompts ensure that **only when all required fields (restaurant name, name, contact, party size, and time)** are filled, the assistant proceeds to ask for booking confirmation.
   * Prevents accidental bookings and ensures user consent before writing to the database.

4. **🛡️ Safe Query Execution**

   * Only **SELECT statements** generated by the LLM are allowed to be executed directly.
   * INSERT/UPDATE operations (like booking a reservation) are handled by a **separate, controlled module**, protecting the database from unintended writes or corruption.

5. **📦 Iterative Prompt Optimization**

   * Prompts have been fine-tuned through iterative experimentation and real conversation testing.
   * Incorporated **few-shot examples** where relevant to guide the LLM.
   * Prompts are designed to gracefully handle edge cases, e.g., when users give partial or ambiguous information.

6. **📏 Robust Format Enforcement & Cleaning**

   * JSON outputs (e.g., for `store_user_info`) include explicit instructions on quoting keys/values to prevent parsing issues.
   * Pre/post-processing logic strips any unexpected or extra text surrounding JSON responses from the LLM.
   * Regular expressions and cleaning checks are used to sanitize LLM responses before using them in downstream logic.

7. **🌐 User-Centric Design**

   * Prompts use natural, polite tone and context-aware replies, improving user trust and UX.
   * Conversational flow shifts fluidly between transactional (booking) and informational (restaurant FAQs) based on detected intent, also handling **multiple-intent** cases.

---


### ⚠️ Error Handling & Edge Cases

This assistant is designed to offer a smooth and reliable user experience, even in unexpected scenarios. The following mechanisms are implemented to handle errors and edge cases effectively:

#### ✅ Error Handling

* **LLM Output Sanitization**:
  When the LLM occasionally adds extra text before or after the expected response (e.g., in SQL queries), the output is parsed and cleaned using regex or string manipulation to extract only the required format. This ensures that unexpected formatting does not break the application.

* **Safe Execution with Try-Catch Blocks**:
  All critical operations — especially SQL queries and bookings — are wrapped in `try-except` blocks. This prevents the UI from crashing and allows the assistant to gracefully inform the user about what went wrong.

* **Pre-Booking Availability Recheck**:
  Just before finalizing a reservation, the system re-checks for table and slot availability. This is to prevent race conditions where multiple users might try to book the same slot at the same time — ensuring consistency and avoiding double bookings.

 * **Preventive measures for malicious data injection/Database modification by prompt**:
The LLM does not directly execute SQL INSERT statements. Instead, it only interprets user intent, and can perform certain select queries to gather information. There is a dedicated backend module securely handles data injection for reservations , reducing the risk of malicious injection or malformed queries.

---

#### 🔍 Edge Cases

* **Random or Nonsensical User Input**:
  If a user inputs irrelevant or nonsensical text (e.g., "asdf123", emojis, or spam), the assistant classifies it as an invalid intent (tagged as `RUBBISH`) and politely asks the user to rephrase or clarify their request.

* **Partial Reservation Information**:
  When users provide only some details (e.g., name but not time), the assistant remembers the known information and continues the conversation by asking only for the missing fields, without repeating previously collected data.

* **Privacy Protection**:
Users cannot ask about bookings made by others. The SQL data access layer enforces this by exposing only the current user’s booking context. There is no direct query access to personal or third-party reservation data.

* **Restaurant Not Found**:
  If the user provides a restaurant name that does not exist in the database, the assistant notifies them and may offer to show a list of available restaurants.

* **Unavailable Timeslots**:
  If the requested time has no available tables (due to existing reservations), the assistant explains this clearly and suggests choosing a different time.

---

By handling these cases gracefully, the assistant ensures that users have a seamless experience even when unexpected situations arise.






## 🧠 Business Strategy Summary

### 🔍 Problem

Restaurants often struggle with fragmented booking systems, no-shows, and poor conversational interfaces.

### 💡 Opportunity

* AI-powered assistants streamline booking while providing a human-like experience.
* Can answer FAQs, collect information passively, and integrate with POS or CRM systems.

### 📈 Success Metrics

* 💬 90%+ booking completion rate post-data collection
* 🧑‍💼 25% reduction in manual staff interventions
* 🔁 < 5% drop-off rate during multi-turn conversations

### 📊 ROI Potential

* Time saved per reservation = \~3 minutes
* For 100 daily bookings, savings = 5 hours/day
* Yearly FTE savings = \~\$15–30K per location

---

## 🧭 Assumptions, Limitations & Enhancements

### ✅ Assumptions

* All bookings are for a fixed date (`2025-05-12`) from 9AM to 9PM for testing simplicity

### ⚠️ Limitations

* No support for special requests (e.g., "window seat"), but suggests from existing features that are available

### 🔮 Future Enhancements

* ✅ Date picker and calendar integration
* 📲 SMS/WhatsApp confirmation with reservation ID
* 🧾 Admin dashboard to manage reservations & analytics
* 🌐 Multilingual support for non-English customers
* 🔌 API-first backend to support mobile and kiosk interfaces

---

## 📊 Vertical Expansion

This solution can be adapted for:

* ✈️ Airlines (seat booking assistants)
* 🏥 Clinics & Hospitals (appointment schedulers)
* 🎟️ Event Ticketing Systems (concerts, sports, etc.)
* 🏨 Hotels (room booking, amenities)

---

## 🥇 Competitive Advantages

1. 🔁 Multi-turn conversation memory (session-state-based and intent based)
2. 🧠 Contextual intent handling with seamless switching between FAQ and transactional flows
3. 📦 Modular LLM prompt architecture for future scaling
4. 🔒 Secure and Controlled SQL Access
Only read-only SQL (SELECT) statements are generated and executed via the LLM to prevent any risk of data corruption.
Reservation actions like INSERT or UPDATE are handled securely in a separate logic module, ensuring strict control over data modification.

---

## 📅 Implementation Timeline

| Phase   | Description                            | Duration |
| ------- | -------------------------------------- | -------- |
| Phase 1 | Database creation+LLM sql query creation and interpretation              | 1st day   |
| Phase 2 | Intent detection+conversational flow | 1st day  |
| Phase 3 | Booking and edge-case handling    | 2nd day    |
| Phase 4 | Presentation & packaging               | 2nd day    |

---

## 👥 Key Stakeholders

* Restaurant Manager / Owner
* Frontdesk / Host
* Customer Service Ops
* Technical Dev Team

---

## 📎 File Structure

```
├── app.py
├── requirements.txt
├── prompts/
│   ├── determine_intent.txt
│   ├── generate_reservation_conversation.txt
│   ├── interpret_sql_result.txt
│   ├── schema_prompt.txt
│   └── store_user_info.txt
├── db/
│   └── restaurant_reservation.db
└── README.md
```

### Explanation of Each File

#### 1. **`app.py`**

* The main application file that serves as the backend logic for the restaurant reservation system.
* This file handles user input, determines the intent of the user, interacts with the database, and generates responses based on pre-defined prompts.
* It is responsible for orchestrating the interaction between the user, the database, and the various models or prompt files.

#### 2. **`prompts/` Folder**

The `prompts/` folder contains text files that define various parts of the restaurant reservation assistant's behavior and logic.

* **`determine_intent.txt`**:

  * Contains the prompt for determining the user's intent (e.g., whether the user is asking about restaurant availability, making a reservation, or asking for restaurant information).
  * Helps the system classify the user's input into specific intents (e.g., "greet", "select", "book","rubbish").

* **`generate_reservation_conversation.txt`**:

  * Defines the conversation logic when generating responses related to reservations.
  * Includes instructions for collecting necessary reservation details (e.g., name, party size, contact info, etc.) and handling different user interactions.
  * Used to guide the assistant's conversation flow and to extract or confirm user data for reservations.

* **`interpret_sql_result.txt`**:

  * Contains the prompt for interpreting the results of SQL queries executed on the database.
  * Used to process the output from SQL queries (such as availability of tables, restaurant features, etc.) and format the result for the assistant to present to the user.

* **`schema_prompt.txt`**:

  * Defines the schema of the restaurant reservation system’s database and serves as a guide to interact with it.
  * Contains detailed instructions for how the assistant should create database queries and interpret the structure of data stored in the system.

* **`store_user_info.txt`**:

  * Contains the prompt for extracting and storing user information such as name, contact, party size, and time of reservation.
  * Helps the assistant gather and update relevant details for a reservation, ensuring data is correctly collected and stored.

#### 3. **`db/` Folder**

The `db/` folder contains the SQLite database that stores all the relevant information for the restaurant reservation system.



### Assumptions:
* There is a hardcoded 4-person table capacity, so the system itself selects multiple tables that are available at that time.
* Reservation slots are fixed to **2025-05-12**, and all reservations are for this date.
---
### ⚠️ Limitations:

* The system currently supports reservations only for a fixed date (2025-05-12). This could be extended to multi-day support by adding appropriate entries to the database.
* Since the system relies on Large Language Models (LLMs), there's **no absolute guarantee of perfect behavior**—LLMs can occasionally misinterpret queries, miss context, or produce inaccurate outputs.
* **Table preferences cannot be specified** by the user. The system auto-assigns tables based on availability, so users cannot choose specific table locations (e.g., window-side, outdoor, etc.).
* Only **select queries** are executed directly by the LLM to ensure **data safety**. For insert/update operations (e.g., booking), a separate transaction module is used.


---
### Future Enhancements:

* Expand the system to allow for multi-day reservations.
* Also add table preferences to choose(eg. beside window,private space).
* Add features like user authentication, personalized recommendations, and more sophisticated handling of party sizes and table combinations.



---
