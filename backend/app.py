import os
import json
import logging
from functools import wraps
from datetime import datetime, timedelta
from decimal import Decimal

from flask import Flask, request, session, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash

import ai_engine

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://127.0.0.1:5173"])
app.secret_key = os.getenv("SECRET_KEY", "finora_2024_change_in_prod")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ── Utilities ──────────────────────────────────────────────────────

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


# ── Auth ───────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    pwd = data.get("password", "")
    budget = float(data.get("monthly_budget", 0) or 0)

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
        return jsonify({"message": f"Welcome {name}!", "user": {"id": uid, "name": name, "email": email}})
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
        })

    return jsonify({"error": "Invalid email or password."}), 401


@app.route("/api/check-auth", methods=["GET"])
def api_check_auth():
    if "user_id" in session:
        return jsonify({
            "authenticated": True,
            "user": {
                "id": session["user_id"],
                "name": session["user_name"],
                "email": session["user_email"],
            },
        })
    return jsonify({"authenticated": False}), 401


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})


# ── Expenses ───────────────────────────────────────────────────────

@app.route("/api/get-summary", methods=["GET"])
@login_required
def api_get_summary():
    uid = session["user_id"]
    today = datetime.now()
    month = int(request.args.get("month", today.month))
    year = int(request.args.get("year", today.year))

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses "
        "WHERE user_id=%s AND expense_year=%s AND expense_month=%s",
        (uid, year, month),
    )
    current_total = _f(cur.fetchone()["total"])

    # Budget (month-specific first, then user default)
    cur.execute(
        "SELECT amount FROM budgets WHERE user_id=%s AND year=%s AND month=%s",
        (uid, year, month),
    )
    row = cur.fetchone()
    if not row:
        cur.execute("SELECT monthly_budget FROM users WHERE id=%s", (uid,))
        row2 = cur.fetchone()
        budget = _f(row2["monthly_budget"]) if row2 else 0.0
    else:
        budget = _f(row["amount"])

    # Category breakdown
    cur.execute(
        "SELECT category, ROUND(SUM(amount)::numeric, 2) AS total "
        "FROM expenses WHERE user_id=%s AND expense_year=%s AND expense_month=%s "
        "GROUP BY category ORDER BY total DESC",
        (uid, year, month),
    )
    by_category = [{"category": r["category"], "total": _f(r["total"])} for r in cur.fetchall()]

    # 6-month spending trend
    trend_labels, trend_values = [], []
    for i in range(5, -1, -1):
        d = datetime(year, month, 1) - timedelta(days=30 * i)
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS t FROM expenses "
            "WHERE user_id=%s AND expense_year=%s AND expense_month=%s",
            (uid, d.year, d.month),
        )
        trend_labels.append(d.strftime("%b"))
        trend_values.append(_f(cur.fetchone()["t"]))

    # Recent transactions
    cur.execute(
        "SELECT id, amount, category, expense_month, expense_year, note, created_at "
        "FROM expenses WHERE user_id=%s ORDER BY created_at DESC LIMIT 5",
        (uid,),
    )
    recent_transactions = [dict(r) for r in cur.fetchall()]

    cur.close()
    conn.close()

    return jsonify(_safe_json({
        "budget": budget,
        "total_spent": current_total,
        "remaining": max(0, budget - current_total),
        "pct_used": (current_total / budget * 100) if budget > 0 else 0,
        "category_breakdown": by_category,
        "trend_labels": trend_labels,
        "trend_values": trend_values,
        "recent_transactions": recent_transactions,
    }))


@app.route("/api/add-transaction", methods=["POST"])
@login_required
def api_add_transaction():
    uid = session["user_id"]
    data = request.json or {}
    amount = float(data.get("amount", 0) or 0)
    category = data.get("category", "Others")
    note = data.get("note", "")

    today = datetime.now()
    month = int(data.get("month", today.month))
    year = int(data.get("year", today.year))

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    conn = get_db()
    with conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO expenses(user_id, amount, category, expense_month, expense_year, note) "
            "VALUES(%s, %s, %s, %s, %s, %s) RETURNING id",
            (uid, amount, category, month, year, note),
        )
        tx_id = cur.fetchone()[0]
    conn.close()

    return jsonify({"message": "Transaction added successfully", "id": tx_id})


# ── Wardrobe ───────────────────────────────────────────────────────

@app.route("/api/wardrobe-data", methods=["GET"])
@login_required
def api_wardrobe_data():
    uid = session["user_id"]
    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT * FROM wardrobe_items WHERE user_id=%s ORDER BY created_at DESC",
            (uid,),
        )
        items = cur.fetchall()
        for item in items:
            p = _f(item.get("purchase_price") or 0)
            w = item.get("wear_count") or 0
            item["cpw"] = round(p / w, 2) if w > 0 else p
    conn.close()
    return jsonify(_safe_json(items))


@app.route("/api/add-wardrobe-item", methods=["POST"])
@login_required
def api_add_wardrobe_item():
    uid = session["user_id"]
    data = request.json or {}
    item_name = data.get("item_name", "").strip()
    category = data.get("category", "Other")
    color = data.get("color", "")
    purchase_price = float(data.get("purchase_price", 0) or 0)

    if not item_name:
        return jsonify({"error": "Item name is required"}), 400

    conn = get_db()
    with conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO wardrobe_items(user_id, item_name, category, color, purchase_price, wear_count) "
            "VALUES(%s, %s, %s, %s, %s, 0) RETURNING id",
            (uid, item_name, category, color, purchase_price),
        )
        item_id = cur.fetchone()[0]
    conn.close()
    return jsonify({"message": "Item added successfully", "id": item_id})


@app.route("/api/log-wear/<int:item_id>", methods=["POST"])
@login_required
def api_log_wear(item_id):
    uid = session["user_id"]
    conn = get_db()
    with conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE wardrobe_items SET wear_count = wear_count + 1 "
            "WHERE id=%s AND user_id=%s RETURNING wear_count",
            (item_id, uid),
        )
        row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Item not found"}), 404
    return jsonify({"message": "Wear logged", "wear_count": row[0]})


# ── AI ─────────────────────────────────────────────────────────────

@app.route("/api/ai-analysis", methods=["GET"])
@login_required
def api_ai_analysis():
    uid = session["user_id"]
    try:
        recommendations = ai_engine.generate_insights(uid)
        return jsonify(_safe_json({"insights": recommendations}))
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        return jsonify({"error": "Could not generate insights at this time."}), 500


# ── Run ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))