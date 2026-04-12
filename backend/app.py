"""
fenora — Flask Backend (app.py)
Drop-in replacement: adds missing APIs, fixes response shapes expected by new frontend.
"""
import os
from dotenv import load_dotenv
load_dotenv(override=True)

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

import os
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_DOMAIN'] = None

CORS(app,
     origins=["https://spendwise-beryl-six.vercel.app",
               "http://localhost:5173"],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

@app.route('/api/health')
def health():
    return {"status": "ok", "message": "Spendwise backend is live"}, 200

@app.route("/")
def index():
    return jsonify({
        "status": "online",
        "message": "fenora API is running! 🚀",
        "frontend": os.environ.get("FRONTEND_URL", "https://spendwise-beryl-six.vercel.app")
    })

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

def create_tables():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                password_hash VARCHAR(256) NOT NULL,
                age INTEGER,
                gender VARCHAR(20),
                is_admin BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT now(),
                monthly_budget DOUBLE PRECISION,
                email_reminders_enabled BOOLEAN DEFAULT true,
                email_frequency VARCHAR(10) DEFAULT 'monthly',
                reset_token VARCHAR(255),
                reset_token_expiry TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                amount DOUBLE PRECISION NOT NULL,
                category VARCHAR(50) DEFAULT 'Others' NOT NULL,
                expense_month INTEGER NOT NULL,
                expense_year INTEGER NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT now(),
                mood VARCHAR(20)
            );
            CREATE TABLE IF NOT EXISTS budgets (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                amount DOUBLE PRECISION DEFAULT 0 NOT NULL,
                created_at TIMESTAMP DEFAULT now(),
                UNIQUE(user_id, month, year)
            );
            CREATE TABLE IF NOT EXISTS goals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                goal_name VARCHAR(100) NOT NULL,
                target_amount DOUBLE PRECISION NOT NULL,
                saved_amount DOUBLE PRECISION DEFAULT 0,
                deadline DATE,
                created_at TIMESTAMP DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS savings_goals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                name VARCHAR(200) NOT NULL,
                target_amount NUMERIC(12,2) NOT NULL,
                saved_amount NUMERIC(12,2) DEFAULT 0,
                months INTEGER DEFAULT 6,
                created_at TIMESTAMP DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS category_budgets (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                category VARCHAR(100) NOT NULL,
                cap_amount NUMERIC(12,2) NOT NULL,
                created_at TIMESTAMP DEFAULT now(),
                UNIQUE(user_id, category)
            );
            CREATE TABLE IF NOT EXISTS daily_limits (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                daily_limit NUMERIC(10,2),
                date DATE DEFAULT CURRENT_DATE
            );
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS email_log (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                subject VARCHAR(200),
                sent_at TIMESTAMP DEFAULT now(),
                status VARCHAR(20)
            );
            CREATE TABLE IF NOT EXISTS ml_predictions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                predicted_spending DOUBLE PRECISION,
                risk_category VARCHAR(20),
                budget_ratio DOUBLE PRECISION,
                monthly_budget DOUBLE PRECISION,
                alerts JSONB,
                reminders JSONB,
                predicted_at TIMESTAMP DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS survey_responses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                wardrobe_size INTEGER,
                average_decision_time DOUBLE PRECISION,
                monthly_budget DOUBLE PRECISION,
                monthly_spending DOUBLE PRECISION,
                repeat_frequency VARCHAR(50),
                created_at TIMESTAMP DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS wardrobe_items (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                item_name VARCHAR(100),
                category VARCHAR(50),
                color VARCHAR(50),
                purchase_price DOUBLE PRECISION,
                purchase_date DATE,
                wear_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT now(),
                purchase_month VARCHAR(10),
                last_worn DATE,
                tags VARCHAR(255)
            );
            CREATE TABLE IF NOT EXISTS outfit_decisions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                decision_time DOUBLE PRECISION,
                date DATE DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS outfit_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                items JSONB DEFAULT '[]' NOT NULL,
                note TEXT,
                worn_date DATE DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT now()
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("[INFO] All tables created successfully")
    except Exception as e:
        print(f"[ERROR] Table creation failed: {e}")

create_tables()


def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if request.method == "OPTIONS":
            return f(*a, **kw)
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        token = auth_header.split(" ")[1]
        try:
            import jwt
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except Exception as e:
            return jsonify({"error": "Invalid or expired token"}), 401
        return f(*a, **kw)
    return dec


def get_uid():
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            import jwt
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            return data["user_id"]
        except:
            pass
    return 1


# ─── Auth ─────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    pwd = data.get("password", "")
    budget_raw = data.get("monthly_budget") or data.get("budget")
    budget = float(budget_raw) if budget_raw else None

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
        import jwt
        token = jwt.encode({
            "user_id": uid,
            "exp": datetime.utcnow() + timedelta(days=7)
        }, app.config["SECRET_KEY"], algorithm="HS256")
        
        return jsonify({
            "message": f"Welcome {name}!",
            "user": {"id": uid, "name": name, "email": email},
            "user_id": uid, "name": name, "budget": budget,
            "token": token
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
        import jwt
        token = jwt.encode({
            "user_id": user["id"],
            "exp": datetime.utcnow() + timedelta(days=7)
        }, app.config["SECRET_KEY"], algorithm="HS256")
        
        return jsonify({
            "message": f"Welcome back, {user['name']}!",
            "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
            "user_id": user["id"], "name": user["name"],
            "budget": float(user.get("monthly_budget") or 0),
            "token": token
        })
    return jsonify({"error": "Invalid email or password."}), 401


@app.route("/api/check-auth", methods=["GET"])
def api_check_auth():
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            import jwt
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            conn = get_db()
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, email FROM users WHERE id=%s", (data["user_id"],))
                u = cur.fetchone()
            conn.close()
            if u:
                return jsonify({"authenticated": True, "user": {"id": u[0], "name": u[1], "email": u[2]}})
        except:
            pass
    return jsonify({"authenticated": False}), 401


@app.route("/api/logout", methods=["POST"])
def api_logout():
    return jsonify({"message": "Logged out successfully"})

@app.route("/api/budget", methods=["GET"])
@login_required
def api_get_budget():
    uid = get_uid()
    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT monthly_budget FROM users WHERE id=%s", (uid,))
        user = cur.fetchone()
    conn.close()
    
    if not user or user.get("monthly_budget") is None:
        return jsonify({"budget": None, "message": "No budget set"})
    return jsonify({"budget": float(user["monthly_budget"])})

@app.route("/api/budget/update", methods=["PUT"])
@login_required
def api_update_budget():
    uid = get_uid()
    data = request.json or {}
    new_raw = data.get("budget")
    new_budget = float(new_raw) if new_raw is not None and new_raw != "" else None
    
    if new_budget is not None and new_budget < 0:
        return jsonify({"error": "Budget must be positive"}), 400

    conn = get_db()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("UPDATE users SET monthly_budget = %s WHERE id = %s", (new_budget, uid))
        conn.close()
        return jsonify({"message": "Budget updated successfully", "budget": new_budget})
    except Exception as e:
        logger.error(f"Error updating budget: {e}")
        return jsonify({"error": "Database update failed"}), 500

import uuid
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@app.route("/api/auth/forgot-password", methods=["POST", "OPTIONS"])
def api_forgot_password():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
        
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        
        if user:
            import uuid
            token = str(uuid.uuid4())
            expiry = datetime.now() + timedelta(minutes=15)
            
            cur.execute(
                "UPDATE users SET reset_token=%s, reset_token_expiry=%s WHERE id=%s",
                (token, expiry, user["id"])
            )
            conn.commit()
            
            brevo_key = os.getenv("BREVO_API_KEY")
            
            if brevo_key:
                try:
                    import sib_api_v3_sdk
                    from sib_api_v3_sdk.rest import ApiException
                except ImportError:
                    logger.error("sib_api_v3_sdk not installed. Did you update requirements.txt?")
                    return jsonify({"error": "Email SDK not installed on server."}), 500
                    
                try:
                    configuration = sib_api_v3_sdk.Configuration()
                    configuration.api_key['api-key'] = brevo_key
                    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                        sib_api_v3_sdk.ApiClient(configuration)
                    )
                    reset_link = f"{os.getenv('FRONTEND_URL', 'https://spendwise-beryl-six.vercel.app')}/reset-password?token={token}"
                    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                        to=[{"email": email}],
                        sender={"name": "Fenora", "email": "cloudberryyohh@gmail.com"},
                        subject="Reset Your Fenora Password",
                        html_content=f"<p>Click here to reset: <a href='{reset_link}'>{reset_link}</a></p>"
                    )
                    api_response = api_instance.send_transac_email(send_smtp_email)
                    logger.info(f"Brevo API response: {api_response}")
                except ApiException as e:
                    logger.error(f"Brevo ApiException Status: {e.status}, Reason: {e.reason}, Body: {e.body}")
                    return jsonify({"error": f"Email service failure: {e.reason}", "details": e.body}), 500
                except Exception as _e:
                    logger.error(f"Render Brevo API general error: {_e}")
                    return jsonify({"error": f"Failed to send reset email: {str(_e)}"}), 500
            else:
                logger.warning("BREVO_API_KEY not set. Cannot send reset email.")
                return jsonify({"error": "Email service not configured (missing key)."}), 500
                
        cur.close()
        conn.close()
        
        return jsonify({"message": "If an account with that email exists, we have sent a password reset link."})
        
    except Exception as e:
        print("Reset error:", e)
        logger.error(f"Forgot password error: {e}")
        return jsonify({"error": "Failed to handle password reset"}), 500

@app.route("/api/auth/reset-password", methods=["POST", "OPTIONS"])
def api_reset_password():
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
    data = request.json or {}
    token = data.get("token")
    pwd = data.get("password", "")
    
    if not token or not pwd:
        return jsonify({"error": "Token and password are required"}), 400
        
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute(
            "SELECT id FROM users WHERE reset_token=%s AND reset_token_expiry > NOW()",
            (token,)
        )
        user = cur.fetchone()
        
        if not user:
            cur.close()
            conn.close()
            return jsonify({"error": "Invalid or expired token"}), 400
            
        hashed = generate_password_hash(pwd)
        cur.execute(
            "UPDATE users SET password_hash=%s, reset_token=NULL, reset_token_expiry=NULL WHERE id=%s",
            (hashed, user["id"])
        )
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"message": "Password updated successfully"})
        
    except Exception as e:
        print("Reset error:", e)
        logger.error(f"Reset password error: {e}")
        return jsonify({"error": "Failed to reset password"}), 500

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


@app.route("/api/expenses/calendar", methods=["GET"])
@login_required
def api_expenses_calendar():
    uid = get_uid()
    year = request.args.get("year", datetime.now().year, type=int)
    month = request.args.get("month", datetime.now().month, type=int)
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT DATE(created_at) as date, COALESCE(SUM(amount),0) as amount FROM expenses "
                "WHERE user_id=%s AND EXTRACT(YEAR FROM created_at)=%s AND EXTRACT(MONTH FROM created_at)=%s "
                "GROUP BY DATE(created_at) ORDER BY date",
                (uid, year, month)
            )
            rows = [{"date": str(r["date"]), "amount": _f(r["amount"])} for r in cur.fetchall()]
    finally:
        conn.close()
    return jsonify(rows)


@app.route("/api/expenses", methods=["POST", "OPTIONS"])
@login_required
def api_expenses_post():
    if request.method == "OPTIONS":
        return "", 200

    uid = get_uid()
    data = request.json or {}
    amount = float(data.get("amount", 0) or 0)
    category = data.get("category", "Others")
    note = data.get("note", "")

    if amount <= 0:
        return jsonify({"error": "Amount must be > 0"}), 400

    conn = get_db()
    with conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        today = datetime.now()
        
        # Grab current budget / total spent info for alerts
        cur.execute("SELECT email, monthly_budget FROM users WHERE id=%s", (uid,))
        user_row = cur.fetchone()
        budget = _f(user_row["monthly_budget"] if user_row else 0)
        user_email = user_row["email"] if user_row else None
        
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses WHERE user_id=%s "
            "AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s",
            (uid, today.month, today.year)
        )
        spent_row = cur.fetchone()
        prev_spent = _f(spent_row["t"] if spent_row else 0)

        # Insert expense
        cur.execute("BEGIN;") # Start subtransaction mentally via context? Already in 'with conn'
        try:
            cur.execute(
                "INSERT INTO expenses(user_id, amount, category, note) "
                "VALUES(%s,%s,%s,%s) RETURNING id",
                (uid, amount, category, note),
            )
        except Exception:
            conn.rollback()
            try:
                cur.execute(
                    "INSERT INTO expenses(user_id, amount, category, note) "
                    "VALUES(%s,%s,%s,%s) RETURNING id",
                    (uid, amount, category, note),
                )
            except Exception:
                conn.rollback()
                cur.execute(
                    "INSERT INTO expenses(user_id, amount, category, note, expense_month, expense_year) "
                    "VALUES(%s,%s,%s,%s,%s,%s) RETURNING id",
                    (uid, amount, category, note, today.month, today.year),
                )
        eid = cur.fetchone()["id"]
        conn.commit()

    # Budget Trigger Alert
    new_spent = prev_spent + amount
    if budget > 0 and user_email:
        trigger_level = None
        if prev_spent < 0.5 * budget <= new_spent: trigger_level = "50%"
        elif prev_spent < 0.8 * budget <= new_spent: trigger_level = "80%"
        elif prev_spent <= 1.0 * budget < new_spent: trigger_level = "100%"
        
        if trigger_level:
            import threading
            def send_alert_email(to_email, level, spent_amount, monthly_budget):
                try:
                    brevo_key = os.getenv("BREVO_API_KEY")
                    if not brevo_key: return
                    subj = f"⚠️ Budget Alert: {level} Limit Reached" if level != "100%" else "🚨 Budget Exceeded: 100% Limit Reached"
                    body = f"Hello,\n\nYou have hit the {level} mark of your monthly budget.\nTotal Spent this month: ₹{spent_amount:,.0f}\nMonthly Budget: ₹{monthly_budget:,.0f}\n\nReview your expenses in Fenora.\n\n- The Fenora Team"
                    
                    import sib_api_v3_sdk
                    from sib_api_v3_sdk.rest import ApiException
                    configuration = sib_api_v3_sdk.Configuration()
                    configuration.api_key['api-key'] = brevo_key
                    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
                    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                        to=[{"email": to_email}],
                        sender={"name": "Fenora", "email": "cloudberryyohh@gmail.com"},
                        subject=subj,
                        html_content=body.replace('\n', '<br>')
                    )
                    api_instance.send_transac_email(send_smtp_email)
                except Exception as e:
                    logger.error(f"Failed to send alert email: {e}")
            threading.Thread(target=send_alert_email, args=(user_email, trigger_level, new_spent, budget)).start()

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
def api_update_budget_legacy():
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



import re
import calendar as cal_module

# ─────────────────────────────────────────────────────────────────────
# FIX 1 — AI CHAT (dynamic, free-text, data-driven)
# Replace the existing /api/chat route entirely.
# ─────────────────────────────────────────────────────────────────────

@app.route("/api/smart-chat", methods=["POST"])
@login_required
def api_smart_chat():
    """
    Fully dynamic AI chat — understands free-text questions and
    answers with real user data. No more generic responses.

    Accepted JSON: { "message": "Can I afford ₹2000?" }
    Returns:       { "reply": "...", "data": {...} }
    """
    uid = get_uid()
    data = request.json or {}
    message = (data.get("message") or data.get("question_key") or "").strip().lower()

    if not message:
        return jsonify({"reply": "What would you like to know about your finances?"}), 400

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        today = datetime.now()

        # ── Fetch all user data ────────────────────────────────────
        cur.execute("SELECT monthly_budget, name FROM users WHERE id=%s", (uid,))
        u = cur.fetchone()
        budget = _f(u["monthly_budget"] if u else 0)
        name = (u.get("name") or "there").split()[0] if u else "there"

        # This month spending
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
            "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s",
            (uid, today.month, today.year),
        )
        spent = _f(cur.fetchone()["t"])
        remaining = max(0.0, budget - spent)
        budget_pct = (spent / budget * 100) if budget > 0 else 0

        # Category breakdown this month
        cur.execute(
            "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
            "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s "
            "GROUP BY category ORDER BY total DESC",
            (uid, today.month, today.year),
        )
        cats = {r["category"]: _f(r["total"]) for r in cur.fetchall()}
        top_cat = max(cats.items(), key=lambda x: x[1]) if cats else None

        # Last month
        last_m = today.replace(day=1) - timedelta(days=1)
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
            "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s",
            (uid, last_m.month, last_m.year),
        )
        last_month_spent = _f(cur.fetchone()["t"])

        # Wardrobe
        cur.execute("SELECT COUNT(*) AS c FROM wardrobe_items WHERE user_id=%s AND wear_count=0", (uid,))
        never_worn = int(cur.fetchone()["c"])

        # Last 7 days
        week_start = today - timedelta(days=7)
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
            "WHERE user_id=%s AND created_at >= %s",
            (uid, week_start),
        )
        week_spent = _f(cur.fetchone()["t"])


        # Savings goals
        cur.execute(
            "SELECT * FROM savings_goals WHERE user_id=%s ORDER BY created_at DESC LIMIT 3",
            (uid,),
        )
        goals = cur.fetchall()

        cur.close()
        conn.close()

        # ── Intent detection + reply ───────────────────────────────

        # Extract rupee amount from message (e.g. "2000", "₹2000", "2,000")
        amount_match = re.search(r"[₹rs\s]?\s*(\d[\d,]*)", message.replace(",", ""))
        asked_amount = float(amount_match.group(1).replace(",", "")) if amount_match else 0

        reply = ""
        ctx = {
            "budget": budget, "spent": spent, "remaining": remaining,
            "budget_pct": budget_pct, "week_spent": week_spent,
        }

        # ── AFFORD CHECK ──────────────────────────────────────────
        if any(w in message for w in ["afford", "can i buy", "should i buy", "worth buying", "is it okay to buy"]):
            if asked_amount > 0:
                if asked_amount <= remaining:
                    pct_of_remaining = (asked_amount / remaining * 100) if remaining > 0 else 100
                    if pct_of_remaining > 60:
                        reply = (
                            f"Technically yes — ₹{asked_amount:,.0f} fits in your remaining ₹{remaining:,.0f}, "
                            f"but it would use {pct_of_remaining:.0f}% of what you have left. "
                            f"You've already spent {budget_pct:.0f}% of your ₹{budget:,.0f} budget. "
                            f"I'd wait unless it's essential. 🤔"
                        )
                    else:
                        reply = (
                            f"✅ Yes, you can afford ₹{asked_amount:,.0f}! "
                            f"You have ₹{remaining:,.0f} left from your ₹{budget:,.0f} budget "
                            f"({100 - budget_pct:.0f}% remaining). "
                            f"This would bring you to {((spent + asked_amount) / budget * 100):.0f}% used — still okay."
                        )
                else:
                    short = asked_amount - remaining
                    reply = (
                        f"❌ Not recommended. ₹{asked_amount:,.0f} is more than your remaining budget of ₹{remaining:,.0f}. "
                        f"You'd overspend by ₹{short:,.0f}. "
                        f"You've already used {budget_pct:.0f}% of your ₹{budget:,.0f} budget this month."
                    )
            else:
                # Generic afford check
                if remaining > 2000:
                    reply = f"You have ₹{remaining:,.0f} left in your budget ({100 - budget_pct:.0f}% unused). You have decent room, but mention a specific amount for a precise answer!"
                else:
                    reply = f"⚠️ Your budget is tight — only ₹{remaining:,.0f} left ({100 - budget_pct:.0f}% of ₹{budget:,.0f}). Be careful with purchases this month."

        # ── CLOTHES / WARDROBE ────────────────────────────────────
        elif any(w in message for w in ["clothes", "clothing", "wardrobe", "outfit", "shirt", "dress", "jacket", "jeans", "shoes", "kurta", "saree"]):
            shopping_spent = cats.get("Shopping", 0)
            if never_worn >= 3:
                reply = (
                    f"👗 Hold on — you already have {never_worn} unworn items in your wardrobe! "
                    f"That's money not being used. "
                    + (f"You've also spent ₹{shopping_spent:,.0f} on shopping this month. " if shopping_spent > 0 else "")
                    + "Challenge: wear something you haven't in 30 days before buying anything new."
                )
            elif shopping_spent > 2000:
                reply = (
                    f"You've already spent ₹{shopping_spent:,.0f} on shopping this month. "
                    f"With ₹{remaining:,.0f} left in your budget, I'd think twice before adding more. "
                    f"Do you actually need it, or just want it right now? 😅"
                )
            elif remaining > asked_amount and asked_amount > 0:
                reply = f"You have ₹{remaining:,.0f} left, so ₹{asked_amount:,.0f} on clothes is affordable. Just make sure it gets worn — {never_worn} items already sit unworn in your wardrobe!"
            else:
                reply = f"You have ₹{remaining:,.0f} remaining this month. If you've been eyeing something, just make sure you'll actually wear it — your wardrobe utilization can always improve! 👕"

        # ── FOOD / DELIVERY ────────────────────────────────────────
        elif any(w in message for w in ["food", "swiggy", "zomato", "delivery", "restaurant", "eating", "eat out"]):
            food_spent = cats.get("Food", 0)
            if food_spent > 0:
                food_pct = (food_spent / spent * 100) if spent > 0 else 0
                save_potential = int(food_spent * 0.3)
                reply = (
                    f"🍱 You've spent ₹{food_spent:,.0f} on food this month ({food_pct:.0f}% of your total). "
                    f"Cooking at home 3 extra days/week could save you about ₹{save_potential:,}. "
                    f"Try packing lunch on weekdays — saves ₹150–250/day easily."
                )
            else:
                reply = "No food expenses logged yet this month. Start tracking your food spending to get personalised insights!"

        # ── BUDGET STATUS ─────────────────────────────────────────
        elif any(w in message for w in ["budget", "how much left", "remaining", "left", "how am i doing", "status"]):
            if budget == 0:
                reply = "You haven't set a monthly budget yet! Set one from your dashboard to start tracking properly."
            elif budget_pct >= 90:
                reply = (
                    f"🚨 Budget critically low! You've spent ₹{spent:,.0f} ({budget_pct:.0f}%) of your ₹{budget:,.0f} budget. "
                    f"Only ₹{remaining:,.0f} left. Avoid all non-essential spending for the rest of the month."
                )
            elif budget_pct >= 70:
                reply = (
                    f"⚠️ Budget getting tight — {budget_pct:.0f}% used (₹{spent:,.0f} of ₹{budget:,.0f}). "
                    f"₹{remaining:,.0f} left. "
                    + (f"Your biggest expense is {top_cat[0]} (₹{top_cat[1]:,.0f}). Try cutting that next." if top_cat else "")
                )
            else:
                days_left = cal_module.monthrange(today.year, today.month)[1] - today.day
                daily_budget = remaining / max(days_left, 1)
                reply = (
                    f"✅ Budget looks healthy! You've spent {budget_pct:.0f}% (₹{spent:,.0f}) of ₹{budget:,.0f}. "
                    f"₹{remaining:,.0f} left with {days_left} days to go — about ₹{daily_budget:,.0f}/day."
                )

        # ── SPENDING ANALYSIS ─────────────────────────────────────
        elif any(w in message for w in ["spending", "spend", "expenses", "where", "analysis", "breakdown"]):
            if not cats:
                reply = "No expenses logged this month yet. Start tracking to see where your money goes!"
            else:
                top3 = sorted(cats.items(), key=lambda x: -x[1])[:3]
                breakdown = ", ".join(f"{c}: ₹{v:,.0f}" for c, v in top3)
                mom_change = ((spent - last_month_spent) / last_month_spent * 100) if last_month_spent > 0 else 0
                trend = f"📈 +{mom_change:.0f}% vs last month" if mom_change > 10 else (f"📉 {mom_change:.0f}% vs last month" if mom_change < -5 else "~same as last month")
                reply = (
                    f"📊 This month: ₹{spent:,.0f} total ({budget_pct:.0f}% of budget). "
                    f"Top categories — {breakdown}. "
                    f"Trend: {trend}."
                )

        # ── SAVINGS / HOW TO SAVE ─────────────────────────────────
        elif any(w in message for w in ["save", "saving", "savings", "how to save", "cut", "reduce"]):
            tips = []
            if cats.get("Food", 0) > 2000:
                tips.append(f"Cut food delivery by 25% → save ~₹{int(cats['Food'] * 0.25):,}/month")
            if cats.get("Shopping", 0) > 1500:
                tips.append(f"Pause shopping for 2 weeks → save ₹{int(cats.get('Shopping', 0)):,} this month")
            if remaining > 0:
                tips.append(f"Move ₹{int(remaining * 0.5):,} of your remaining budget to savings before month-end")
            if not tips:
                daily_save = int(remaining / max((cal_module.monthrange(today.year, today.month)[1] - today.day), 1))
                tips.append(f"You're tracking well. Try setting a savings goal and put aside ₹{daily_save:,}/day")
            reply = "💰 Here's how to save more this month:\n" + "\n".join(f"• {t}" for t in tips)

        # ── WEEKLY SUMMARY ────────────────────────────────────────
        elif any(w in message for w in ["week", "this week", "weekly", "past 7 days", "last 7"]):
            if week_spent == 0:
                reply = "No expenses in the past 7 days. Either you've been great with money, or you forgot to log! 😄"
            else:
                daily_avg = week_spent / 7
                reply = (
                    f"📅 Last 7 days: ₹{week_spent:,.0f} spent (avg ₹{daily_avg:,.0f}/day). "
                    + (f"Your budget allows ₹{budget / 30:,.0f}/day on average. " if budget > 0 else "")
                    + ("You're pacing well! 🟢" if budget > 0 and daily_avg <= budget / 30 else "Consider slowing down this week. 🔴" if budget > 0 else "")
                )

        # ── OMITTED MOOD SPENDING (Schema updated) ────────────────
        # ── GOALS ─────────────────────────────────────────────────
        elif any(w in message for w in ["goal", "goals", "target", "save for", "saving for"]):
            if not goals:
                reply = "You haven't set any savings goals yet! Go to your dashboard and create one — whether it's a trip, gadget, or emergency fund. Having a goal makes saving 3x more effective. 🎯"
            else:
                g = goals[0]  # Most recent goal
                target = _f(g.get("target_amount"))
                saved = _f(g.get("saved_amount"))
                months_left = max(int(g.get("months") or 1), 1)
                remaining_amt = target - saved
                monthly_needed = remaining_amt / months_left if months_left > 0 else remaining_amt
                daily_needed = monthly_needed / 30
                pct_done = (saved / target * 100) if target > 0 else 0
                reply = (
                    f"🎯 Goal: '{g['name']}' — ₹{target:,.0f} target. "
                    f"Progress: ₹{saved:,.0f} saved ({pct_done:.0f}%). "
                    f"To finish in {months_left} month{'s' if months_left > 1 else ''}: "
                    f"save ₹{monthly_needed:,.0f}/month or ₹{daily_needed:,.0f}/day."
                )

        # ── DEFAULT (smart fallback) ───────────────────────────────
        else:
            if budget == 0:
                reply = "Set a monthly budget first to get personalised advice. Once you do, I can answer questions like 'can I afford X?' or 'how's my spending?'"
            elif budget_pct >= 80:
                reply = (
                    f"Quick heads up: you've spent {budget_pct:.0f}% of your ₹{budget:,.0f} budget this month. "
                    f"₹{remaining:,.0f} left. "
                    + (f"Top spend: {top_cat[0]} (₹{top_cat[1]:,.0f}). " if top_cat else "")
                    + "Try asking: 'Can I afford ₹X?' or 'How to save more?'"
                )
            else:
                reply = (
                    f"Budget: ₹{spent:,.0f} / ₹{budget:,.0f} used ({budget_pct:.0f}%). ₹{remaining:,.0f} remaining. "
                    + (f"Top category: {top_cat[0]} (₹{top_cat[1]:,.0f}). " if top_cat else "")
                    + "Ask me anything — 'Can I afford ₹2000?', 'Where am I spending most?', 'How to save?'"
                )

        return jsonify({"reply": reply, "data": ctx})

    except Exception as e:
        import traceback
        print("Chat trace:", traceback.format_exc())
        logger.error(f"Smart chat error: {e}")
        return jsonify({"error": str(e)}), 500

# ─────────────────────────────────────────────────────────────────────
# FIX 2 — SAVINGS GOALS with daily/monthly calculation
# This REPLACES the existing /api/savings-goals GET to add calculations.
# ─────────────────────────────────────────────────────────────────────

@app.route("/api/savings-goals/calculated", methods=["GET"])
@login_required
def api_savings_goals_calculated():
    """
    Returns all savings goals with real-time calculations:
    - remaining_amount
    - monthly_saving_needed
    - daily_saving_needed
    - progress_pct
    - on_track (bool)
    """
    uid = get_uid()
    today = datetime.now()

    try:
        conn = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM savings_goals WHERE user_id=%s ORDER BY created_at DESC",
                (uid,),
            )
            raw_goals = cur.fetchall()

            # Get monthly remaining budget for "on track" check
            cur.execute("SELECT monthly_budget FROM users WHERE id=%s", (uid,))
            u = cur.fetchone()
            budget = _f(u["monthly_budget"] if u else 0)

            cur.execute(
                "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
                "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s",
                (uid, today.month, today.year),
            )
            spent = _f(cur.fetchone()["t"])
        conn.close()
    except Exception as e:
        logger.error(f"Savings goals calculated error: {e}")
        return jsonify([])

    remaining_budget = max(0.0, budget - spent)
    goals_out = []

    for g in raw_goals:
        target = _f(g.get("target_amount"))
        saved = _f(g.get("saved_amount"))
        months = max(int(g.get("months") or 1), 1)
        remaining_amt = max(0.0, target - saved)
        progress_pct = round((saved / target * 100), 1) if target > 0 else 0

        # Calculate how many months remain from creation date
        created_at = g.get("created_at")
        if created_at:
            if hasattr(created_at, "year"):
                months_elapsed = (today.year - created_at.year) * 12 + (today.month - created_at.month)
            else:
                months_elapsed = 0
        else:
            months_elapsed = 0

        months_remaining = max(1, months - months_elapsed)
        monthly_needed = round(remaining_amt / months_remaining, 2)
        daily_needed = round(monthly_needed / 30, 2)

        # Is user on track? Monthly needed vs available monthly surplus
        monthly_surplus = remaining_budget  # This month's remaining budget
        on_track = monthly_needed <= monthly_surplus if monthly_needed > 0 else True

        goals_out.append(_safe_json({
            **dict(g),
            "remaining_amount": remaining_amt,
            "monthly_saving_needed": monthly_needed,
            "daily_saving_needed": daily_needed,
            "progress_pct": progress_pct,
            "months_remaining": months_remaining,
            "on_track": on_track,
            "tip": (
                f"Save ₹{monthly_needed:,.0f}/month (₹{daily_needed:,.0f}/day) to hit your goal in {months_remaining} month{'s' if months_remaining > 1 else ''}."
                if remaining_amt > 0 else "🎉 Goal achieved! You've hit your target."
            )
        }))

    return jsonify(goals_out)


# ─────────────────────────────────────────────────────────────────────
# FIX 3 — MOOD TRACKING (store + analyse)
# ─────────────────────────────────────────────────────────────────────

@app.route("/api/mood-analytics", methods=["GET"])
@login_required
def api_mood_analytics():
    """
    Returns mood-wise spending totals + insight message.
    Frontend: GET /api/mood-analytics
    """
    uid = get_uid()
    today = datetime.now()

    try:
        conn = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT mood, COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt "
                "FROM expenses "
                "WHERE user_id=%s AND mood IS NOT NULL AND mood != '' "
                "AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s "
                "GROUP BY mood ORDER BY total DESC",
                (uid, today.month, today.year),
            )
            rows = cur.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"Mood analytics error: {e}")
        return jsonify({"mood_totals": {}, "insight": "Add mood tags to see patterns.", "entries": []})

    if not rows:
        return jsonify({
            "mood_totals": {},
            "insight": "No mood-tagged expenses yet. Add mood to your expenses to see patterns!",
            "entries": [],
        })

    mood_totals = {r["mood"]: _f(r["total"]) for r in rows}
    mood_counts = {r["mood"]: int(r["cnt"]) for r in rows}
    total_tagged = sum(mood_totals.values())

    # Build insight
    worst_mood = max(mood_totals.items(), key=lambda x: x[1])
    best_mood = min(mood_totals.items(), key=lambda x: x[1])
    insight = ""

    if worst_mood[0] in ("stressed", "sad") and worst_mood[1] > 0:
        pct = (worst_mood[1] / total_tagged * 100) if total_tagged > 0 else 0
        insight = (
            f"⚠️ You spend the most when {worst_mood[0]} — ₹{worst_mood[1]:,.0f} ({pct:.0f}% of mood-tagged). "
            "Try a 10-min pause before buying when you're feeling this way."
        )
    elif worst_mood[0] == "happy":
        insight = (
            f"😊 You spend most when happy (₹{worst_mood[1]:,.0f}) — usually fine, just avoid impulse buys! "
            "Your mood spending looks balanced overall."
        )
    elif worst_mood[0] == "excited":
        insight = f"🤩 Excitement drives your spending (₹{worst_mood[1]:,.0f}). Sleep on purchases over ₹500 before buying."
    else:
        insight = f"Your mood spending data is building up. Keep tagging to see clearer patterns!"

    return jsonify({
        "mood_totals": mood_totals,
        "mood_counts": mood_counts,
        "insight": insight,
        "entries": [_safe_json(dict(r)) for r in rows],
    })


# ─────────────────────────────────────────────────────────────────────
# FIX 4 — WEEKLY SUMMARY (fixed date query)
# ─────────────────────────────────────────────────────────────────────

@app.route("/api/weekly-summary", methods=["GET"])
@login_required
def api_weekly_summary():
    """
    Returns this week vs last week spending with correct date filtering.
    Frontend: GET /api/weekly-summary
    """
    uid = get_uid()
    today = datetime.now()

    # This week: last 7 days
    this_week_start = today - timedelta(days=7)
    # Last week: 8–14 days ago
    last_week_start = today - timedelta(days=14)
    last_week_end = today - timedelta(days=7)

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # This week total
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS t FROM expenses "
            "WHERE user_id=%s AND created_at >= %s",
            (uid, this_week_start),
        )
        this_week_total = _f(cur.fetchone()["t"])

        # Last week total
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS t FROM expenses "
            "WHERE user_id=%s AND created_at >= %s AND created_at < %s",
            (uid, last_week_start, last_week_end),
        )
        last_week_total = _f(cur.fetchone()["t"])

        # This week by category
        cur.execute(
            "SELECT category, COALESCE(SUM(amount), 0) AS total FROM expenses "
            "WHERE user_id=%s AND created_at >= %s "
            "GROUP BY category ORDER BY total DESC",
            (uid, this_week_start),
        )
        this_week_cats = {r["category"]: _f(r["total"]) for r in cur.fetchall()}

        # Daily breakdown for chart
        daily = {}
        for i in range(7):
            d = today - timedelta(days=6 - i)
            day_key = d.strftime("%a")
            cur.execute(
                "SELECT COALESCE(SUM(amount), 0) AS t FROM expenses "
                "WHERE user_id=%s AND DATE(created_at) = %s",
                (uid, d.date()),
            )
            daily[day_key] = _f(cur.fetchone()["t"])

        # Budget context
        cur.execute("SELECT monthly_budget FROM users WHERE id=%s", (uid,))
        u = cur.fetchone()
        budget = _f(u["monthly_budget"] if u else 0)
        weekly_budget = budget / 4.33 if budget > 0 else 0

        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Weekly summary error: {e}")
        return jsonify({
            "this_week": 0, "last_week": 0, "change_pct": 0,
            "daily": {}, "categories": {}, "weekly_budget": 0,
            "message": f"Error: {str(e)}"
        })

    # Change calculation
    change_pct = 0
    if last_week_total > 0:
        change_pct = round(((this_week_total - last_week_total) / last_week_total) * 100, 1)

    daily_avg = this_week_total / 7

    # Build message
    if this_week_total == 0:
        message = "No expenses logged in the past 7 days. Start logging to see insights!"
    elif weekly_budget > 0 and this_week_total > weekly_budget:
        message = f"⚠️ You've spent ₹{this_week_total:,.0f} this week — over your estimated weekly budget of ₹{weekly_budget:,.0f}."
    elif change_pct > 20:
        message = f"📈 Spending up {change_pct:.0f}% vs last week (₹{this_week_total:,.0f} vs ₹{last_week_total:,.0f}). What happened?"
    elif change_pct < -10:
        message = f"📉 Great job! You spent {abs(change_pct):.0f}% less than last week. Saved ₹{last_week_total - this_week_total:,.0f}!"
    else:
        message = f"Spending ₹{this_week_total:,.0f} this week (avg ₹{daily_avg:,.0f}/day). {'On track! ✅' if weekly_budget == 0 or this_week_total <= weekly_budget else 'Slightly over pace.'}"

    return jsonify(_safe_json({
        "this_week": this_week_total,
        "last_week": last_week_total,
        "change_pct": change_pct,
        "daily": daily,
        "categories": this_week_cats,
        "weekly_budget": round(weekly_budget, 2),
        "daily_avg": round(daily_avg, 2),
        "message": message,
    }))


# ─────────────────────────────────────────────────────────────────────
# FIX 5 — EMAIL (reads EMAIL_SENDER / EMAIL_PASSWORD correctly)
# This is the /api/test-email fix.
# In email_service.py the env vars are already fixed — this route
# makes /api/test-email also callable from the old chat interface.
# ─────────────────────────────────────────────────────────────────────

@app.route("/api/test-email", methods=["POST"])
@login_required
def api_test_email_direct():
    """
    Direct test-email endpoint that works even without email_service.py.
    Uses EMAIL_SENDER + EMAIL_PASSWORD from .env.
    """
    uid = get_uid()
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT name, email, monthly_budget FROM users WHERE id=%s", (uid,))
            user = cur.fetchone()
            if not user:
                return jsonify({"success": False, "message": "User not found"}), 404

            today = datetime.now()
            cur.execute(
                "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
                "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s",
                (uid, today.month, today.year),
            )
            spent = _f(cur.fetchone()["t"])
            cur.execute(
                "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
                "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s "
                "GROUP BY category ORDER BY total DESC LIMIT 5",
                (uid, today.month, today.year),
            )
            cats = {r["category"]: _f(r["total"]) for r in cur.fetchall()}
        conn.close()
    except Exception as e:
        return jsonify({"success": False, "message": f"DB error: {e}"}), 500

    smtp_user = os.getenv("EMAIL_SENDER") or os.getenv("EMAIL_USER") or os.getenv("MAIL_USERNAME")
    smtp_pass = os.getenv("EMAIL_PASSWORD") or os.getenv("EMAIL_PASS") or os.getenv("MAIL_PASSWORD")

    if not smtp_user or not smtp_pass:
        return jsonify({
            "success": False,
            "message": "Email not configured. Set EMAIL_SENDER and EMAIL_PASSWORD in your .env file.",
            "hint": "Get a Gmail App Password at: myaccount.google.com/apppasswords"
        }), 400

    budget = _f(user["monthly_budget"])
    budget_pct = (spent / budget * 100) if budget > 0 else 0
    remaining = max(0.0, budget - spent)
    first_name = user["name"].split()[0]
    month_name = today.strftime("%B %Y")

    cat_rows = "".join(
        f"<tr><td style='padding:6px 14px;font-size:13px;color:#444;'>{c}</td>"
        f"<td style='padding:6px 14px;font-size:13px;font-weight:700;color:#7c6fa0;text-align:right;'>₹{v:,.0f}</td></tr>"
        for c, v in cats.items()
    ) if cats else "<tr><td colspan='2' style='padding:12px;color:#aaa;text-align:center;font-size:12px;'>No expenses this month</td></tr>"

    status_color = "#e74c3c" if budget_pct >= 90 else "#f39c12" if budget_pct >= 70 else "#27ae60"
    status_emoji = "🚨" if budget_pct >= 90 else "⚠️" if budget_pct >= 70 else "✅"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:20px;background:#f5f3fc;font-family:'Segoe UI',sans-serif;">
<div style="max-width:520px;margin:0 auto;background:#fff;border-radius:18px;overflow:hidden;box-shadow:0 4px 30px rgba(107,95,160,0.12);">
  <div style="background:linear-gradient(135deg,#6b5fa0,#a89cc8);padding:30px;text-align:center;">
    <div style="font-size:11px;color:rgba(255,255,255,0.7);letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">fenora · smart finance</div>
    <h1 style="color:#fff;margin:0;font-size:20px;font-weight:800;">Monthly Snapshot 📊</h1>
    <p style="color:rgba(255,255,255,0.75);margin:6px 0 0;font-size:13px;">Hey {first_name}! Here's your {month_name} summary.</p>
  </div>
  <div style="padding:24px;">
    <div style="background:#f8f5ff;border-left:4px solid {status_color};border-radius:10px;padding:16px 18px;margin-bottom:20px;">
      <div style="font-size:11px;color:#888;text-transform:uppercase;font-weight:600;letter-spacing:0.5px;margin-bottom:6px;">{status_emoji} Budget Status</div>
      <div style="font-size:26px;font-weight:800;color:#1a1a2e;">₹{spent:,.0f}</div>
      <div style="font-size:12px;color:#666;margin-top:4px;">of ₹{budget:,.0f} budget · {budget_pct:.0f}% used · ₹{remaining:,.0f} remaining</div>
      <div style="background:#e8e4f5;border-radius:6px;height:7px;margin-top:10px;overflow:hidden;">
        <div style="background:{status_color};height:7px;width:{min(budget_pct,100):.0f}%;border-radius:6px;"></div>
      </div>
    </div>
    <h3 style="font-size:12px;font-weight:700;color:#7c6fa0;text-transform:uppercase;letter-spacing:0.5px;margin:0 0 10px;">💳 Where Your Money Went</h3>
    <table style="width:100%;border-collapse:collapse;background:#faf8ff;border-radius:10px;overflow:hidden;margin-bottom:20px;">
      <tbody>{cat_rows}</tbody>
    </table>
    <div style="text-align:center;">
      <a href="http://localhost:5173" style="display:inline-block;background:linear-gradient(135deg,#6b5fa0,#a89cc8);color:#fff;padding:12px 28px;border-radius:50px;text-decoration:none;font-size:13px;font-weight:700;">Open Dashboard →</a>
    </div>
  </div>
  <div style="padding:16px;text-align:center;color:#bbb;font-size:11px;">fenora · Smart Budget & Wardrobe Intelligence</div>
</div>
</body></html>"""

    plain = f"fenora Test Email\n\nHi {first_name}!\n\nBudget: ₹{spent:,.0f} / ₹{budget:,.0f} ({budget_pct:.0f}% used)\nRemaining: ₹{remaining:,.0f}\n\n— fenora AI"

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"fenora AI <{smtp_user}>"
        msg["To"] = user["email"]
        msg["Subject"] = f"fenora: Your {month_name} Financial Snapshot 📊"
        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, user["email"], msg.as_string())

        logger.info(f"Test email sent to {user['email']}")
        return jsonify({
            "success": True,
            "message": f"✅ Test email sent to {user['email']}! Check your inbox.",
            "to": user["email"],
            "subject": f"fenora: Your {month_name} Financial Snapshot 📊",
            "insights_summary": {
                "this_month_total": spent,
                "budget_pct": round(budget_pct, 1),
                "expense_insights_count": len(cats),
                "wardrobe_insights_count": 0,
                "recommendations_count": 1,
            }
        })

    except smtplib.SMTPAuthenticationError:
        return jsonify({
            "success": False,
            "message": "❌ Gmail authentication failed. Use a Gmail App Password (not your real password).",
            "hint": "Get one at: myaccount.google.com/apppasswords — requires 2FA to be ON."
        }), 400
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return jsonify({"success": False, "message": f"Email error: {str(e)}"}), 500


# ─────────────────────────────────────────────────────────────────────
# FIX 6 — AI INSIGHTS endpoint with real data (never returns empty)
# Enhanced /api/ai-analysis with more data + mood context
# ─────────────────────────────────────────────────────────────────────

@app.route("/api/ai-insights-full", methods=["GET"])
@login_required
def api_ai_insights_full():
    """
    Comprehensive AI insights that never returns "Could not generate".
    Always returns real, calculated data.
    GET /api/ai-insights-full
    """
    uid = get_uid()
    today = datetime.now()

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Budget
        cur.execute("SELECT monthly_budget FROM users WHERE id=%s", (uid,))
        u = cur.fetchone()
        budget = _f(u["monthly_budget"] if u else 0)

        # This month expenses
        cur.execute(
            "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
            "WHERE user_id=%s AND EXTRACT(YEAR FROM created_at)=%s AND EXTRACT(MONTH FROM created_at)=%s "
            "GROUP BY category ORDER BY total DESC",
            (uid, today.year, today.month),
        )
        this_month_cats = {r["category"]: _f(r["total"]) for r in cur.fetchall()}
        this_month_total = sum(this_month_cats.values())

        # Last month
        last_m = today.replace(day=1) - timedelta(days=1)
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
            "WHERE user_id=%s AND EXTRACT(YEAR FROM created_at)=%s AND EXTRACT(MONTH FROM created_at)=%s",
            (uid, last_m.year, last_m.month),
        )
        last_month_total = _f(cur.fetchone()["t"])

        # Last 7 days
        week_start = today - timedelta(days=7)
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses WHERE user_id=%s AND created_at >= %s",
            (uid, week_start),
        )
        week_total = _f(cur.fetchone()["t"])

        # Wardrobe
        cur.execute("SELECT item_name, category, purchase_price, wear_count FROM wardrobe_items WHERE user_id=%s", (uid,))
        wardrobe = cur.fetchall()

        # Mood
        cur.execute(
            "SELECT mood, COALESCE(SUM(amount),0) AS t FROM expenses "
            "WHERE user_id=%s AND mood IS NOT NULL AND mood != '' "
            "AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s GROUP BY mood",
            (uid, today.month, today.year),
        )
        mood_data = {r["mood"]: _f(r["t"]) for r in cur.fetchall()}

        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"AI insights full error: {e}")
        return jsonify({
            "expense_insights": [{"icon": "⚠️", "type": "info", "text": f"Error loading insights: {str(e)}"}],
            "wardrobe_insights": [],
            "recommendations": [],
            "summary": {},
            "mood_insight": None,
            "weekly_context": {},
        })

    # Build insights
    never_worn = [i for i in wardrobe if (i.get("wear_count") or 0) == 0]
    total_wardrobe_value = sum(_f(i.get("purchase_price")) for i in wardrobe)
    budget_pct = (this_month_total / budget * 100) if budget > 0 else 0
    remaining = max(0.0, budget - this_month_total)
    days_left = cal_module.monthrange(today.year, today.month)[1] - today.day
    daily_remaining = remaining / max(days_left, 1)

    expense_insights = []
    wardrobe_insights = []
    recommendations = []

    # -- Budget insight (always show one) --
    if budget == 0:
        expense_insights.append({"icon": "💡", "type": "info", "text": "Set a monthly budget to start tracking how well you're managing money."})
    elif budget_pct >= 90:
        expense_insights.append({"icon": "🚨", "type": "danger", "text": f"You've used {budget_pct:.0f}% of your ₹{budget:,.0f} budget (₹{this_month_total:,.0f} spent). Only ₹{remaining:,.0f} left — stop non-essential spending NOW."})
    elif budget_pct >= 70:
        expense_insights.append({"icon": "⚠️", "type": "warning", "text": f"You've spent {budget_pct:.0f}% of your budget. ₹{remaining:,.0f} left with {days_left} days to go — about ₹{daily_remaining:,.0f}/day."})
    elif this_month_total > 0:
        expense_insights.append({"icon": "✅", "type": "success", "text": f"Budget on track! Spent {budget_pct:.0f}% (₹{this_month_total:,.0f}). ₹{remaining:,.0f} remaining — avg ₹{daily_remaining:,.0f}/day for {days_left} days."})
    else:
        expense_insights.append({"icon": "💡", "type": "info", "text": "No expenses logged this month yet. Start tracking every purchase!"})

    # -- Top category --
    if this_month_cats:
        top_cat, top_amt = max(this_month_cats.items(), key=lambda x: x[1])
        top_pct = (top_amt / this_month_total * 100) if this_month_total > 0 else 0
        expense_insights.append({"icon": "📊", "type": "info", "text": f"Biggest spend: {top_cat} (₹{top_amt:,.0f}, {top_pct:.0f}% of total). " + ("Consider reducing this category." if top_pct > 40 else "Looks balanced!")})

    # -- Month-over-month --
    if last_month_total > 0 and this_month_total > 0:
        mom = ((this_month_total - last_month_total) / last_month_total) * 100
        if mom > 15:
            expense_insights.append({"icon": "📈", "type": "warning", "text": f"Spending up {mom:.0f}% vs last month. You've spent ₹{this_month_total - last_month_total:,.0f} more. What's driving this?"})
        elif mom < -10:
            expense_insights.append({"icon": "📉", "type": "success", "text": f"Spending down {abs(mom):.0f}% vs last month! You saved ₹{last_month_total - this_month_total:,.0f}. Keep it up 🎉"})

    # -- Weekly context --
    if week_total > 0:
        week_daily = week_total / 7
        expense_insights.append({"icon": "📅", "type": "info", "text": f"Past 7 days: ₹{week_total:,.0f} (avg ₹{week_daily:,.0f}/day). " + ("Slightly high — consider a slower week." if budget > 0 and week_daily > budget / 30 else "Good daily pace!")})

    # -- Mood insight --
    mood_insight = None
    if mood_data:
        stressed = mood_data.get("stressed", 0)
        total_mood = sum(mood_data.values())
        if stressed > 0 and total_mood > 0:
            stress_pct = (stressed / total_mood * 100)
            if stress_pct > 30:
                mood_insight = {"icon": "😤", "type": "warning", "text": f"You spent ₹{stressed:,.0f} ({stress_pct:.0f}%) of mood-tagged expenses when stressed. Pause before buying when feeling this way!"}
            else:
                mood_insight = {"icon": "😊", "type": "success", "text": f"Your mood spending looks healthy. Only {stress_pct:.0f}% of tagged expenses were stress-driven."}

    # -- Wardrobe insights --
    if wardrobe:
        never_worn_val = sum(_f(i.get("purchase_price")) for i in never_worn)
        if never_worn:
            wardrobe_insights.append({"icon": "😴", "type": "warning", "text": f"{len(never_worn)} item{'s' if len(never_worn) > 1 else ''} never worn (₹{never_worn_val:,.0f} idle). Wear them before buying anything new."})
        worn_items = [i for i in wardrobe if (i.get("wear_count") or 0) > 0 and _f(i.get("purchase_price")) > 0]
        if worn_items:
            best = min(worn_items, key=lambda i: _f(i.get("purchase_price")) / max(i.get("wear_count") or 1, 1))
            cpw = _f(best.get("purchase_price")) / max(best.get("wear_count") or 1, 1)
            wardrobe_insights.append({"icon": "⭐", "type": "success", "text": f"Best value: '{best['item_name']}' at ₹{cpw:.0f}/wear. That's efficiency!"})
    else:
        wardrobe_insights.append({"icon": "👗", "type": "info", "text": "Add items to your wardrobe to unlock clothing analytics."})

    # -- Recommendations --
    food_spend = this_month_cats.get("Food", 0)
    if food_spend > 1500:
        recommendations.append({"icon": "🍕", "priority": "high", "title": "Cut food delivery", "text": f"₹{food_spend:,.0f} on food. Cook at home 3x/week → save ~₹{int(food_spend*0.25):,}/month."})

    shopping = this_month_cats.get("Shopping", 0)
    if shopping > 1000 and len(never_worn) >= 2:
        recommendations.append({"icon": "🛍️", "priority": "high", "title": "Pause shopping", "text": f"₹{shopping:,.0f} on shopping + {len(never_worn)} unworn items. Wear what you own first!"})

    if budget_pct > 85:
        recommendations.append({"icon": "🛑", "priority": "high", "title": "No-spend week", "text": f"You've used {budget_pct:.0f}% of budget. Try a 7-day no-spend challenge on non-essentials."})

    if not recommendations and remaining > 500:
        recommendations.append({"icon": "💰", "priority": "success", "title": "Save the surplus", "text": f"You have ₹{remaining:,.0f} left. Move ₹{int(remaining*0.5):,} to a savings goal before month-end!"})

    return jsonify(_safe_json({
        "expense_insights": expense_insights,
        "wardrobe_insights": wardrobe_insights,
        "recommendations": recommendations,
        "mood_insight": mood_insight,
        "summary": {
            "this_month_total": this_month_total,
            "last_month_total": last_month_total,
            "budget": budget,
            "budget_pct": round(budget_pct, 1),
            "remaining": remaining,
            "week_total": week_total,
            "never_worn_count": len(never_worn),
            "total_wardrobe_value": total_wardrobe_value,
            "category_breakdown": this_month_cats,
            "mood_data": mood_data,
        },
        "weekly_context": {
            "total": week_total,
            "daily_avg": round(week_total / 7, 2),
        },
    }))
"""
production_routes.py — fenora Production Routes
=================================================
Paste this entire file's content into app.py BEFORE the
`from email_routes import email_bp` line.

New routes added:
  PUT  /api/wardrobe/<id>          — edit wardrobe item
  GET  /api/expenses/calendar      — spending calendar data
  POST /api/budget/update          — update budget (alias for /api/update-budget)

SQL migrations (run once):
─────────────────────────────────────────────────────────────
-- Already exists but add mood if missing:
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS mood VARCHAR(20) DEFAULT NULL;

-- For wardrobe edit (no migration needed — PUT uses existing columns)
─────────────────────────────────────────────────────────────
"""

# ─────────────────────────────────────────────────────────────────────
# WARDROBE EDIT  —  PUT /api/wardrobe/<id>
# ─────────────────────────────────────────────────────────────────────

@app.route("/api/wardrobe/<int:wid>", methods=["PUT"])
@login_required
def api_wardrobe_update(wid):
    """
    Edit an existing wardrobe item.
    Body: { item_name, category, color, purchase_price }
    """
    uid = get_uid()
    data = request.json or {}
    item_name = data.get("item_name", "").strip()
    if not item_name:
        return jsonify({"error": "Item name required"}), 400

    category       = data.get("category", "Other")
    color          = data.get("color", "")
    purchase_price = float(data.get("purchase_price", 0) or 0)

    try:
        conn = get_db()
        with conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE wardrobe_items "
                "SET item_name=%s, category=%s, color=%s, purchase_price=%s "
                "WHERE id=%s AND user_id=%s "
                "RETURNING id",
                (item_name, category, color, purchase_price, wid, uid),
            )
            row = cur.fetchone()
        conn.close()
        if not row:
            return jsonify({"error": "Item not found or access denied"}), 404
        return jsonify({"message": "Updated", "id": wid})
    except Exception as e:
        logger.error(f"Wardrobe update error: {e}")
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
# SPENDING CALENDAR  —  GET /api/expenses/calendar
# ─────────────────────────────────────────────────────────────────────

@app.route("/api/expenses/calendar", methods=["GET"])
@login_required
def api_expenses_calendar_legacy():
    """
    Returns daily spending totals for a full month.
    Query params: year (default current), month (default current, 1-based)

    Response: [{ "date": "2026-04-05", "amount": 450.0 }, ...]
    All days in the month are returned; days with no spend have amount=0.
    """
    uid   = get_uid()
    today = datetime.now()
    year  = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))

    # Validate
    if not (1 <= month <= 12):
        return jsonify({"error": "Invalid month"}), 400

    import calendar as _cal
    days_in_month = _cal.monthrange(year, month)[1]

    try:
        conn = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT DATE(created_at) AS day, COALESCE(SUM(amount), 0) AS total "
                "FROM expenses "
                "WHERE user_id=%s "
                "AND EXTRACT(YEAR FROM created_at)=%s "
                "AND EXTRACT(MONTH FROM created_at)=%s "
                "GROUP BY DATE(created_at)",
                (uid, year, month),
            )
            rows = cur.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"Calendar error: {e}")
        return jsonify([])

    # Build full month map (every day, even zero-spend days)
    day_map = {}
    for r in rows:
        day_key = r["day"].isoformat() if hasattr(r["day"], "isoformat") else str(r["day"])
        day_map[day_key] = _f(r["total"])

    result = []
    for d in range(1, days_in_month + 1):
        date_str = f"{year}-{month:02d}-{d:02d}"
        result.append({
            "date":   date_str,
            "amount": day_map.get(date_str, 0.0),
            "day":    d,
        })

    return jsonify(_safe_json(result))


# ─────────────────────────────────────────────────────────────────────
# BUDGET UPDATE ALIAS  —  PUT /api/budget/update
# (the existing POST /api/update-budget also works; this adds REST alias)
# ─────────────────────────────────────────────────────────────────────

@app.route("/api/budget/update", methods=["PUT", "POST"])
@login_required
def api_budget_update_alias():
    """
    Update the user's monthly budget.
    Body: { "monthly_budget": 15000 }
    Returns: { "message": "...", "monthly_budget": 15000 }
    """
    uid = get_uid()
    data = request.json or {}
    # Accept both field names for flexibility
    budget = float(data.get("monthly_budget", data.get("budget", 0)) or 0)
    if budget <= 0:
        return jsonify({"error": "Budget must be greater than 0"}), 400

    try:
        conn = get_db()
        with conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET monthly_budget = %s WHERE id = %s RETURNING monthly_budget",
                (budget, uid),
            )
            row = cur.fetchone()
        conn.close()
        if not row:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"message": f"Budget updated to ₹{budget:,.0f}", "monthly_budget": float(row[0])})
    except Exception as e:
        logger.error(f"Budget update alias error: {e}")
        return jsonify({"error": str(e)}), 500

# ─── Run ──────────────────────────────────────────────────────────

from email_routes import email_bp

app.register_blueprint(email_bp)


@app.route("/api/chat/v2", methods=["POST"])
@login_required
def api_chat_v2():
    """Alias — routes to smart-chat."""
    return api_smart_chat()


# ─────────────────────────────────────────────────────────────────────
# EMAIL: IMPROVED /api/test-email with detailed error handling
# (Overrides the version from email_routes.py)
# ─────────────────────────────────────────────────────────────────────



@app.route("/api/test-email-v2", methods=["POST"])
@login_required
def api_test_email_v2():
    """
    Production email sender with full error details.
    Uses EMAIL_SENDER + EMAIL_PASSWORD (port 587 + STARTTLS).
    """
    uid = get_uid()

    # ── Fetch user data ────────────────────────────────────────────
    try:
        conn = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT name, email, monthly_budget FROM users WHERE id=%s", (uid,))
            user = cur.fetchone()
            if not user:
                return jsonify({"success": False, "message": "User not found"}), 404

            today = datetime.now()
            cur.execute(
                "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
                "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s",
                (uid, today.month, today.year),
            )
            spent = _f(cur.fetchone()["t"])

            cur.execute(
                "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
                "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s "
                "GROUP BY category ORDER BY total DESC LIMIT 5",
                (uid, today.month, today.year),
            )
            categories = {r["category"]: _f(r["total"]) for r in cur.fetchall()}

            cur.execute(
                "SELECT COUNT(*) AS c FROM wardrobe_items WHERE user_id=%s AND wear_count=0",
                (uid,),
            )
            never_worn = int(cur.fetchone()["c"])
        conn.close()
    except Exception as e:
        logger.error(f"[test-email-v2] DB error: {e}")
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

    # ── Get credentials ────────────────────────────────────────────
    smtp_user = (
        os.getenv("EMAIL_SENDER") or os.getenv("EMAIL_USER") or
        os.getenv("MAIL_USERNAME") or os.getenv("SMTP_USER")
    )
    smtp_pass = (
        os.getenv("EMAIL_PASSWORD") or os.getenv("EMAIL_PASS") or
        os.getenv("MAIL_PASSWORD") or os.getenv("SMTP_PASS")
    )
    if smtp_user: smtp_user = smtp_user.strip()
    if smtp_pass: smtp_pass = smtp_pass.strip()

    if not smtp_user or not smtp_pass:
        return jsonify({
            "success": False,
            "message": "Email credentials not configured.",
            "hint": (
                "Add to your .env file:\n"
                "  EMAIL_SENDER=your@gmail.com\n"
                "  EMAIL_PASSWORD=your_app_password\n\n"
                "Get an App Password at: myaccount.google.com/apppasswords\n"
                "(requires 2-Step Verification to be ON)"
            ),
            "debug": {
                "sender_set": bool(smtp_user),
                "password_set": bool(smtp_pass),
            }
        }), 400

    # Strip spaces from App Password
    smtp_pass = smtp_pass.replace(" ", "").strip()

    # ── Build email ────────────────────────────────────────────────
    budget     = _f(user["monthly_budget"])
    remaining  = max(0.0, budget - spent)
    budget_pct = (spent / budget * 100) if budget > 0 else 0
    name       = user["name"].split()[0]
    month_name = today.strftime("%B %Y")

    status_color = "#e74c3c" if budget_pct >= 90 else "#f39c12" if budget_pct >= 70 else "#27ae60"
    status_emoji = "🚨" if budget_pct >= 90 else "⚠️" if budget_pct >= 70 else "✅"

    cat_rows = "".join(
        f"<tr><td style='padding:8px 14px;font-size:13px;color:#444;'>{c}</td>"
        f"<td style='padding:8px 14px;font-size:13px;font-weight:700;color:#7c6fa0;text-align:right;'>₹{v:,.0f}</td></tr>"
        for c, v in categories.items()
    ) if categories else "<tr><td colspan='2' style='padding:12px;color:#aaa;font-size:12px;text-align:center;'>No expenses this month</td></tr>"

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    html_body = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:20px;background:#f5f3fc;font-family:'Segoe UI',sans-serif;">
<div style="max-width:520px;margin:0 auto;background:#fff;border-radius:18px;overflow:hidden;box-shadow:0 4px 30px rgba(107,95,160,0.12);">
  <div style="background:linear-gradient(135deg,#6b5fa0,#a89cc8);padding:28px;text-align:center;">
    <div style="font-size:11px;color:rgba(255,255,255,0.7);letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">fenora · smart finance</div>
    <h1 style="color:#fff;margin:0;font-size:20px;font-weight:800;">Monthly Snapshot 📊</h1>
    <p style="color:rgba(255,255,255,0.75);margin:6px 0 0;font-size:13px;">Hey {name}! Here's your {month_name} summary.</p>
  </div>
  <div style="padding:24px;">
    <div style="background:#f8f5ff;border-left:4px solid {status_color};border-radius:10px;padding:16px 18px;margin-bottom:20px;">
      <div style="font-size:11px;color:#888;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">{status_emoji} Budget Status</div>
      <div style="font-size:26px;font-weight:800;color:#1a1a2e;">₹{spent:,.0f}</div>
      <div style="font-size:12px;color:#666;margin-top:4px;">of ₹{budget:,.0f} budget · {budget_pct:.0f}% used · ₹{remaining:,.0f} remaining</div>
      <div style="background:#e8e4f5;border-radius:6px;height:7px;margin-top:10px;overflow:hidden;">
        <div style="background:{status_color};height:7px;width:{min(budget_pct, 100):.0f}%;border-radius:6px;"></div>
      </div>
    </div>
    <h3 style="font-size:12px;font-weight:700;color:#7c6fa0;text-transform:uppercase;letter-spacing:0.5px;margin:0 0 10px;">💳 Spending by Category</h3>
    <table style="width:100%;border-collapse:collapse;background:#faf8ff;border-radius:10px;overflow:hidden;margin-bottom:20px;">
      <tbody>{cat_rows}</tbody>
    </table>
    {"<div style='background:#fff8ec;border:1px solid #fde68a;border-radius:10px;padding:14px;margin-bottom:16px;'><p style='margin:0;font-size:13px;color:#92400e;'>👗 <strong>" + str(never_worn) + " item(s)</strong> never worn. Wear them before buying new!</p></div>" if never_worn > 0 else ""}
    <div style="text-align:center;">
      <a href="{frontend_url}" style="display:inline-block;background:linear-gradient(135deg,#6b5fa0,#a89cc8);color:#fff;padding:12px 28px;border-radius:50px;text-decoration:none;font-size:13px;font-weight:700;">Open Dashboard →</a>
    </div>
  </div>
  <div style="padding:16px;text-align:center;color:#bbb;font-size:11px;">fenora · Smart Budget & Wardrobe Intelligence</div>
</div>
</body></html>"""

    plain_body = (
        f"fenora Financial Snapshot\n\n"
        f"Hi {name}!\n\n"
        f"Budget: ₹{budget:,.0f}\nSpent: ₹{spent:,.0f} ({budget_pct:.0f}%)\nRemaining: ₹{remaining:,.0f}\n\n"
        + ("Categories:\n" + "\n".join(f"  • {c}: ₹{v:,.0f}" for c, v in categories.items()) + "\n\n" if categories else "")
        + "— fenora AI"
    )

    subject = f"fenora: Your {month_name} Snapshot 📊"

    # ── Send via Brevo SDK ────────────────────────────────────────
    try:
        import sib_api_v3_sdk
        from sib_api_v3_sdk.rest import ApiException
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": user["email"]}],
            sender={"name": "Fenora", "email": "cloudberryyohh@gmail.com"},
            subject=subject,
            html_content=html_body
        )
        api_instance.send_transac_email(send_smtp_email)
        logger.info(f"✅ Email sent to {user['email']}")
        return jsonify({
            "success": True,
            "message": f"✅ Email sent to {user['email']}! Check your inbox (and spam folder).",
            "to":      user["email"],
            "subject": subject,
            "insights_summary": {
                "this_month_total": spent,
                "budget_pct": round(budget_pct, 1),
                "expense_insights_count": len(categories),
                "wardrobe_insights_count": 1 if never_worn > 0 else 0,
                "recommendations_count": 1,
            },
        })

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP auth error: {e}")
        return jsonify({
            "success": False,
            "message": "❌ Gmail authentication failed.",
            "hint": (
                "You MUST use a Gmail App Password — not your regular Gmail password.\n\n"
                "Steps:\n"
                "1. Go to myaccount.google.com\n"
                "2. Security → 2-Step Verification (must be ON)\n"
                "3. Security → App passwords → Create\n"
                "4. Copy the 16-char password to EMAIL_PASSWORD in your .env\n"
                "5. Spaces in the password are fine"
            ),
        }), 400

    except smtplib.SMTPConnectError as e:
        logger.error(f"SMTP connect error: {e}")
        return jsonify({
            "success": False,
            "message": "❌ Could not connect to Gmail SMTP.",
            "hint": "Check your internet connection. Port 587 may be blocked by your firewall or VPN.",
        }), 400

    except Exception as e:
        logger.error(f"Email unexpected error: {type(e).__name__}: {e}")
        return jsonify({
            "success": False,
            "message": f"❌ {type(e).__name__}: {str(e)}",
            "hint": "Check your backend logs for full details.",
        }), 500


# ─────────────────────────────────────────────────────────────────────
# EMAIL DEBUG ENDPOINT  — GET /api/email-debug
# ─────────────────────────────────────────────────────────────────────



@app.route("/api/email-debug", methods=["GET"])
@login_required
def api_email_debug():
    """Returns email config status without exposing credentials."""
    resend_key = os.getenv("RESEND_API_KEY")
    return jsonify({
        "sender_configured":   bool(resend_key),
        "password_configured": bool(resend_key),
        "sender_preview":      "onboarding@resend.dev (Resend SDK)" if resend_key else None,
        "smtp_host":  "api.resend.com",
        "smtp_port":  443,
        "method":     "HTTPS REST (Resend)",
        "ready":      bool(resend_key),
        "hint": (
            "✅ Ready to send email via Resend API!" if resend_key
            else "⚠️ Set RESEND_API_KEY in your Render environment."
        ),
    })


if __name__ == "__main__":
    from email_service import init_email_scheduler
    init_email_scheduler(app, get_db)
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.getenv("PORT", 5000))
    app.run(debug=debug_mode, host="0.0.0.0", port=port)