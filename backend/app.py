"""
fenora — Flask Backend (app.py)
Drop-in replacement: adds missing APIs, fixes response shapes expected by new frontend.
"""
import os
import json
import logging
from functools import wraps
from datetime import datetime, timedelta
from decimal import Decimal
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import Flask, request, session, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash

# ─── App Setup ────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:3000", "http://127.0.0.1:3000",
])
app.secret_key = os.getenv("SECRET_KEY", "fenora_2026_change_in_prod")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)



# ─── Utilities ────────────────────────────────────────────────────

def _f(val, default=0.0):
    if val is None:
        return float(default)
    return float(val)


def _safe_json(obj):
    if isinstance(obj, dict):
        return {k: _safe_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_safe_json(i) for i in obj]
    if isinstance(obj, Decimal):
        return float(obj)
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return obj


def get_db():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(db_url, sslmode="require")
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "wardrobe_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "wardrobe123"),
        port=os.getenv("DB_PORT", "5432"),
    )


def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*a, **kw)
    return dec


def get_uid():
    return session.get("user_id", 1)


# ─── Auth ─────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    pwd = data.get("password", "")
    budget = float(data.get("monthly_budget", data.get("budget", 10000)) or 10000)

    if not name or not email:
        return jsonify({"error": "Name and email are required."}), 400
    if len(pwd) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    try:
        conn = get_db()
        with conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users(name, email, password_hash, monthly_budget) "
                "VALUES(%s, %s, %s, %s) RETURNING id",
                (name, email, generate_password_hash(pwd), budget),
            )
            uid = cur.fetchone()[0]
        conn.close()
        session.update(user_id=uid, user_name=name, user_email=email)
        return jsonify({
            "message": f"Welcome {name}!",
            "user": {"id": uid, "name": name, "email": email},
            "user_id": uid, "name": name, "budget": budget,
        })
    except psycopg2.errors.UniqueViolation:
        return jsonify({"error": "Email already registered."}), 400
    except Exception as e:
        logger.error(f"Register error: {e}")
        return jsonify({"error": "Registration failed. Please try again."}), 500


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    pwd = data.get("password", "")

    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
    conn.close()

    if user and check_password_hash(user["password_hash"], pwd):
        session.update(user_id=user["id"], user_name=user["name"], user_email=user["email"])
        return jsonify({
            "message": f"Welcome back, {user['name']}!",
            "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
            "user_id": user["id"], "name": user["name"],
            "budget": float(user.get("monthly_budget") or 0),
        })
    return jsonify({"error": "Invalid email or password."}), 401


@app.route("/api/check-auth", methods=["GET"])
def api_check_auth():
    if "user_id" in session:
        return jsonify({
            "authenticated": True,
            "user": {"id": session["user_id"], "name": session["user_name"], "email": session["user_email"]},
        })
    return jsonify({"authenticated": False}), 401


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})


# ─── Summary & Aggregation ────────────────────────────────────────

@app.route("/api/get-summary", methods=["GET"])
@login_required
def api_get_summary():
    uid = get_uid()
    today = datetime.now()
    month = int(request.args.get("month", today.month))
    year = int(request.args.get("year", today.year))

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # This month total
    cur.execute(
        "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
        "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s",
        (uid, month, year),
    )
    row = cur.fetchone()
    current_total = _f(row["t"] if row else 0)

    # Budget
    cur.execute("SELECT monthly_budget FROM users WHERE id=%s", (uid,))
    u = cur.fetchone()
    budget = _f(u["monthly_budget"] if u else 0)

    # Never worn count
    cur.execute("SELECT COUNT(*) AS c FROM wardrobe_items WHERE user_id=%s AND wear_count=0", (uid,))
    nw = cur.fetchone()
    never_worn_count = int(nw["c"]) if nw else 0

    cur.close()
    conn.close()

    pct = round((current_total / budget * 100), 1) if budget > 0 else 0

    return jsonify(_safe_json({
        "budget": budget,
        "this_month_total": current_total,
        "total_spent": current_total,
        "remaining": max(0, budget - current_total),
        "budget_used_pct": pct,
        "pct_used": pct,
        "never_worn_count": never_worn_count,
    }))


@app.route("/api/expense-summary", methods=["GET"])
@login_required
def api_expense_summary():
    uid = get_uid()
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Category totals (all time)
    cur.execute(
        "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
        "WHERE user_id=%s GROUP BY category ORDER BY total DESC",
        (uid,),
    )
    cat_rows = cur.fetchall()
    category_totals = {r["category"]: _f(r["total"]) for r in cat_rows}

    # Monthly totals (last 6 months)
    monthly_totals = {}
    today = datetime.now()
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=30 * i)
        key = f"{d.year}-{d.month:02d}"
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses WHERE user_id=%s "
            "AND EXTRACT(YEAR FROM created_at)=%s AND EXTRACT(MONTH FROM created_at)=%s",
            (uid, d.year, d.month),
        )
        row = cur.fetchone()
        monthly_totals[key] = _f(row["t"] if row else 0)

    cur.close()
    conn.close()
    return jsonify(_safe_json({"category_totals": category_totals, "monthly_totals": monthly_totals}))


# ─── Expenses CRUD ────────────────────────────────────────────────

@app.route("/api/expenses", methods=["GET"])
@login_required
def api_expenses_get():
    uid = get_uid()
    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT id, amount, category, note, created_at FROM expenses "
            "WHERE user_id=%s ORDER BY created_at DESC LIMIT 200",
            (uid,),
        )
        rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(_safe_json(rows))


@app.route("/api/expenses", methods=["POST"])
@login_required
def api_expenses_post():
    uid = get_uid()
    data = request.json or {}
    amount = float(data.get("amount", 0) or 0)
    category = data.get("category", "Others")
    note = data.get("note", "")

    if amount <= 0:
        return jsonify({"error": "Amount must be > 0"}), 400

    conn = get_db()
    with conn, conn.cursor() as cur:
        # Try new schema first, fallback to old
        try:
            cur.execute(
                "INSERT INTO expenses(user_id, amount, category, note) "
                "VALUES(%s,%s,%s,%s) RETURNING id",
                (uid, amount, category, note),
            )
        except Exception:
            conn.rollback()
            today = datetime.now()
            cur.execute(
                "INSERT INTO expenses(user_id, amount, category, note, expense_month, expense_year) "
                "VALUES(%s,%s,%s,%s,%s,%s) RETURNING id",
                (uid, amount, category, note, today.month, today.year),
            )
        eid = cur.fetchone()[0]
    conn.close()
    return jsonify({"message": "Added", "id": eid}), 201


@app.route("/api/expenses/<int:eid>", methods=["DELETE"])
@login_required
def api_expense_delete(eid):
    uid = get_uid()
    conn = get_db()
    with conn, conn.cursor() as cur:
        cur.execute("DELETE FROM expenses WHERE id=%s AND user_id=%s", (eid, uid))
    conn.close()
    return jsonify({"message": "Deleted"})


# Legacy add-transaction
@app.route("/api/add-transaction", methods=["POST"])
@login_required
def api_add_transaction():
    uid = get_uid()
    data = request.json or {}
    amount = float(data.get("amount", 0) or 0)
    if amount <= 0:
        return jsonify({"error": "Amount must be > 0"}), 400
    category = data.get("category", "Others")
    note = data.get("note", "")
    today = datetime.now()
    conn = get_db()
    with conn, conn.cursor() as cur:
        try:
            cur.execute("INSERT INTO expenses(user_id,amount,category,note) VALUES(%s,%s,%s,%s) RETURNING id", (uid, amount, category, note))
        except Exception:
            conn.rollback()
            cur.execute("INSERT INTO expenses(user_id,amount,category,note,expense_month,expense_year) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id", (uid, amount, category, note, today.month, today.year))
        eid = cur.fetchone()[0]
    conn.close()
    return jsonify({"message": "Added", "id": eid})


# ─── Wardrobe CRUD ────────────────────────────────────────────────

@app.route("/api/wardrobe", methods=["GET"])
@login_required
def api_wardrobe_get():
    uid = get_uid()
    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM wardrobe_items WHERE user_id=%s ORDER BY created_at DESC", (uid,))
        items = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(_safe_json(items))


@app.route("/api/wardrobe", methods=["POST"])
@login_required
def api_wardrobe_post():
    uid = get_uid()
    data = request.json or {}
    item_name = data.get("item_name", "").strip()
    if not item_name:
        return jsonify({"error": "Item name required"}), 400
    category = data.get("category", "Other")
    color = data.get("color", "")
    price = float(data.get("purchase_price", 0) or 0)
    conn = get_db()
    with conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO wardrobe_items(user_id,item_name,category,color,purchase_price,wear_count) "
            "VALUES(%s,%s,%s,%s,%s,0) RETURNING id",
            (uid, item_name, category, color, price),
        )
        wid = cur.fetchone()[0]
    conn.close()
    return jsonify({"message": "Added", "id": wid}), 201


@app.route("/api/wardrobe/<int:wid>", methods=["DELETE"])
@login_required
def api_wardrobe_delete(wid):
    uid = get_uid()
    conn = get_db()
    with conn, conn.cursor() as cur:
        cur.execute("DELETE FROM wardrobe_items WHERE id=%s AND user_id=%s", (wid, uid))
    conn.close()
    return jsonify({"message": "Deleted"})


@app.route("/api/wardrobe-data", methods=["GET"])
@login_required
def api_wardrobe_data():
    uid = get_uid()
    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM wardrobe_items WHERE user_id=%s ORDER BY wear_count DESC", (uid,))
        items = [dict(r) for r in cur.fetchall()]
    conn.close()

    total_items = len(items)
    total_value = sum(_f(i.get("purchase_price")) for i in items)
    utilization = [{"name": i["item_name"], "wear_count": i.get("wear_count") or 0} for i in items]

    return jsonify(_safe_json({
        "total_items": total_items,
        "total_value": total_value,
        "utilization_data": utilization,
        "items": items,
    }))


@app.route("/api/log-wear/<int:item_id>", methods=["POST"])
@login_required
def api_log_wear(item_id):
    uid = get_uid()
    conn = get_db()
    with conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE wardrobe_items SET wear_count=wear_count+1 WHERE id=%s AND user_id=%s RETURNING wear_count",
            (item_id, uid),
        )
        row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"message": "Logged", "wear_count": row[0]})


# Legacy wardrobe endpoints
@app.route("/api/add-wardrobe-item", methods=["POST"])
@login_required
def api_add_wardrobe_item():
    return api_wardrobe_post()


# ─── AI Analysis ──────────────────────────────────────────────────

def _generate_ai_analysis(uid):
    """Generate data-driven insights without any AI library dependency."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    today = datetime.now()

    # Expenses
    cur.execute(
        "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
        "WHERE user_id=%s AND EXTRACT(YEAR FROM created_at)=%s AND EXTRACT(MONTH FROM created_at)=%s "
        "GROUP BY category ORDER BY total DESC",
        (uid, today.year, today.month),
    )
    this_month_cats = {r["category"]: _f(r["total"]) for r in cur.fetchall()}
    this_month_total = sum(this_month_cats.values())

    # Last month
    last = today.replace(day=1) - timedelta(days=1)
    cur.execute(
        "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
        "WHERE user_id=%s AND EXTRACT(YEAR FROM created_at)=%s AND EXTRACT(MONTH FROM created_at)=%s "
        "GROUP BY category",
        (uid, last.year, last.month),
    )
    last_month_cats = {r["category"]: _f(r["total"]) for r in cur.fetchall()}
    last_month_total = sum(last_month_cats.values())

    # Budget
    cur.execute("SELECT monthly_budget FROM users WHERE id=%s", (uid,))
    u = cur.fetchone()
    budget = _f(u["monthly_budget"] if u else 0)

    # Wardrobe
    cur.execute("SELECT * FROM wardrobe_items WHERE user_id=%s", (uid,))
    wardrobe = cur.fetchall()

    cur.close()
    conn.close()

    expense_insights = []
    wardrobe_insights = []
    recommendations = []

    # --- Expense Insights ---
    if this_month_total > 0 and budget > 0:
        pct = (this_month_total / budget) * 100
        if pct >= 90:
            expense_insights.append({"icon": "🚨", "type": "danger", "text": f"You've used {pct:.0f}% of your monthly budget (₹{this_month_total:,.0f} of ₹{budget:,.0f}). Slow down spending!"})
        elif pct >= 70:
            expense_insights.append({"icon": "⚠️", "type": "warning", "text": f"You've spent {pct:.0f}% of your budget this month. ₹{max(0, budget - this_month_total):,.0f} left."})
        else:
            expense_insights.append({"icon": "✅", "type": "success", "text": f"Great job! You've only spent {pct:.0f}% of your budget. ₹{max(0, budget - this_month_total):,.0f} remaining."})

    if this_month_cats:
        top_cat, top_amt = max(this_month_cats.items(), key=lambda x: x[1])
        if this_month_total > 0:
            top_pct = (top_amt / this_month_total) * 100
            expense_insights.append({"icon": "📊", "type": "info", "text": f"You spent {top_pct:.0f}% of your budget on {top_cat} (₹{top_amt:,.0f}) — your biggest category this month."})

    if last_month_total > 0 and this_month_total > 0:
        change = ((this_month_total - last_month_total) / last_month_total) * 100
        if change > 15:
            expense_insights.append({"icon": "📈", "type": "warning", "text": f"Your spending increased by {change:.0f}% vs last month. You spent ₹{this_month_total - last_month_total:,.0f} more."})
        elif change < -10:
            expense_insights.append({"icon": "📉", "type": "success", "text": f"Great work! Spending dropped by {abs(change):.0f}% vs last month. You saved ₹{last_month_total - this_month_total:,.0f}."})

    food_spend = this_month_cats.get("Food", 0)
    if food_spend > 0 and this_month_total > 0:
        food_pct = (food_spend / this_month_total) * 100
        if food_pct > 35:
            potential_save = food_spend * 0.25
            expense_insights.append({"icon": "🍱", "type": "warning", "text": f"Food costs ₹{food_spend:,.0f} ({food_pct:.0f}% of total). Cutting delivery orders by 25% could save ₹{potential_save:,.0f}/month."})

    # --- Wardrobe Insights ---
    if wardrobe:
        never_worn = [i for i in wardrobe if (i.get("wear_count") or 0) == 0]
        total_value = sum(_f(i.get("purchase_price")) for i in wardrobe)
        never_worn_value = sum(_f(i.get("purchase_price")) for i in never_worn)

        if len(never_worn) > 0:
            wardrobe_insights.append({"icon": "😴", "type": "warning", "text": f"{len(never_worn)} item{'s' if len(never_worn) > 1 else ''} in your wardrobe {'have' if len(never_worn) > 1 else 'has'} never been worn, worth ₹{never_worn_value:,.0f} sitting unused."})

        # Most worn
        worn = sorted(wardrobe, key=lambda x: x.get("wear_count") or 0, reverse=True)
        if worn and (worn[0].get("wear_count") or 0) > 0:
            top = worn[0]
            price = _f(top.get("purchase_price"))
            wears = top.get("wear_count") or 1
            cpw = price / wears if wears > 0 and price > 0 else 0
            wardrobe_insights.append({"icon": "⭐", "type": "success", "text": f"Your most-worn item is '{top['item_name']}' ({wears} wears){f', costing only ₹{cpw:.0f}/wear — excellent value!' if cpw > 0 else '.'}"})

        if total_value > 0 and len(never_worn) > 0:
            waste_pct = (never_worn_value / total_value) * 100
            wardrobe_insights.append({"icon": "💸", "type": "info", "text": f"₹{never_worn_value:,.0f} ({waste_pct:.0f}% of your wardrobe value) is tied up in unworn clothes. Try wearing them before buying more."})

    # --- Recommendations ---
    # Food delivery
    if food_spend > 1500:
        save_amt = int(food_spend * 0.3)
        recommendations.append({
            "icon": "🍕", "priority": "high",
            "title": "Reduce food delivery",
            "text": f"You're spending ₹{food_spend:,.0f}/month on food. Cook at home 3 extra days/week to save ₹{save_amt:,}."
        })

    # Unused wardrobe → avoid shopping
    if wardrobe:
        never_worn = [i for i in wardrobe if (i.get("wear_count") or 0) == 0]
        tops_count = len([i for i in never_worn if i.get("category") in ("Tops", "T-Shirts", "Shirts")])
        if tops_count >= 3:
            recommendations.append({
                "icon": "👕", "priority": "high",
                "title": f"Don't buy more tops this month",
                "text": f"You already own {tops_count} unworn tops. Wear them before buying new ones."
            })

    shopping_spend = this_month_cats.get("Shopping", 0)
    if shopping_spend > 2000:
        recommendations.append({
            "icon": "🛍️", "priority": "medium",
            "title": "Watch your shopping spend",
            "text": f"You've spent ₹{shopping_spend:,.0f} on shopping this month. Try a 7-day no-shopping challenge."
        })

    if budget > 0 and this_month_total > budget * 0.85:
        recommendations.append({
            "icon": "📅", "priority": "high",
            "title": "Budget almost exhausted",
            "text": f"You've used {(this_month_total/budget*100):.0f}% of your budget. Avoid non-essential purchases for the rest of the month."
        })

    if not expense_insights and not wardrobe_insights:
        expense_insights.append({"icon": "💡", "type": "info", "text": "Log more expenses and wardrobe items to unlock personalised AI insights!"})

    return {
        "expense_insights": expense_insights,
        "wardrobe_insights": wardrobe_insights,
        "recommendations": recommendations,
    }


@app.route("/api/ai-analysis", methods=["GET"])
@login_required
def api_ai_analysis():
    uid = get_uid()
    try:
        result = _generate_ai_analysis(uid)
        return jsonify(_safe_json(result))
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        return jsonify({
            "expense_insights": [{"icon": "⚠️", "type": "info", "text": "Could not generate insights. Add some data first!"}],
            "wardrobe_insights": [],
            "recommendations": [],
        })


# ─── Chat ─────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    uid = get_uid()
    data = request.json or {}
    key = data.get("question_key", "budget")

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        today = datetime.now()

        cur.execute("SELECT monthly_budget FROM users WHERE id=%s", (uid,))
        u = cur.fetchone()
        budget = _f(u["monthly_budget"] if u else 0)

        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses WHERE user_id=%s "
            "AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s",
            (uid, today.month, today.year),
        )
        spent_row = cur.fetchone()
        spent = _f(spent_row["t"] if spent_row else 0)

        cur.execute(
            "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
            "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s "
            "GROUP BY category ORDER BY total DESC LIMIT 1",
            (uid, today.month, today.year),
        )
        top = cur.fetchone()

        cur.execute("SELECT COUNT(*) AS c FROM wardrobe_items WHERE user_id=%s AND wear_count=0", (uid,))
        nw = cur.fetchone()
        never_worn = int(nw["c"]) if nw else 0

        cur.close()
        conn.close()

        remaining = max(0, budget - spent)
        pct = (spent / budget * 100) if budget > 0 else 0

        if key == "budget":
            if pct >= 90:
                reply = f"🚨 Your budget is critically low! You've spent ₹{spent:,.0f} out of ₹{budget:,.0f} ({pct:.0f}%). Only ₹{remaining:,.0f} left. Avoid all non-essential purchases immediately."
            elif pct >= 70:
                reply = f"⚠️ Your budget is getting tight. You've used {pct:.0f}% (₹{spent:,.0f} of ₹{budget:,.0f}). You have ₹{remaining:,.0f} left — be careful with the rest of the month."
            elif pct > 0:
                reply = f"✅ Your budget looks healthy! You've spent {pct:.0f}% (₹{spent:,.0f} of ₹{budget:,.0f}), with ₹{remaining:,.0f} still available. Keep it up!"
            else:
                reply = "No budget data available yet. Set your monthly budget and start tracking expenses!"

        elif key == "reduce":
            tips = []
            if top:
                tips.append(f"Your biggest expense this month is {top['category']} (₹{_f(top['total']):,.0f}) — try cutting this by 20%.")
            tips.append("Cook at home instead of ordering food delivery — saves ₹800–1500/month on average.")
            tips.append("Use UPI cashback offers and avoid impulse purchases by waiting 24 hours before buying.")
            if never_worn > 0:
                tips.append(f"You have {never_worn} unworn wardrobe items — wear them before buying anything new!")
            reply = " | ".join(tips) if tips else "Log more expenses to get personalised reduction tips."

        elif key == "avoid":
            avoids = []
            if never_worn >= 3:
                avoids.append(f"Clothes — you already have {never_worn} items you've never worn. Use what you own!")
            if top and top["category"] in ("Shopping", "Entertainment"):
                avoids.append(f"More {top['category'].lower()} spending — it's already your top category this month.")
            avoids.append("Subscription services you don't use regularly.")
            avoids.append("Food delivery on weekdays — pack lunch instead and save ₹150–250/day.")
            reply = " Avoid: " + " | Also avoid: ".join(avoids) if avoids else "Track your expenses to get personalised advice."

        else:
            reply = "Ask me about your budget, how to reduce spending, or what to avoid buying!"

    except Exception as e:
        logger.error(f"Chat error: {e}")
        reply = "Something went wrong. Make sure you have some data logged first!"

    return jsonify({"reply": reply})


# ─── Email Reminder (manual trigger) ─────────────────────────────

@app.route("/api/send-monthly-report", methods=["POST"])
@login_required
def api_send_monthly_report():
    uid = get_uid()
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT name, email, monthly_budget FROM users WHERE id=%s", (uid,))
        user = cur.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        today = datetime.now()
        last = today.replace(day=1) - timedelta(days=1)

        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses WHERE user_id=%s "
            "AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s",
            (uid, last.month, last.year),
        )
        last_total_row = cur.fetchone()
        last_total = _f(last_total_row["t"] if last_total_row else 0)

        cur.execute(
            "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
            "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s "
            "GROUP BY category ORDER BY total DESC",
            (uid, last.month, last.year),
        )
        cats = {r["category"]: _f(r["total"]) for r in cur.fetchall()}

        cur.execute("SELECT COUNT(*) AS c FROM wardrobe_items WHERE user_id=%s AND wear_count=0", (uid,))
        nw = cur.fetchone()
        never_worn = int(nw["c"]) if nw else 0

        cur.close()
        conn.close()

        budget = _f(user["monthly_budget"])
        overspend = max(0, last_total - budget)

        # Build email
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        if not smtp_user or not smtp_pass:
            return jsonify({"error": "Email not configured. Set SMTP_USER and SMTP_PASS env vars."}), 400

        month_name = last.strftime("%B %Y")
        subject = f"fenora Monthly Report — {month_name}"

        cat_lines = "\n".join([f"  • {c}: ₹{v:,.0f}" for c, v in cats.items()])

        body = f"""Hello {user['name']},

Here is your fenora monthly report for {month_name}:

💰 SPENDING SUMMARY
━━━━━━━━━━━━━━━━━━
Total Spent:    ₹{last_total:,.0f}
Monthly Budget: ₹{budget:,.0f}
{"🚨 Overspent by: ₹" + f"{overspend:,.0f}" if overspend > 0 else "✅ Under budget by: ₹" + f"{max(0, budget - last_total):,.0f}"}

📂 BY CATEGORY
━━━━━━━━━━━━━━
{cat_lines if cat_lines else "  No data"}

👗 WARDROBE
━━━━━━━━━━━
Unworn items: {never_worn} {"(consider using these before buying more!)" if never_worn > 0 else "(great utilization!)"}

💡 TIP FOR THIS MONTH
{"Reduce non-essential spending to stay within budget." if overspend > 0 else "Keep up the great work! Try to save even more this month."}

— fenora AI
"""

        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = user["email"]
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, user["email"], msg.as_string())

        return jsonify({"message": f"Report sent to {user['email']}"})

    except Exception as e:
        logger.error(f"Email error: {e}")
        return jsonify({"error": str(e)}), 500

# ─── Savings Goals ────────────────────────────────────────────────
# Add this SQL to create the table (run once in your DB):
# CREATE TABLE IF NOT EXISTS savings_goals (
#   id SERIAL PRIMARY KEY,
#   user_id INTEGER NOT NULL REFERENCES users(id),
#   name VARCHAR(200) NOT NULL,
#   target_amount NUMERIC(12,2) NOT NULL,
#   saved_amount NUMERIC(12,2) DEFAULT 0,
#   months INTEGER DEFAULT 2,
#   created_at TIMESTAMP DEFAULT NOW()
# );


@app.route("/api/savings-goals", methods=["GET"])
@login_required
def api_savings_goals_get():
    uid = get_uid()
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM savings_goals WHERE user_id=%s ORDER BY created_at DESC",
                (uid,),
            )
            goals = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(_safe_json(goals))
    except Exception as e:
        logger.error(f"Savings goals get error: {e}")
        return jsonify([])  # Return empty list gracefully if table doesn't exist yet


@app.route("/api/savings-goals", methods=["POST"])
@login_required
def api_savings_goals_post():
    uid = get_uid()
    data = request.json or {}
    name = data.get("name", "").strip()
    target = float(data.get("target_amount", 0) or 0)
    months = int(data.get("months", 2) or 2)

    if not name or target <= 0:
        return jsonify({"error": "Name and target amount required"}), 400

    try:
        conn = get_db()
        with conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO savings_goals(user_id, name, target_amount, months, saved_amount) "
                "VALUES(%s,%s,%s,%s,0) RETURNING id",
                (uid, name, target, months),
            )
            gid = cur.fetchone()[0]
        conn.close()
        return jsonify({"message": "Goal added", "id": gid}), 201
    except Exception as e:
        logger.error(f"Savings goal add error: {e}")
        return jsonify({"error": "Could not save goal. Make sure the savings_goals table exists."}), 500


@app.route("/api/savings-goals/<int:gid>", methods=["DELETE"])
@login_required
def api_savings_goals_delete(gid):
    uid = get_uid()
    try:
        conn = get_db()
        with conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM savings_goals WHERE id=%s AND user_id=%s",
                (gid, uid),
            )
        conn.close()
        return jsonify({"message": "Deleted"})
    except Exception as e:
        logger.error(f"Savings goal delete error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/savings-goals/<int:gid>/deposit", methods=["POST"])
@login_required
def api_savings_goals_deposit(gid):
    """Add savings progress to a goal."""
    uid = get_uid()
    data = request.json or {}
    amount = float(data.get("amount", 0) or 0)
    if amount <= 0:
        return jsonify({"error": "Amount must be > 0"}), 400
    try:
        conn = get_db()
        with conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE savings_goals SET saved_amount = saved_amount + %s "
                "WHERE id=%s AND user_id=%s RETURNING saved_amount",
                (amount, gid, uid),
            )
            row = cur.fetchone()
        conn.close()
        if not row:
            return jsonify({"error": "Goal not found"}), 404
        return jsonify({"message": "Updated", "saved_amount": float(row[0])})
    except Exception as e:
        logger.error(f"Savings deposit error: {e}")
        return jsonify({"error": str(e)}), 500
    
"""
app_extensions.py — New API routes for Fenora Phase 2
======================================================
Add these routes to your existing app.py.

Steps:
  1. pip install analysis_services (copy analysis_services.py to project root)
  2. In app.py, add at the top:
       from analysis_services import (
           get_spending_heatmap, detect_spending_personality,
           detect_anomalies, detect_recurring_expenses,
           calculate_savings_streak, suggest_budget,
           generate_weekly_report, get_category_budget_status,
           get_monthly_recap,
       )
  3. Paste all routes below into app.py before `if __name__ == "__main__":`
  4. Run SQL migration below once.

── SQL MIGRATION (run once) ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS category_budgets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    category VARCHAR(100) NOT NULL,
    cap_amount NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, category)
);

CREATE TABLE IF NOT EXISTS outfit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    items JSONB NOT NULL DEFAULT '[]',
    note TEXT,
    worn_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
──────────────────────────────────────────────────────────────────
"""

# ── Spending Heatmap ───────────────────────────────────────────────

@app.route("/api/heatmap", methods=["GET"])
@login_required
def api_heatmap():
    uid = get_uid()
    days = int(request.args.get("days", 90))
    try:
        from analysis_services import get_spending_heatmap
        data = get_spending_heatmap(uid, days)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Heatmap error: {e}")
        return jsonify([])


# ── Spending Personality ───────────────────────────────────────────

@app.route("/api/personality", methods=["GET"])
@login_required
def api_personality():
    uid = get_uid()
    try:
        from analysis_services import detect_spending_personality
        return jsonify(detect_spending_personality(uid))
    except Exception as e:
        logger.error(f"Personality error: {e}")
        return jsonify({"personality": "unknown", "label": "Unknown", "description": "Not enough data.", "traits": [], "icon": "🌱", "color": "#9898b8"})


# ── Anomaly Detection ──────────────────────────────────────────────

@app.route("/api/anomalies", methods=["GET"])
@login_required
def api_anomalies():
    uid = get_uid()
    try:
        from analysis_services import detect_anomalies
        return jsonify(detect_anomalies(uid))
    except Exception as e:
        logger.error(f"Anomaly error: {e}")
        return jsonify([])


# ── Recurring Expenses ─────────────────────────────────────────────

@app.route("/api/recurring", methods=["GET"])
@login_required
def api_recurring():
    uid = get_uid()
    try:
        from analysis_services import detect_recurring_expenses
        return jsonify(detect_recurring_expenses(uid))
    except Exception as e:
        logger.error(f"Recurring error: {e}")
        return jsonify([])


# ── Savings Streak ─────────────────────────────────────────────────

@app.route("/api/streak", methods=["GET"])
@login_required
def api_streak():
    uid = get_uid()
    try:
        from analysis_services import calculate_savings_streak
        return jsonify(calculate_savings_streak(uid))
    except Exception as e:
        logger.error(f"Streak error: {e}")
        return jsonify({"streak": 0, "best_streak": 0, "daily_budget": 0, "message": "Set a budget to track your streak."})


# ── Budget Suggestion ──────────────────────────────────────────────

@app.route("/api/suggest-budget", methods=["GET"])
@login_required
def api_suggest_budget():
    uid = get_uid()
    try:
        from analysis_services import suggest_budget
        return jsonify(suggest_budget(uid))
    except Exception as e:
        logger.error(f"Budget suggest error: {e}")
        return jsonify({"suggested": 10000, "reason": "Could not generate suggestion.", "category_breakdown": {}})


# ── Weekly Report ──────────────────────────────────────────────────

@app.route("/api/weekly-report", methods=["GET"])
@login_required
def api_weekly_report():
    uid = get_uid()
    try:
        from analysis_services import generate_weekly_report
        return jsonify(generate_weekly_report(uid))
    except Exception as e:
        logger.error(f"Weekly report error: {e}")
        return jsonify({"error": str(e)}), 500


# ── Category Budget Caps ───────────────────────────────────────────

@app.route("/api/category-budgets", methods=["GET"])
@login_required
def api_category_budgets_get():
    uid = get_uid()
    try:
        from analysis_services import get_category_budget_status
        return jsonify(get_category_budget_status(uid))
    except Exception as e:
        logger.error(f"Cat budgets error: {e}")
        return jsonify([])


@app.route("/api/category-budgets", methods=["POST"])
@login_required
def api_category_budgets_set():
    uid = get_uid()
    data = request.json or {}
    category = data.get("category", "").strip()
    cap = float(data.get("cap_amount", 0) or 0)
    if not category or cap <= 0:
        return jsonify({"error": "Category and cap amount required"}), 400
    try:
        conn = get_db()
        with conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO category_budgets(user_id, category, cap_amount)
                VALUES(%s, %s, %s)
                ON CONFLICT(user_id, category)
                DO UPDATE SET cap_amount = EXCLUDED.cap_amount
            """, (uid, category, cap))
        conn.close()
        return jsonify({"message": "Budget cap set"})
    except Exception as e:
        logger.error(f"Cat budget set error: {e}")
        return jsonify({"error": "Could not set budget. Make sure category_budgets table exists."}), 500


# ── Monthly Recap ──────────────────────────────────────────────────

@app.route("/api/monthly-recap", methods=["GET"])
@login_required
def api_monthly_recap():
    uid = get_uid()
    today = datetime.now()
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))
    try:
        from analysis_services import get_monthly_recap
        return jsonify(_safe_json(get_monthly_recap(uid, year, month)))
    except Exception as e:
        logger.error(f"Monthly recap error: {e}")
        return jsonify({"error": str(e)}), 500


# ── Update User Budget ─────────────────────────────────────────────

@app.route("/api/update-budget", methods=["POST"])
@login_required
def api_update_budget():
    uid = get_uid()
    data = request.json or {}
    budget = float(data.get("monthly_budget", 0) or 0)
    if budget <= 0:
        return jsonify({"error": "Budget must be > 0"}), 400
    try:
        conn = get_db()
        with conn, conn.cursor() as cur:
            cur.execute("UPDATE users SET monthly_budget = %s WHERE id = %s", (budget, uid))
        conn.close()
        return jsonify({"message": "Budget updated", "monthly_budget": budget})
    except Exception as e:
        logger.error(f"Budget update error: {e}")
        return jsonify({"error": str(e)}), 500


# ── Outfit Log ─────────────────────────────────────────────────────

@app.route("/api/outfit-logs", methods=["GET"])
@login_required
def api_outfit_logs_get():
    uid = get_uid()
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id, items, note, worn_date, created_at
                FROM outfit_logs
                WHERE user_id = %s ORDER BY worn_date DESC LIMIT 30
            """, (uid,))
            logs = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(_safe_json(logs))
    except Exception as e:
        logger.error(f"Outfit logs get error: {e}")
        return jsonify([])


@app.route("/api/outfit-logs", methods=["POST"])
@login_required
def api_outfit_logs_post():
    uid = get_uid()
    data = request.json or {}
    items = data.get("items", [])  # list of wardrobe item IDs
    note = data.get("note", "")
    worn_date = data.get("worn_date", str(datetime.now().date()))

    if not items:
        return jsonify({"error": "Select at least one item"}), 400

    try:
        conn = get_db()
        with conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO outfit_logs(user_id, items, note, worn_date)
                VALUES(%s, %s, %s, %s) RETURNING id
            """, (uid, json.dumps(items), note, worn_date))
            oid = cur.fetchone()[0]
            # Increment wear count for each item
            for item_id in items:
                cur.execute("""
                    UPDATE wardrobe_items SET wear_count = wear_count + 1
                    WHERE id = %s AND user_id = %s
                """, (item_id, uid))
        conn.close()
        return jsonify({"message": "Outfit logged", "id": oid}), 201
    except Exception as e:
        logger.error(f"Outfit log error: {e}")
        return jsonify({"error": str(e)}), 500
# ─── Run ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.getenv("PORT", 5000))
    app.run(debug=debug_mode, host="0.0.0.0", port=port)