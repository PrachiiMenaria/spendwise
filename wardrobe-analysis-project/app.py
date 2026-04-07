from flask import Flask, render_template, request, redirect
import psycopg2
from wardrobe_ml_system.model import predict_spending
app = Flask(__name__)

# ✅ DATABASE CONNECTION FUNCTION (BEST PRACTICE)
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="wardrobe_db",
        user="postgres",
        password="wardrobe123"
    )

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        gender = request.form["gender"]
        college = request.form["college"]
        email = request.form["email"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO users(name, age, gender, college, email)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, age, gender, college, email))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/survey")

    return render_template("register.html")

# ---------------- SURVEY ----------------
@app.route("/survey", methods=["GET", "POST"])
def survey():
    if request.method == "POST":
        average_decision_time = request.form.get("average_decision_time")
        wardrobe_size = request.form.get("wardrobe_size")
        monthly_spending = request.form.get("monthly_spending")
        repeat_frequency = request.form.get("repeat_frequency")

        if monthly_spending == "":
            monthly_spending = None

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO survey_responses
            (wardrobe_size, average_decision_time, monthly_spending, repeat_frequency)
            VALUES (%s, %s, %s, %s)
        """, (wardrobe_size, average_decision_time, monthly_spending, repeat_frequency))

        conn.commit()
        cur.close()
        conn.close()

        return "Survey Submitted"

    return render_template("survey.html")

# ---------------- WARDROBE PAGE ----------------
@app.route('/wardrobe')
def wardrobe():
    return render_template('wardrobe.html')

# ---------------- ADD ITEM ----------------
@app.route('/add_item', methods=['POST'])
def add_item():
    item_name = request.form['item_name']
    category = request.form['category']
    color = request.form['color']
    price = request.form['price']
    date = request.form['date']
    wear_count = request.form['wear_count']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO wardrobe_items 
        (user_id, item_name, category, color, purchase_price, purchase_date, wear_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (1, item_name, category, color, price, date, wear_count))

    conn.commit()
    cur.close()
    conn.close()

    return redirect('/wardrobe')

# ---------------- DECISION ----------------
@app.route('/decision')
def decision():
    return render_template('decision.html')

# ---------------- ADD DECISION ----------------
@app.route('/add_decision', methods=['POST'])
def add_decision():
    decision_time = request.form['decision_time']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
                INSERT INTO outfit_decisions (user_id, date, decision_time)
                VALUES (%s, CURRENT_DATE, %s)
                """, (1, decision_time))

    conn.commit()
    cur.close()
    conn.close()

    return redirect('/decision')

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()

    # Total wardrobe items
    cur.execute("SELECT COUNT(*) FROM wardrobe_items WHERE user_id = 1")
    total_items = cur.fetchone()[0]

    # Average decision time ✅ (THIS WAS MISSING OR WRONG)
    cur.execute("SELECT AVG(decision_time) FROM outfit_decisions WHERE user_id = 1")
    avg_time = cur.fetchone()[0] or 0

    # Total spending ✅
    cur.execute("SELECT SUM(purchase_price) FROM wardrobe_items WHERE user_id = 1")
    total_spending = cur.fetchone()[0] or 0

    cur.execute("""
    SELECT category, COUNT(*) 
    FROM wardrobe_items 
    WHERE user_id = 1 
    GROUP BY category
    """)
    categories = cur.fetchall()
    categories=categories

    # Most worn item
    cur.execute("""
    SELECT item_name, wear_count 
    FROM wardrobe_items 
    WHERE user_id = 1 
    ORDER BY wear_count ASC 
    LIMIT 3
                """)
    
    least_used = cur.fetchall()
    most_worn = cur.fetchone()
    least_used=least_used

    cur.close()
    conn.close()

    return render_template("dashboard.html",
                       total_items=total_items,
                       avg_time=avg_time,
                       total_spending=total_spending,
                       most_worn=most_worn)
# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)