from flask import Flask, request, jsonify, render_template
import mysql.connector
import pandas as pd
import plotly.express as px
import openai
import os
from dotenv import load_dotenv

app = Flask(__name__, template_folder="templates", static_folder="static")

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="ImOjas@123",
        database="expense_tracker"
    )

# Create tables if not exist
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            amount DECIMAL(10,2) NOT NULL,
            category VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            location VARCHAR(255) DEFAULT 'Unknown',
            payment_mode VARCHAR(50) DEFAULT 'Cash'
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

create_tables()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/add_expense', methods=['POST'])
def add_expense():
    data = request.json
    amount, category, date = data['amount'], data['category'], data['date']
    location = data.get('location', 'Unknown')
    payment_mode = data.get('payment_mode', 'Cash')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO expenses (amount, category, date, location, payment_mode) 
        VALUES (%s, %s, %s, %s, %s)
    """, (amount, category, date, location, payment_mode))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Expense added successfully!"})

@app.route('/get_expenses', methods=['GET'])
def get_expenses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, amount, category, date, location, payment_mode FROM expenses")
    expenses = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(expenses)

@app.route('/delete_expense/<int:id>', methods=['DELETE'])
def delete_expense(id):
    print(f"Received DELETE request for expense ID: {id}")  # Debugging
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Expense deleted successfully!"})
    except Exception as e:
        print(f"Error deleting expense: {e}")
        return jsonify({"error": "Failed to delete expense"}), 500

@app.route('/update_expense/<int:id>', methods=['PUT'])
def update_expense(id):
    data = request.json
    print(f"Received UPDATE request for ID {id} with data: {data}")  

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE expenses 
            SET amount=%s, category=%s, date=%s, location=%s, payment_mode=%s 
            WHERE id=%s
        """, (data['amount'], data['category'], data['date'], data['location'], data['payment_mode'], id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Expense updated successfully!"})
    except Exception as e:
        print(f"Error updating expense: {e}")
        return jsonify({"error": "Failed to update expense"}), 500

@app.route('/get_charts_data', methods=['GET'])
def get_charts_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM expenses")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        return jsonify({"error": "No data available"})

    df = pd.DataFrame(rows)
    df['date'] = pd.to_datetime(df['date'])

    # Expense per category (Pie Chart)
    category_pie = px.pie(df, values='amount', names='category', title='Expense Distribution by Category')

    # Expense over time (Line Chart)
    time_series = df.groupby('date')['amount'].sum().reset_index()
    expense_trend = px.line(time_series, x='date', y='amount', title='Expenses Over Time')

    # Payment mode distribution (Bar Chart)
    payment_mode_bar = px.bar(df, x='payment_mode', y='amount', title='Expenses by Payment Mode', color='payment_mode')

    # Category-wise Spending Over Time (Stacked Bar Chart)
    category_trend = px.bar(df, x='date', y='amount', color='category', title='Category-wise Spending Over Time', barmode='stack')

    # Expense Heatmap (Days vs. Categories)
    df['day_of_week'] = df['date'].dt.day_name()
    heatmap_data = df.pivot_table(values='amount', index='day_of_week', columns='category', aggfunc='sum', fill_value=0)
    expense_heatmap = px.imshow(heatmap_data, labels=dict(x="Category", y="Day of Week", color="Amount"),
                                title="Expense Heatmap (Days vs. Categories)")

    return jsonify({
        "category_pie": category_pie.to_json(),
        "expense_trend": expense_trend.to_json(),
        "payment_mode_bar": payment_mode_bar.to_json(),
        "category_trend": category_trend.to_json(),
        "expense_heatmap": expense_heatmap.to_json()
    })

# import openai
# import os
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# # OpenAI API Key 
# openai_api_key = os.getenv("OPENAI_API_KEY")

# client = openai.OpenAI(api_key=openai_api_key)  # Use new API client

# @app.route('/chatgpt_insights', methods=['GET'])
# def chatgpt_insights():
#     """Fetches expenses from the database and gets insights from ChatGPT."""
#     with get_db_connection() as conn:
#         with conn.cursor(dictionary=True) as cursor:
#             cursor.execute("SELECT category, amount, date FROM expenses")
#             expenses = cursor.fetchall()
    
#     if not expenses:
#         return jsonify({"error": "No expenses found!"}), 400

#     df = pd.DataFrame(expenses)
#     df['date'] = pd.to_datetime(df['date'])
    
#     expense_summary = df.groupby("category")["amount"].sum().to_string()

#     prompt = f"""
#     Analyze the following expense data and provide insights on spending patterns, cost-saving tips, and any unusual trends:
#     {expense_summary}
#     """

#     try:
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": "You are a financial assistant analyzing user expenses."},
#                 {"role": "user", "content": prompt}
#             ]
#         )

#         insights = response.choices[0].message.content  # New way to access response content
        
#         return jsonify({"insights": insights})

#     except Exception as e:
#         print(f"Error fetching ChatGPT insights: {e}")
#         return jsonify({"error": "Failed to generate insights"}), 500

import google.generativeai as genai

# Load Gemini API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@app.route('/chatgpt_insights', methods=['POST'])
def chatgpt_insights():
    data = request.json
    user_query = data.get("question", "").strip()

    if not user_query:
        return jsonify({"error": "No question provided!"}), 400

    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT category, amount, date FROM expenses")
            expenses = cursor.fetchall()

    if not expenses:
        return jsonify({"error": "No expenses found!"}), 400

    df = pd.DataFrame(expenses)
    df['date'] = pd.to_datetime(df['date'])

    expense_summary = df.groupby("category")["amount"].sum().to_string()

    prompt = f"""
    You are a financial assistant. Below is the user's expense data:
    
    {expense_summary}

    The user asks: "{user_query}"
    Provide a helpful response based on the given expenses.
    """

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    return jsonify({"insights": response.text})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
