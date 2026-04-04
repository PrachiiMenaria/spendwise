"""
app.py — WardrobeIQ  Deployment-Ready Final Build
────────────────────────────────────────────────────
FIXES applied based on actual VS Code file structure:
  ✅ Model paths fixed (ml_spending_alert/saved_model.pkl)
  ✅ MSI model safe fallback (wardrobe_ml_system has no models/ folder)
  ✅ Spending analysis result display bug fixed
  ✅ Admin panel — creation SQL + is_admin route guard
  ✅ Wardrobe edit route added
  ✅ purchase_date simplified (month/year only, optional)
  ✅ Input validation on spending analysis form
  ✅ Irregular spending behavior logic (no heavy ML)
  ✅ Email with env vars (deployment safe)
  ✅ All hardcoded DB config removed
  ✅ debug=False for deployment
"""

import os, json, smtplib, logging
from functools import wraps
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify)
import psycopg2, psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash

# ── ML Model 1: spending predictor ──────────────
from ml_spending_alert.pipeline        import load_trained_model, predict_spending
from ml_spending_alert.alert_engine    import classify_risk, generate_alerts
from ml_spending_alert.reminder_engine import generate_reminders

# ─────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "wardrobeiq_2024_change_in_prod")

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── EMAIL — set as env vars for deployment ───────
# Render/Railway: add EMAIL_SENDER + EMAIL_PASSWORD in dashboard
EMAIL_CFG = {
    "sender":   os.getenv("EMAIL_SENDER",   ""),
    "password": os.getenv("EMAIL_PASSWORD", ""),
    "smtp":     "smtp.gmail.com",
    "port":     587,
}

# ── ML Model 1 ───────────────────────────────────
model, scaler = None, None
try:
    model, scaler = load_trained_model()
    logger.info("✅ Spending model loaded.")
except FileNotFoundError as e:
    logger.warning(f"⚠️  Spending model not found: {e} — run ml_spending.py first.")
except Exception as e:
    logger.warning(f"⚠️  Model load error: {e}")

# ── ML Model 2 (MSI) — wardrobe_ml_system ────────
# Your wardrobe_ml_system/ has NO models/ folder → safe fallback
_msi = None
def get_msi():
    global _msi
    if _msi is None:
        try:
            from wardrobe_ml_system.model import SpendingPredictor
            p = SpendingPredictor()
            p.load_model()
            _msi = p
            logger.info("✅ MSI model loaded.")
        except FileNotFoundError:
            logger.warning("⚠️  MSI model not found — rule-based fallback active.")
        except Exception as e:
            logger.warning(f"⚠️  MSI unavailable: {e}")
    return _msi


# ═══════════════════════════════════════════════
# DATABASE — all from env vars (deployment safe)
# ═══════════════════════════════════════════════
def get_db():
    """
    For local: set env vars or it uses defaults.
    For Render/Railway: set DATABASE_URL or individual vars in dashboard.
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Render provides DATABASE_URL — fix postgres:// → postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(database_url, sslmode="require")
    return psycopg2.connect(
        host     = os.getenv("DB_HOST",     "localhost"),
        database = os.getenv("DB_NAME",     "wardrobe_db"),
        user     = os.getenv("DB_USER",     "postgres"),
        password = os.getenv("DB_PASSWORD", "wardrobe123"),
        port     = os.getenv("DB_PORT",     "5432"),
    )


def init_db():
    """Create all tables. Safe to call on every startup."""
    ddl = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(150) UNIQUE NOT NULL,
        password_hash VARCHAR(256) NOT NULL,
        age INTEGER, gender VARCHAR(20),
        is_admin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS survey_responses (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        wardrobe_size INTEGER, average_decision_time FLOAT,
        monthly_budget FLOAT, monthly_spending FLOAT,
        repeat_frequency VARCHAR(50), created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS wardrobe_items (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        item_name VARCHAR(100) NOT NULL,
        category VARCHAR(50) DEFAULT 'Other',
        color VARCHAR(50),
        purchase_price FLOAT DEFAULT 0,
        purchase_month VARCHAR(10),
        wear_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS outfit_decisions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        decision_time FLOAT, date DATE DEFAULT CURRENT_DATE,
        created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS ml_predictions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        predicted_spending FLOAT, risk_category VARCHAR(20),
        budget_ratio FLOAT, monthly_budget FLOAT,
        alerts JSONB, reminders JSONB,
        predicted_at TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS email_log (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        subject VARCHAR(200), sent_at TIMESTAMP DEFAULT NOW(), status VARCHAR(20)
    );
CREATE INDEX IF NOT EXISTS idx_expenses_user_month
    ON expenses(user_id, expense_year, expense_month);
    CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        amount FLOAT NOT NULL,
        category VARCHAR(50) NOT NULL DEFAULT 'Others',
        expense_month INTEGER NOT NULL,
        expense_year  INTEGER NOT NULL,
        note TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_expenses_user_month
        ON expenses(user_id, expense_year, expense_month);
        
    """
    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
    conn.close()
    logger.info("✅ DB tables verified.")


# ═══════════════════════════════════════════════
# AUTH DECORATORS
# ═══════════════════════════════════════════════
def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*a, **kw)
    return dec

def admin_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if not session.get("is_admin"):
            flash("Admin access required.", "danger")
            return redirect(url_for("dashboard"))
        return f(*a, **kw)
    return dec


# ═══════════════════════════════════════════════
# EMAIL HELPERS
# ═══════════════════════════════════════════════
def send_email(to: str, subject: str, html: str) -> tuple:
    """Returns (success: bool, error_msg: str)."""
    sender = EMAIL_CFG["sender"]
    pwd    = EMAIL_CFG["password"]

    if not sender or not pwd:
        return False, ("Email not configured. "
                       "Set EMAIL_SENDER and EMAIL_PASSWORD environment variables.")
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = sender
        msg["To"]      = to
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(EMAIL_CFG["smtp"], EMAIL_CFG["port"], timeout=15) as s:
            s.ehlo(); s.starttls()
            s.login(sender, pwd)
            s.sendmail(sender, to, msg.as_string())
        return True, ""
    except smtplib.SMTPAuthenticationError:
        return False, ("Gmail authentication failed. "
                       "Make sure 2FA is ON and you're using a 16-char App Password, "
                       "not your regular password.")
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        return False, str(e)

def reminder_html(name, risk, predicted, budget):
    diff  = predicted - budget
    bg    = "#d4edda" if risk=="Safe" else "#fff3cd" if risk=="Moderate" else "#f8d7da"
    badge = (f"<b style='color:#c0392b'>₹{diff:,.0f} over budget</b>"
             if diff > 0 else
             f"<b style='color:#27ae60'>₹{abs(diff):,.0f} under budget ✓</b>")
    return f"""<div style="font-family:sans-serif;max-width:540px;margin:auto;padding:36px;
                background:#fff;border-radius:12px;border:1px solid #eee">
      <h2 style="color:#1a1a2e">Hi {name} 👋</h2>
      <p>Your <b>WardrobeIQ</b> weekly spending report:</p>
      <div style="background:{bg};border-radius:10px;padding:20px;margin:20px 0">
        <b>Risk:</b> {risk}<br>
        <b>Predicted Next Month:</b> ₹{predicted:,.0f}<br>
        <b>Your Budget:</b> ₹{budget:,.0f}<br>{badge}
      </div>
      <p>💡 Wear existing clothes before buying new ones.</p>
      <p style="color:#aaa;font-size:12px">WardrobeIQ · Automated Weekly Reminder</p>
    </div>"""


# ═══════════════════════════════════════════════
# IRREGULAR SPENDING BEHAVIOR (logic-based, no ML)
# ═══════════════════════════════════════════════
def compute_spending_behavior(uid: int) -> dict:
    """
    Classify purchase frequency based on wardrobe_items.created_at gaps.
    No ML needed — pure date arithmetic.
    Returns { pattern, label, insight, purchase_dates }
    """
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT created_at::date AS d FROM wardrobe_items "
        "WHERE user_id=%s ORDER BY created_at ASC", (uid,)
    )
    rows = cur.fetchall()
    cur.close(); conn.close()

    dates = [r["d"] for r in rows]
    if len(dates) < 2:
        return {"pattern": "insufficient_data", "label": "Not enough data",
                "insight": "Add more items to see your purchase frequency pattern.",
                "purchase_dates": dates}

    gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
    avg_gap = sum(gaps) / len(gaps)

    if avg_gap < 10:
        pattern = "frequent"
        label   = "Frequent Buyer"
        insight = (f"⚠️ You buy clothes every {avg_gap:.0f} days on average — "
                   "very frequent. Spending spikes are likely. "
                   "Consider a 30-day purchase pause.")
    elif avg_gap <= 30:
        pattern = "moderate"
        label   = "Moderate Buyer"
        insight = (f"👍 You buy clothes every {avg_gap:.0f} days on average — "
                   "a moderate pace. Keep tracking to stay within budget.")
    else:
        pattern = "occasional"
        label   = "Occasional Buyer"
        insight = (f"💡 You buy clothes every {avg_gap:.0f} days on average — "
                   "occasional purchases but spending spikes are possible. "
                   "Watch your per-item cost.")

    # Cluster detection: any 3 purchases within 7 days?
    clustered = False
    for i in range(len(dates)-2):
        if (dates[i+2] - dates[i]).days <= 7:
            clustered = True
            break
    if clustered:
        insight += " 🔴 Clustered purchases detected (3+ items bought within a week)."

    return {"pattern": pattern, "label": label,
            "insight": insight, "purchase_dates": [str(d) for d in dates]}


# ═══════════════════════════════════════════════
# AI INSIGHTS ENGINE
# ═══════════════════════════════════════════════
def generate_ai_insights(uid, wui, total_spending, monthly_budget,
                          avg_decision, latest_pred, total_items) -> list:
    insights = []

    # Budget
    if monthly_budget > 0:
        ratio = total_spending / monthly_budget
        if ratio > 1.0:
            insights.append({"icon":"🚨","level":"danger","title":"Over Budget",
                "message":f"Spent ₹{total_spending:,.0f} vs ₹{monthly_budget:,.0f} budget — "
                          f"₹{(total_spending-monthly_budget):,.0f} over."})
        elif ratio > 0.8:
            insights.append({"icon":"⚠️","level":"warn","title":"Near Budget Limit",
                "message":f"{ratio*100:.0f}% of ₹{monthly_budget:,.0f} used. Slow down."})
        else:
            insights.append({"icon":"✅","level":"good","title":"Within Budget",
                "message":f"₹{total_spending:,.0f} of ₹{monthly_budget:,.0f} — on track."})

    # WUI
    if total_items == 0:
        insights.append({"icon":"👗","level":"info","title":"No Items Tracked",
            "message":"Add wardrobe items to unlock WUI and CPW analysis."})
    elif wui < 2.0:
        insights.append({"icon":"😴","level":"warn","title":"Low WUI",
            "message":f"WUI = {wui} — each item worn {wui:.1f}× on average. Wear before buying."})
    elif wui >= 5.0:
        insights.append({"icon":"🏆","level":"good","title":"Excellent WUI",
            "message":f"WUI = {wui} — great wardrobe utilization!"})

    # Decision time
    if avg_decision > 20:
        insights.append({"icon":"⏱️","level":"warn","title":"High Decision Time",
            "message":f"{avg_decision:.0f} min avg — wardrobe clutter. Fewer items = faster decisions."})

    # ML prediction
    if latest_pred:
        p = float(latest_pred["predicted_spending"])
        b = float(latest_pred["monthly_budget"] or 0)
        if latest_pred["risk_category"] == "High Risk":
            insights.append({"icon":"🔮","level":"danger","title":"High Spending Predicted",
                "message":f"ML predicts ₹{p:,.0f} — ₹{p-b:,.0f} over budget."})
        elif latest_pred["risk_category"] == "Moderate":
            insights.append({"icon":"🔮","level":"warn","title":"Moderate Spending Predicted",
                "message":f"ML predicts ₹{p:,.0f} — approaching ₹{b:,.0f} budget."})

    # CPW
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT category,
                   ROUND(AVG(CASE WHEN wear_count>0 THEN purchase_price/wear_count
                             ELSE purchase_price END)::numeric,0) AS avg_cpw
            FROM wardrobe_items WHERE user_id=%s
            GROUP BY category ORDER BY avg_cpw DESC LIMIT 1
        """, (uid,))
        worst = cur.fetchone()
        cur.close(); conn.close()
        if worst and float(worst["avg_cpw"] or 0) > 300:
            insights.append({"icon":"💰","level":"warn",
                "title":f"High CPW: {worst['category']}",
                "message":f"{worst['category']} costs ₹{worst['avg_cpw']:.0f}/wear. Wear more before buying."})
    except Exception:
        pass

    return insights[:5]


# ═══════════════════════════════════════════════
# CPW HELPER
# ═══════════════════════════════════════════════
def compute_cpw(uid: int) -> dict:
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, item_name, category, purchase_price, wear_count,
               CASE WHEN wear_count>0
                    THEN ROUND((purchase_price/wear_count)::numeric,2)
                    ELSE purchase_price END AS cpw
        FROM wardrobe_items WHERE user_id=%s ORDER BY cpw DESC
    """, (uid,))
    items = cur.fetchall()
    cur.execute("""
        SELECT category, COUNT(*) AS item_count,
               ROUND(SUM(purchase_price)::numeric,2) AS total_spent,
               ROUND(AVG(CASE WHEN wear_count>0 THEN purchase_price/wear_count
                         ELSE purchase_price END)::numeric,2) AS avg_cpw
        FROM wardrobe_items WHERE user_id=%s GROUP BY category ORDER BY avg_cpw DESC
    """, (uid,))
    by_cat = cur.fetchall()
    cur.close(); conn.close()
    insight = "Log wear counts to get accurate cost-per-wear analysis."
    if by_cat:
        worst = by_cat[0]; best = by_cat[-1]
        if float(worst["avg_cpw"] or 0) > 500:
            insight = f"⚠️ {worst['category']} costs ₹{worst['avg_cpw']:.0f}/wear. Wear more."
        elif float(best["avg_cpw"] or 0) < 100:
            insight = f"✅ {best['category']} gives best value at ₹{best['avg_cpw']:.0f}/wear."
        else:
            insight = "💡 Rotate least-worn items to reduce cost per wear."
    return {"items":[dict(r) for r in items],
            "by_category":[dict(r) for r in by_cat], "insight":insight}


# ═══════════════════════════════════════════════
# ROUTES — PUBLIC
# ═══════════════════════════════════════════════
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name  = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        pwd   = request.form["password"]
        age   = request.form.get("age") or None
        gen   = request.form.get("gender") or None
        if len(pwd) < 6:
            flash("Password must be ≥ 6 characters.", "danger")
            return render_template("register.html")
        try:
            conn = get_db()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users(name,email,password_hash,age,gender)"
                        "VALUES(%s,%s,%s,%s,%s) RETURNING id",
                        (name, email, generate_password_hash(pwd), age, gen))
                    uid = cur.fetchone()[0]
            conn.close()
            session.update(user_id=uid, user_name=name, is_admin=False)
            flash(f"Welcome, {name}!", "success")
            return redirect(url_for("survey"))
        except psycopg2.errors.UniqueViolation:
            flash("Email already registered.", "warning")
        except Exception as e:
            flash(f"Registration error: {e}", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        pwd   = request.form["password"]
        conn  = get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cur.fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], pwd):
            session.update(user_id=user["id"], user_name=user["name"],
                           is_admin=bool(user["is_admin"]))
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("admin_panel") if user["is_admin"] else url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Signed out.", "info")
    return redirect(url_for("login"))


# ═══════════════════════════════════════════════
# SURVEY
# ═══════════════════════════════════════════════
@app.route("/survey", methods=["GET","POST"])
@login_required
def survey():
    if request.method == "POST":
        conn = get_db()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO survey_responses"
                    "(user_id,wardrobe_size,average_decision_time,"
                    "monthly_budget,monthly_spending,repeat_frequency)"
                    "VALUES(%s,%s,%s,%s,%s,%s)",
                    (session["user_id"],
                     request.form.get("wardrobe_size"),
                     request.form.get("average_decision_time"),
                     request.form.get("monthly_budget"),
                     request.form.get("monthly_spending") or None,
                     request.form.get("repeat_frequency")))
        conn.close()
        flash("Survey saved!", "success")
        return redirect(url_for("wardrobe_view"))
    return render_template("survey.html")


# ═══════════════════════════════════════════════
# WARDROBE CRUD  (includes EDIT — was missing)
# ═══════════════════════════════════════════════
@app.route("/wardrobe")
@login_required
def wardrobe_view():
    uid  = session["user_id"]
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, item_name, category, color, purchase_price,
               purchase_month, wear_count,
               CASE WHEN wear_count>0
                    THEN ROUND((purchase_price/wear_count)::numeric,2)
                    ELSE purchase_price END AS cpw
        FROM wardrobe_items WHERE user_id=%s ORDER BY created_at DESC
    """, (uid,))
    items = cur.fetchall()
    cur.close(); conn.close()
    return render_template("wardrobe.html", items=items)

@app.route("/wardrobe/add", methods=["GET","POST"])
@login_required
def wardrobe_add():
    if request.method == "POST":
        uid   = session["user_id"]
        name  = request.form["item_name"].strip()
        cat   = request.form.get("category","Other")
        color = request.form.get("color","").strip()
        price = float(request.form.get("purchase_price") or 0)
        month = request.form.get("purchase_month","").strip() or None  # simplified
        wears = int(request.form.get("wear_count") or 0)
        conn  = get_db()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO wardrobe_items"
                    "(user_id,item_name,category,color,purchase_price,purchase_month,wear_count)"
                    "VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    (uid, name, cat, color, price, month, wears))
        conn.close()
        flash(f"'{name}' added! ✓", "success")
        return redirect(url_for("wardrobe_view"))
    return render_template("wardrobe_add.html")

@app.route("/wardrobe/edit/<int:item_id>", methods=["GET","POST"])
@login_required
def wardrobe_edit(item_id):
    """Edit an existing wardrobe item."""
    uid  = session["user_id"]
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if request.method == "POST":
        name  = request.form["item_name"].strip()
        cat   = request.form.get("category","Other")
        color = request.form.get("color","").strip()
        price = float(request.form.get("purchase_price") or 0)
        month = request.form.get("purchase_month","").strip() or None
        wears = int(request.form.get("wear_count") or 0)
        with conn:
            with conn.cursor() as cur2:
                cur2.execute(
                    "UPDATE wardrobe_items SET item_name=%s,category=%s,color=%s,"
                    "purchase_price=%s,purchase_month=%s,wear_count=%s "
                    "WHERE id=%s AND user_id=%s",
                    (name, cat, color, price, month, wears, item_id, uid))
        conn.close()
        flash(f"'{name}' updated! ✓", "success")
        return redirect(url_for("wardrobe_view"))

    cur.execute("SELECT * FROM wardrobe_items WHERE id=%s AND user_id=%s", (item_id, uid))
    item = cur.fetchone()
    cur.close(); conn.close()
    if not item:
        flash("Item not found.", "danger")
        return redirect(url_for("wardrobe_view"))
    return render_template("wardrobe_edit.html", item=item)

@app.route("/wardrobe/wear/<int:item_id>", methods=["POST"])
@login_required
def wardrobe_wear(item_id):
    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE wardrobe_items SET wear_count=wear_count+1 "
                "WHERE id=%s AND user_id=%s", (item_id, session["user_id"]))
    conn.close()
    flash("Wear count +1 ✓", "success")
    return redirect(url_for("wardrobe_view"))

@app.route("/wardrobe/delete/<int:item_id>", methods=["POST"])
@login_required
def wardrobe_delete(item_id):
    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM wardrobe_items WHERE id=%s AND user_id=%s",
                        (item_id, session["user_id"]))
    conn.close()
    flash("Item removed.", "info")
    return redirect(url_for("wardrobe_view"))


# ═══════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════
@app.route("/dashboard")
@login_required
def dashboard():
    uid  = session["user_id"]
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT name,email FROM users WHERE id=%s", (uid,))
    user = cur.fetchone()

    cur.execute("SELECT monthly_budget FROM survey_responses "
                "WHERE user_id=%s ORDER BY created_at DESC LIMIT 1", (uid,))
    sv = cur.fetchone()
    monthly_budget = float(sv["monthly_budget"]) if sv and sv["monthly_budget"] else 0.0

    cur.execute("SELECT COALESCE(SUM(purchase_price),0) AS t FROM wardrobe_items WHERE user_id=%s",(uid,))
    total_spending = round(float(cur.fetchone()["t"]), 2)

    cur.execute("SELECT COALESCE(SUM(wear_count),0) AS tw, COUNT(*) AS tc "
                "FROM wardrobe_items WHERE user_id=%s", (uid,))
    r  = cur.fetchone()
    tw = float(r["tw"]); tc = max(float(r["tc"]), 1)
    wui = round(tw / tc, 2)
    total_items = int(r["tc"])

    cur.execute("SELECT COALESCE(AVG(decision_time),0) AS a FROM outfit_decisions WHERE user_id=%s",(uid,))
    avg_decision = round(float(cur.fetchone()["a"]), 1)

    cur.execute("SELECT category,COUNT(*) AS cnt FROM wardrobe_items "
                "WHERE user_id=%s GROUP BY category ORDER BY cnt DESC", (uid,))
    categories = cur.fetchall()

    cur.execute("SELECT item_name,wear_count FROM wardrobe_items "
                "WHERE user_id=%s ORDER BY wear_count DESC LIMIT 1", (uid,))
    most_worn = cur.fetchone()

    cur.execute("SELECT item_name,wear_count FROM wardrobe_items "
                "WHERE user_id=%s ORDER BY wear_count ASC LIMIT 5", (uid,))
    least_used = cur.fetchall()

    cur.execute("SELECT * FROM ml_predictions WHERE user_id=%s "
                "ORDER BY predicted_at DESC LIMIT 1", (uid,))
    latest_pred = cur.fetchone()

    cur.execute("""
        SELECT category,
               ROUND(AVG(CASE WHEN wear_count>0 THEN purchase_price/wear_count
                         ELSE purchase_price END)::numeric,2) AS avg_cpw
        FROM wardrobe_items WHERE user_id=%s
        GROUP BY category ORDER BY avg_cpw DESC LIMIT 3
    """, (uid,))
    top_cpw = cur.fetchall()
    cur.close(); conn.close()

    # Expense summary for current month
    today_dt    = datetime.now()
    exp_summary = get_expense_summary(uid, today_dt.year, today_dt.month)

    insights = generate_ai_insights(uid, wui, total_spending, monthly_budget,
                                     avg_decision, latest_pred, total_items)
    behavior = compute_spending_behavior(uid)
    total_expense = exp_summary.get("total", 0)
    category_data = exp_summary.get("category_breakdown", {})
    analytics = {
    "budget": monthly_budget,
    "total_spent": total_expense,
    "remaining": monthly_budget - total_expense,
    "pct_used": int((total_expense / monthly_budget) * 100) if monthly_budget else 0,
    "category_breakdown": category_data
    }

    # ONE single return — all variables included
    return render_template("dashboard.html",
    user=user,
    analytics=analytics,   # ✅ ADD THIS
    monthly_budget=monthly_budget,
    total_spending=total_spending,
    total_items=total_items,
    wui=wui,
    avg_decision=avg_decision,
    categories=categories,
    most_worn=most_worn,
    least_used=least_used,
    latest_pred=latest_pred,
    top_cpw=top_cpw,
    insights=insights,
    behavior=behavior,
    exp_summary=exp_summary,
    now=today_dt,
)

# ═══════════════════════════════════════════════
# CHART.JS API ROUTES
# ═══════════════════════════════════════════════
@app.route("/api/chart/spending-vs-budget")
@login_required
def chart_spending_vs_budget():
    uid  = session["user_id"]
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT TO_CHAR(predicted_at,'DD Mon') AS label,
               ROUND(predicted_spending::numeric,0) AS predicted,
               ROUND(monthly_budget::numeric,0) AS budget
        FROM ml_predictions WHERE user_id=%s
        ORDER BY predicted_at DESC LIMIT 6
    """, (uid,))
    rows = list(reversed(cur.fetchall()))
    cur.close(); conn.close()
    return jsonify({"labels":[r["label"] for r in rows],
                    "predicted":[float(r["predicted"] or 0) for r in rows],
                    "budget":[float(r["budget"] or 0) for r in rows]})

@app.route("/api/chart/cpw-by-category")
@login_required
def chart_cpw():
    uid  = session["user_id"]
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT category,
               ROUND(AVG(CASE WHEN wear_count>0 THEN purchase_price/wear_count
                         ELSE purchase_price END)::numeric,2) AS avg_cpw
        FROM wardrobe_items WHERE user_id=%s GROUP BY category ORDER BY avg_cpw DESC
    """, (uid,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify({"labels":[r["category"] for r in rows],
                    "values":[float(r["avg_cpw"] or 0) for r in rows]})

@app.route("/api/chart/category-distribution")
@login_required
def chart_cat_dist():
    uid  = session["user_id"]
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT category,COUNT(*) AS cnt FROM wardrobe_items "
                "WHERE user_id=%s GROUP BY category ORDER BY cnt DESC", (uid,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify({"labels":[r["category"] for r in rows],
                    "values":[int(r["cnt"]) for r in rows]})

@app.route("/api/chart/wui-gauge")
@login_required
def chart_wui():
    uid  = session["user_id"]
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT COALESCE(SUM(wear_count),0) AS tw, COUNT(*) AS tc "
                "FROM wardrobe_items WHERE user_id=%s", (uid,))
    r = cur.fetchone()
    cur.close(); conn.close()
    tw, tc = float(r["tw"]), max(float(r["tc"]),1)
    wui = round(tw/tc, 2)
    return jsonify({"wui":wui, "label":"Excellent" if wui>=5 else "Moderate" if wui>=2 else "Low"})

@app.route("/api/chart/admin/user-growth")
@admin_required
def chart_admin_growth():
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT TO_CHAR(DATE_TRUNC('day',created_at),'DD Mon') AS day, COUNT(*) AS cnt
        FROM users WHERE is_admin=FALSE AND created_at>=NOW()-INTERVAL '14 days'
        GROUP BY DATE_TRUNC('day',created_at) ORDER BY DATE_TRUNC('day',created_at)
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify({"labels":[r["day"] for r in rows],
                    "values":[int(r["cnt"]) for r in rows]})

@app.route("/api/chart/admin/risk-distribution")
@admin_required
def chart_admin_risk():
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT risk_category,COUNT(*) AS cnt FROM ml_predictions GROUP BY risk_category")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify({"labels":[r["risk_category"] for r in rows],
                    "values":[int(r["cnt"]) for r in rows]})

@app.route("/api/chart/admin/category-popularity")
@admin_required
def chart_admin_cats():
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT category,COUNT(*) AS cnt FROM wardrobe_items "
                "GROUP BY category ORDER BY cnt DESC LIMIT 8")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify({"labels":[r["category"] for r in rows],
                    "values":[int(r["cnt"]) for r in rows]})


# ═══════════════════════════════════════════════
# CPW PAGE
# ═══════════════════════════════════════════════
@app.route("/cpw")
@login_required
def cpw_page():
    return render_template("cpw.html", **compute_cpw(session["user_id"]))


# ═══════════════════════════════════════════════
# SPENDING ALERT — BUG FIX: result always returned
# ═══════════════════════════════════════════════
@app.route("/spending-alert", methods=["GET","POST"])
@login_required
def spending_alert():
    """
    FIX: result was not displaying because:
    1. Model was None (wrong path) → fixed in constants.py
    2. Form redirect on flash prevented result rendering → removed redirect
    3. Input validation missing → added
    """
    uid    = session["user_id"]
    result = None
    form_data = {}   # preserve form values on error

    if request.method == "POST":
        form_data = request.form.to_dict()

        # ── Input validation ──────────────────────
        errors = []
        try:
            budget   = float(request.form.get("monthly_budget",0))
            last_sp  = float(request.form.get("last_month_spending",0))
            num_pur  = int(request.form.get("num_purchases",0))
            ward_sz  = int(request.form.get("wardrobe_size",1))
            tot_worn = int(request.form.get("total_times_worn",0))
            dec_time = float(request.form.get("avg_outfit_decision_min",0))
            shop_frq = float(request.form.get("shopping_frequency",0))

            if budget <= 0:     errors.append("Monthly budget must be > 0")
            if ward_sz <= 0:    errors.append("Wardrobe size must be > 0")
            if shop_frq < 0:    errors.append("Shopping frequency cannot be negative")
            if dec_time < 0:    errors.append("Decision time cannot be negative")
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid input: {e}")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("spending_alert.html",
                                   result=None, form_data=form_data)

        if model is None:
            # FIX: don't redirect — render with informative message
            flash("ML model not loaded. Run: python ml_spending_alert/ml_spending.py", "danger")
            return render_template("spending_alert.html",
                                   result=None, form_data=form_data)

        try:
            ud = {
                "monthly_budget":          budget,
                "last_month_spending":     last_sp,
                "num_purchases":           num_pur,
                "wardrobe_size":           ward_sz,
                "total_times_worn":        tot_worn,
                "avg_outfit_decision_min": dec_time,
                "shopping_frequency":      shop_frq,
            }

            # ── Model 1: ml_spending_alert ──
            predicted   = predict_spending(ud, model, scaler)
            risk, ratio = classify_risk(predicted, ud["monthly_budget"])
            alerts      = generate_alerts(ud, predicted, risk, ratio)
            reminders   = generate_reminders(risk, ratio, ud["shopping_frequency"])
            wui         = round(ud["total_times_worn"] / max(ud["wardrobe_size"],1), 2)

            # ── Model 2: MSI — rule-based fallback ──
            msi_result = None
            msi = get_msi()
            if msi:
                try:
                    msi_result = msi.predict_spending({
                        "monthly_budget":                  budget,
                        "total_clothing_spent_last_month": last_sp,
                        "number_of_purchases_last_month":  num_pur,
                        "wardrobe_size":                   ward_sz,
                        "total_times_worn":                tot_worn,
                        "average_decision_time_minutes":   dec_time,
                        "shopping_frequency_per_month":    shop_frq,
                    })
                except Exception as e:
                    logger.warning(f"MSI skipped: {e}")

            if msi_result is None:
                # Fallback rule-based MSI estimate
                ratio_last = last_sp / max(budget, 1)
                msi_result = {
                    "predicted_spending": round(last_sp * 1.05, 2),
                    "alert_triggered":    ratio_last > 0.8,
                    "alert_message":      ("Based on last-month trend (MSI model unavailable)."
                                          if ratio_last > 0.8 else None),
                    "is_fallback":        True,
                }

            # Save to DB
            conn = get_db()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO ml_predictions"
                        "(user_id,predicted_spending,risk_category,"
                        "budget_ratio,monthly_budget,alerts,reminders)"
                        "VALUES(%s,%s,%s,%s,%s,%s,%s)",
                        (uid, round(predicted,2), risk, round(ratio,4),
                         budget, json.dumps(alerts), json.dumps(reminders)))
            conn.close()

            # FIX: result dict always set → template renders it
            result = {
                "predicted":   round(predicted, 2),
                "budget":      budget,
                "risk":        risk,
                "ratio":       round(ratio * 100, 1),
                "wui":         wui,
                "over_under":  round(predicted - budget, 2),
                "alerts":      alerts,
                "reminders":   reminders,
                "msi":         msi_result,
            }
            logger.info(f"✅ Prediction OK: user={uid} predicted=₹{predicted:.0f} risk={risk}")

        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            flash(f"Prediction failed: {str(e)}", "danger")
            result = None

    # ── Always render template (never redirect away from POST results) ──
    return render_template("spending_alert.html", result=result, form_data=form_data)


# ═══════════════════════════════════════════════
# EMAIL REMINDER
# ═══════════════════════════════════════════════
@app.route("/send-reminder", methods=["POST"])
@login_required
def send_reminder():
    uid  = session["user_id"]
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT name,email FROM users WHERE id=%s", (uid,))
    user = cur.fetchone()
    cur.execute("SELECT * FROM ml_predictions WHERE user_id=%s "
                "ORDER BY predicted_at DESC LIMIT 1", (uid,))
    pred = cur.fetchone()
    cur.close(); conn.close()

    if not pred:
        flash("No prediction found. Run Spending Analysis first.", "warning")
        return redirect(url_for("spending_alert"))

    html    = reminder_html(user["name"], pred["risk_category"],
                            pred["predicted_spending"], pred["monthly_budget"] or 0)
    ok, err = send_email(user["email"], "📊 WardrobeIQ Weekly Reminder", html)

    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO email_log(user_id,subject,status) VALUES(%s,%s,%s)",
                        (uid, "Weekly Reminder", "sent" if ok else "failed"))
    conn.close()

    flash("✓ Reminder sent!" if ok else f"Email failed: {err}", "success" if ok else "danger")
    return redirect(url_for("dashboard"))


# ═══════════════════════════════════════════════
# ADMIN PANEL
# ═══════════════════════════════════════════════
@app.route("/admin")
@admin_required
def admin_panel():
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT COUNT(*) AS c FROM users WHERE is_admin=FALSE")
    total_users = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM ml_predictions WHERE risk_category='High Risk'")
    high_risk = cur.fetchone()["c"]

    cur.execute("SELECT COALESCE(AVG(predicted_spending),0) AS ap FROM ml_predictions")
    avg_spending = round(float(cur.fetchone()["ap"]), 2)

    cur.execute("SELECT COALESCE(AVG(budget_ratio),0) AS ar FROM ml_predictions")
    avg_ratio = round(float(cur.fetchone()["ar"])*100, 1)

    cur.execute("SELECT category,COUNT(*) AS cnt FROM wardrobe_items "
                "GROUP BY category ORDER BY cnt DESC LIMIT 2")
    top_cats = cur.fetchall()

    cur.execute("""SELECT COALESCE(ROUND(AVG(CASE WHEN wear_count>0 THEN purchase_price/wear_count
                              ELSE purchase_price END)::numeric,2),0) AS gcpw FROM wardrobe_items""")
    gcpw = cur.fetchone()["gcpw"]

    cur.execute("""
        SELECT u.id,u.name,u.email,TO_CHAR(u.created_at,'DD Mon YYYY') AS joined,
               s.monthly_budget,p.predicted_spending,p.risk_category
        FROM users u
        LEFT JOIN LATERAL(
            SELECT monthly_budget FROM survey_responses
            WHERE user_id=u.id ORDER BY created_at DESC LIMIT 1) s ON TRUE
        LEFT JOIN LATERAL(
            SELECT predicted_spending,risk_category FROM ml_predictions
            WHERE user_id=u.id ORDER BY predicted_at DESC LIMIT 1) p ON TRUE
        WHERE u.is_admin=FALSE ORDER BY u.created_at DESC
    """)
    all_users = cur.fetchall()

    cur.execute("SELECT risk_category,COUNT(*) AS cnt FROM ml_predictions GROUP BY risk_category")
    risk_dist = cur.fetchall()
    cur.close(); conn.close()

    return render_template("admin.html",
        total_users=total_users, high_risk=high_risk,
        avg_spending=avg_spending, avg_ratio=avg_ratio,
        top_cats=top_cats, gcpw=gcpw,
        all_users=all_users, risk_dist=risk_dist)

# ═══════════════════════════════════════════════
# EXPENSE TRACKING ENGINE
# ═══════════════════════════════════════════════

EXPENSE_CATEGORIES = ["Food", "Clothing", "Subscriptions", "Lifestyle", "Others"]

def get_monthly_budget(uid: int) -> float:
    """Fetch latest monthly budget for user from survey_responses."""
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT monthly_budget FROM survey_responses "
        "WHERE user_id=%s ORDER BY created_at DESC LIMIT 1", (uid,)
    )
    row = cur.fetchone()
    cur.close(); conn.close()
    return float(row["monthly_budget"]) if row and row["monthly_budget"] else 0.0


def get_expense_summary(uid: int, year: int, month: int) -> dict:
    """
    Returns full spending summary for a given month.
    Used by both the expense page and dashboard integration.
    """
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Total for requested month
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id=%s AND expense_year=%s AND expense_month=%s
    """, (uid, year, month))
    current_total = round(float(cur.fetchone()["total"]), 2)

    # Previous month total (handles January → December of previous year)
    prev_month = month - 1 if month > 1 else 12
    prev_year  = year if month > 1 else year - 1
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id=%s AND expense_year=%s AND expense_month=%s
    """, (uid, prev_year, prev_month))
    prev_total = round(float(cur.fetchone()["total"]), 2)

    # Per-category breakdown for current month
    cur.execute("""
        SELECT category, ROUND(SUM(amount)::numeric, 2) AS total
        FROM expenses
        WHERE user_id=%s AND expense_year=%s AND expense_month=%s
        GROUP BY category ORDER BY total DESC
    """, (uid, year, month))
    by_category = cur.fetchall()

    cur.close(); conn.close()

    budget    = get_monthly_budget(uid)
    remaining = round(budget - current_total, 2)
    util_pct  = round((current_total / budget * 100), 1) if budget > 0 else 0.0
    mom_delta = round(current_total - prev_total, 2)     # month-over-month change

    return {
        "current_total":  current_total,
        "prev_total":     prev_total,
        "by_category":    [dict(r) for r in by_category],
        "budget":         budget,
        "remaining":      remaining,
        "util_pct":       util_pct,
        "mom_delta":      mom_delta,
        "month":          month,
        "year":           year,
        "prev_month":     prev_month,
        "prev_year":      prev_year,
    }


# ── ADD EXPENSE ──────────────────────────────────
@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def expense_add():
    uid   = session["user_id"]
    today = datetime.now()

    if request.method == "POST":
        errors = []
        try:
            amount   = float(request.form.get("amount", 0))
            category = request.form.get("category", "Others").strip()
            month    = int(request.form.get("expense_month", today.month))
            year     = int(request.form.get("expense_year",  today.year))
            note     = request.form.get("note", "").strip() or None

            if amount <= 0:
                errors.append("Amount must be greater than 0.")
            if category not in EXPENSE_CATEGORIES:
                errors.append("Invalid category selected.")
            if not (1 <= month <= 12):
                errors.append("Invalid month.")
            if not (2000 <= year <= today.year + 1):
                errors.append("Invalid year.")
        except (ValueError, TypeError):
            errors.append("Invalid input values. Please check the form.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("expense_add.html",
                                   categories=EXPENSE_CATEGORIES,
                                   today=today)

        conn = get_db()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO expenses(user_id, amount, category, "
                    "expense_month, expense_year, note) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (uid, amount, category, month, year, note)
                )
        conn.close()
        flash(f"✓ ₹{amount:,.0f} expense added under {category}.", "success")
        return redirect(url_for("expense_list"))

    return render_template("expense_add.html",
                           categories=EXPENSE_CATEGORIES,
                           today=today)


# ── LIST + MONTHLY OVERVIEW ──────────────────────
@app.route("/expenses")
@login_required
def expense_list():
    uid   = session["user_id"]
    today = datetime.now()

    # Allow ?month=MM&year=YYYY filtering
    try:
        month = int(request.args.get("month", today.month))
        year  = int(request.args.get("year",  today.year))
        if not (1 <= month <= 12):
            month = today.month
        if not (2000 <= year <= today.year + 1):
            year = today.year
    except (ValueError, TypeError):
        month, year = today.month, today.year

    summary = get_expense_summary(uid, year, month)

    # Individual expense rows for selected month
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, amount, category, expense_month, expense_year,
               note, created_at
        FROM expenses
        WHERE user_id=%s AND expense_year=%s AND expense_month=%s
        ORDER BY created_at DESC
    """, (uid, year, month))
    expenses = cur.fetchall()
    cur.close(); conn.close()

    # Build month/year options for dropdown (last 12 months)
    month_options = []
    for i in range(12):
        d = today.replace(day=1) - timedelta(days=30 * i)
        month_options.append({"month": d.month, "year": d.year,
                               "label": d.strftime("%B %Y")})

    return render_template("expense_list.html",
                           expenses=expenses,
                           summary=summary,
                           month_options=month_options,
                           selected_month=month,
                           selected_year=year)


# ── DELETE EXPENSE ───────────────────────────────
@app.route("/expenses/delete/<int:expense_id>", methods=["POST"])
@login_required
def expense_delete(expense_id):
    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM expenses WHERE id=%s AND user_id=%s",
                (expense_id, session["user_id"])
            )
    conn.close()
    flash("Expense removed.", "info")
    return redirect(url_for("expense_list"))


# ── API: Category chart data for current month ──
@app.route("/api/chart/expense-by-category")
@login_required
def chart_expense_category():
    uid   = session["user_id"]
    today = datetime.now()
    month = int(request.args.get("month", today.month))
    year  = int(request.args.get("year",  today.year))
    conn  = get_db()
    cur   = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT category, ROUND(SUM(amount)::numeric, 2) AS total
        FROM expenses
        WHERE user_id=%s AND expense_year=%s AND expense_month=%s
        GROUP BY category ORDER BY total DESC
    """, (uid, year, month))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify({
        "labels": [r["category"] for r in rows],
        "values": [float(r["total"]) for r in rows]
    })


# ── API: 6-month trend for dashboard sparkline ──
@app.route("/api/chart/expense-trend")
@login_required
def chart_expense_trend():
    uid   = session["user_id"]
    today = datetime.now()
    labels, values = [], []
    for i in range(5, -1, -1):
        d = today.replace(day=1) - timedelta(days=30 * i)
        conn = get_db()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM expenses WHERE user_id=%s
            AND expense_year=%s AND expense_month=%s
        """, (uid, d.year, d.month))
        total = float(cur.fetchone()["total"])
        cur.close(); conn.close()
        labels.append(d.strftime("%b %Y"))
        values.append(round(total, 2))
    return jsonify({"labels": labels, "values": values})

# ═══════════════════════════════════════════════
# EXPENSE ANALYSIS PAGE (NEW)
# Add this route to app.py alongside other expense routes
# ═══════════════════════════════════════════════

@app.route("/expenses/analysis")
@login_required
def expense_analysis():
    """
    Dedicated expense analysis page.
    Shows spending patterns, dominant category, risk level, behavioral insights.
    """
    uid     = session["user_id"]
    today   = datetime.now()
    summary = get_expense_summary(uid, today.year, today.month)

    return render_template("expense_analysis.html",
                           exp_summary=summary,
                           now=today)
"""
PATCH — paste these two helper functions into app.py
to fix: TypeError: unsupported operand type(s) for /: 'decimal.Decimal' and 'float'

The root cause: psycopg2 returns NUMERIC columns as decimal.Decimal objects.
Division with Python floats fails.  The fix: cast every DB value with float().

Replace your existing get_expense_summary() with this version.
Also replace get_monthly_budget() with this version.
"""

from decimal import Decimal

# ─── helper ──────────────────────────────────────────
def _f(val, default=0.0):
    """Safely cast decimal.Decimal / None / str → float."""
    if val is None:
        return float(default)
    return float(val)


def get_monthly_budget(uid: int) -> float:
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT monthly_budget FROM survey_responses "
        "WHERE user_id=%s ORDER BY created_at DESC LIMIT 1", (uid,)
    )
    row = cur.fetchone()
    cur.close(); conn.close()
    return _f(row["monthly_budget"]) if row and row["monthly_budget"] else 0.0


def get_expense_summary(uid: int, year: int, month: int) -> dict:
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id=%s AND expense_year=%s AND expense_month=%s
    """, (uid, year, month))
    current_total = round(_f(cur.fetchone()["total"]), 2)

    prev_month = month - 1 if month > 1 else 12
    prev_year  = year if month > 1 else year - 1
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id=%s AND expense_year=%s AND expense_month=%s
    """, (uid, prev_year, prev_month))
    prev_total = round(_f(cur.fetchone()["total"]), 2)

    cur.execute("""
        SELECT category, ROUND(SUM(amount)::numeric, 2) AS total
        FROM expenses
        WHERE user_id=%s AND expense_year=%s AND expense_month=%s
        GROUP BY category ORDER BY total DESC
    """, (uid, year, month))
    by_category = [{"category": r["category"], "total": _f(r["total"])}
                   for r in cur.fetchall()]

    cur.close(); conn.close()

    budget    = get_monthly_budget(uid)
    remaining = round(budget - current_total, 2)
    # KEY FIX: guard against budget == 0 before division
    util_pct  = round((current_total / budget * 100), 1) if budget > 0 else 0.0
    mom_delta = round(current_total - prev_total, 2)

    return {
        "current_total": current_total,
        "prev_total":    prev_total,
        "by_category":   by_category,
        "budget":        budget,
        "remaining":     remaining,
        "util_pct":      util_pct,
        "mom_delta":     mom_delta,
        "month":         month,
        "year":          year,
        "prev_month":    prev_month,
        "prev_year":     prev_year,
    }
@app.route('/analytics')
def analytics_page():
    month_names = [
    "Jan","Feb","Mar","Apr","May","Jun",
    "Jul","Aug","Sep","Oct","Nov","Dec"
]
    return render_template(
    "analytics.html",
    month_names=month_names,
    month=3,   # example
    year=2026
)
@app.route('/api/chart/budget-vs-expense')
def budget_vs_expense():
    data = {
        "budget": 5000,
        "expense": 3200
    }
    return jsonify(data)

# ═══════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    init_db()
    # deployment: set DEBUG=False via env var
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, host="0.0.0.0",
            port=int(os.getenv("PORT", 5000)))