"""
analysis_services.py
fenora – Data Intelligence Layer
Provides expense analysis, wardrobe analysis, and recommendation engine.
Drop this file into: wardrobe-analysis-project/backend/
"""

from datetime import datetime, date
import calendar


# ─────────────────────────────────────────
# EXPENSE ANALYSIS SERVICE
# ─────────────────────────────────────────

def analyze_expenses(expenses: list, budget: float = 10000) -> dict:
    """
    Input: list of expense dicts with keys:
        amount, category, created_at (ISO string or date)
    Returns structured insights dict.
    """
    if not expenses:
        return {"insights": [], "category_totals": {}, "monthly_totals": {}, "total": 0}

    now = datetime.now()
    this_month = now.month
    this_year = now.year
    last_month = this_month - 1 if this_month > 1 else 12
    last_month_year = this_year if this_month > 1 else this_year - 1

    category_totals = {}
    monthly_totals = {}
    this_month_total = 0
    last_month_total = 0
    category_last_month = {}

    for exp in expenses:
        amount = float(exp.get("amount", 0))
        category = exp.get("category", "Others")
        raw_date = exp.get("created_at") or exp.get("date")

        # Parse date
        if isinstance(raw_date, str):
            try:
                dt = datetime.fromisoformat(raw_date[:10])
            except Exception:
                dt = now
        elif isinstance(raw_date, (datetime, date)):
            dt = raw_date if isinstance(raw_date, datetime) else datetime.combine(raw_date, datetime.min.time())
        else:
            dt = now

        # Category totals (all time)
        category_totals[category] = category_totals.get(category, 0) + amount

        # Monthly totals
        month_key = f"{dt.year}-{dt.month:02d}"
        monthly_totals[month_key] = monthly_totals.get(month_key, 0) + amount

        # This month vs last month
        if dt.month == this_month and dt.year == this_year:
            this_month_total += amount
        if dt.month == last_month and dt.year == last_month_year:
            last_month_total += amount
            category_last_month[category] = category_last_month.get(category, 0) + amount

    total = sum(category_totals.values())

    # Build insights
    insights = []

    # Budget insight
    if budget > 0:
        pct = (this_month_total / budget) * 100
        if pct > 90:
            insights.append({
                "type": "danger",
                "icon": "🚨",
                "text": f"You've used {pct:.0f}% of your ₹{budget:,.0f} monthly budget. You're almost out!"
            })
        elif pct > 70:
            insights.append({
                "type": "warning",
                "icon": "⚠️",
                "text": f"You've spent ₹{this_month_total:,.0f} ({pct:.0f}% of budget). Slow down this week."
            })
        else:
            insights.append({
                "type": "success",
                "icon": "✅",
                "text": f"Good job! You've used only {pct:.0f}% of your budget this month."
            })

    # Top category insight
    if category_totals:
        top_cat = max(category_totals, key=category_totals.get)
        top_pct = (category_totals[top_cat] / total * 100) if total > 0 else 0
        insights.append({
            "type": "info",
            "icon": "📊",
            "text": f"You spent {top_pct:.0f}% of your total on {top_cat} — that's your biggest category."
        })

    # Month-over-month change
    if last_month_total > 0 and this_month_total > 0:
        change_pct = ((this_month_total - last_month_total) / last_month_total) * 100
        if change_pct > 20:
            insights.append({
                "type": "warning",
                "icon": "📈",
                "text": f"Your spending increased by {change_pct:.0f}% compared to last month. Watch out!"
            })
        elif change_pct < -10:
            insights.append({
                "type": "success",
                "icon": "📉",
                "text": f"Great! You cut spending by {abs(change_pct):.0f}% from last month."
            })

    # Category spike
    for cat, amt in category_totals.items():
        prev = category_last_month.get(cat, 0)
        if prev > 0 and (amt - prev) / prev > 0.3:
            savings_possible = round((amt - prev) * 0.5)
            insights.append({
                "type": "warning",
                "icon": "💸",
                "text": f"Your {cat} spending jumped {((amt-prev)/prev*100):.0f}% vs last month. Cutting back could save ₹{savings_possible:,}."
            })

    return {
        "insights": insights,
        "category_totals": category_totals,
        "monthly_totals": dict(sorted(monthly_totals.items())),
        "total": total,
        "this_month_total": this_month_total,
        "last_month_total": last_month_total,
        "budget_used_pct": round((this_month_total / budget * 100) if budget > 0 else 0, 1)
    }


# ─────────────────────────────────────────
# WARDROBE ANALYSIS SERVICE
# ─────────────────────────────────────────

def analyze_wardrobe(items: list) -> dict:
    """
    Input: list of wardrobe item dicts with keys:
        id, item_name, category, purchase_price, wear_count
    Returns structured wardrobe insights.
    """
    if not items:
        return {"insights": [], "utilization_data": [], "never_worn": [], "best_value": None}

    insights = []
    total_value = sum(float(i.get("purchase_price", 0)) for i in items)

    # Never worn items
    never_worn = [i for i in items if int(i.get("wear_count", 0)) == 0]
    rarely_worn = [i for i in items if 0 < int(i.get("wear_count", 0)) <= 2]

    if never_worn:
        wasted = sum(float(i.get("purchase_price", 0)) for i in never_worn)
        names = ", ".join(i.get("item_name", "?") for i in never_worn[:3])
        suffix = f" and {len(never_worn)-3} more" if len(never_worn) > 3 else ""
        insights.append({
            "type": "warning",
            "icon": "👕",
            "text": f"{len(never_worn)} item(s) never worn ({names}{suffix}) — that's ₹{wasted:,.0f} sitting idle in your wardrobe."
        })

    if rarely_worn:
        insights.append({
            "type": "info",
            "icon": "🔄",
            "text": f"{len(rarely_worn)} item(s) worn only 1–2 times. Try styling them differently before buying new clothes."
        })

    # Best value item (lowest cost-per-wear)
    worn_items = [i for i in items if int(i.get("wear_count", 0)) > 0 and float(i.get("purchase_price", 0)) > 0]
    best_value = None
    if worn_items:
        def cost_per_wear(item):
            return float(item.get("purchase_price", 1)) / max(int(item.get("wear_count", 1)), 1)
        best = min(worn_items, key=cost_per_wear)
        cpw = cost_per_wear(best)
        best_value = best
        insights.append({
            "type": "success",
            "icon": "🏆",
            "text": f"'{best.get('item_name')}' is your best investment — only ₹{cpw:.0f} per wear!"
        })

    # Category breakdown for bar chart
    category_wear = {}
    for item in items:
        cat = item.get("category", "Other")
        category_wear[cat] = category_wear.get(cat, 0) + int(item.get("wear_count", 0))

    # Utilization data for chart
    utilization_data = [
        {
            "name": i.get("item_name", "?")[:15],
            "wear_count": int(i.get("wear_count", 0)),
            "purchase_price": float(i.get("purchase_price", 0))
        }
        for i in sorted(items, key=lambda x: int(x.get("wear_count", 0)), reverse=True)[:8]
    ]

    return {
        "insights": insights,
        "utilization_data": utilization_data,
        "category_wear": category_wear,
        "never_worn": never_worn,
        "total_items": len(items),
        "total_wardrobe_value": total_value,
        "best_value": best_value
    }


# ─────────────────────────────────────────
# RECOMMENDATION SERVICE
# ─────────────────────────────────────────

def generate_recommendations(expense_analysis: dict, wardrobe_analysis: dict, budget: float = 10000) -> list:
    """
    Combines expense + wardrobe data to produce actionable recommendations.
    Returns list of recommendation dicts.
    """
    recs = []
    cat_totals = expense_analysis.get("category_totals", {})
    never_worn = wardrobe_analysis.get("never_worn", [])
    this_month = expense_analysis.get("this_month_total", 0)

    # Food/delivery recommendation
    food_cats = ["Food", "Dining", "Swiggy", "Zomato", "Restaurant", "food"]
    food_total = sum(cat_totals.get(c, 0) for c in food_cats)
    if food_total > 2000:
        save = round(food_total * 0.3)
        recs.append({
            "icon": "🍱",
            "title": "Cut Food Delivery",
            "text": f"You spent ₹{food_total:,.0f} on food/delivery this month. Reducing by 30% saves ₹{save:,}/month.",
            "priority": "high"
        })

    # Shopping + wardrobe combined recommendation
    shopping_cats = ["Shopping", "Clothes", "Fashion", "Clothing"]
    shopping_total = sum(cat_totals.get(c, 0) for c in shopping_cats)
    if shopping_total > 1500 and never_worn:
        recs.append({
            "icon": "🛍️",
            "title": "Pause Clothing Purchases",
            "text": f"You spent ₹{shopping_total:,.0f} on shopping but have {len(never_worn)} unworn item(s). Wear what you own first!",
            "priority": "high"
        })
    elif never_worn:
        recs.append({
            "icon": "👗",
            "title": "Use What You Have",
            "text": f"You have {len(never_worn)} unworn item(s). Style them before buying anything new this month.",
            "priority": "medium"
        })

    # Budget pacing
    budget_pct = expense_analysis.get("budget_used_pct", 0)
    today = datetime.now().day
    days_in_month = calendar.monthrange(datetime.now().year, datetime.now().month)[1]
    expected_pct = (today / days_in_month) * 100
    if budget_pct > expected_pct + 15:
        overpace = round(this_month - (budget * today / days_in_month))
        recs.append({
            "icon": "📅",
            "title": "Slow Your Spending Pace",
            "text": f"You're ₹{overpace:,} ahead of your daily budget pace. Avoid non-essential purchases for the next week.",
            "priority": "high"
        })

    # Entertainment
    ent_cats = ["Entertainment", "Movies", "Netflix", "OTT", "Subscriptions"]
    ent_total = sum(cat_totals.get(c, 0) for c in ent_cats)
    if ent_total > 500:
        recs.append({
            "icon": "🎬",
            "title": "Review Subscriptions",
            "text": f"₹{ent_total:,.0f} on entertainment. Check for duplicate OTT subscriptions you can cancel.",
            "priority": "low"
        })

    # Savings nudge
    if budget_pct < 60 and today > 15:
        potential_save = round(budget - this_month)
        recs.append({
            "icon": "💰",
            "title": "You Can Save This Month!",
            "text": f"You're on track to save ₹{potential_save:,} this month. Consider moving it to a savings goal!",
            "priority": "success"
        })

    return recs


# ─────────────────────────────────────────
# EMAIL REMINDER SERVICE
# ─────────────────────────────────────────

def build_monthly_email(user_name: str, expense_analysis: dict, wardrobe_analysis: dict, budget: float) -> dict:
    """
    Builds the subject and HTML body for the monthly summary email.
    Returns {"subject": ..., "html_body": ...}
    """
    total = expense_analysis.get("this_month_total", 0)
    budget_pct = expense_analysis.get("budget_used_pct", 0)
    cat_totals = expense_analysis.get("category_totals", {})
    never_worn_count = len(wardrobe_analysis.get("never_worn", []))

    month_name = calendar.month_name[(datetime.now().month - 1) or 12]

    if budget_pct > 100:
        status_line = f"⚠️ You overspent by ₹{total - budget:,.0f} this month."
        status_color = "#e74c3c"
    elif budget_pct > 80:
        status_line = f"Close call! You used {budget_pct:.0f}% of your budget."
        status_color = "#f39c12"
    else:
        status_line = f"Well done! You used only {budget_pct:.0f}% of your budget."
        status_color = "#27ae60"

    top_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)[:3]
    cats_html = "".join(
        f"<tr><td style='padding:6px 12px;'>{cat}</td><td style='padding:6px 12px;text-align:right;font-weight:600;'>₹{amt:,.0f}</td></tr>"
        for cat, amt in top_cats
    )

    html_body = f"""
    <div style="font-family:'Segoe UI',sans-serif;max-width:560px;margin:auto;background:#faf9f7;border-radius:16px;overflow:hidden;border:1px solid #ede9e3;">
      <div style="background:linear-gradient(135deg,#7c6fa0,#a89cc8);padding:32px;text-align:center;">
        <h1 style="color:#fff;margin:0;font-size:24px;">fenora Monthly Recap</h1>
        <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;">{month_name} Summary for {user_name}</p>
      </div>
      <div style="padding:28px;">
        <div style="background:#fff;border-radius:12px;padding:20px;margin-bottom:16px;border-left:4px solid {status_color};">
          <p style="margin:0;font-size:15px;color:#333;">{status_line}</p>
          <p style="margin:8px 0 0;font-size:28px;font-weight:700;color:#1a1a2e;">₹{total:,.0f} <span style="font-size:14px;color:#888;">/ ₹{budget:,.0f} budget</span></p>
        </div>
        <h3 style="color:#7c6fa0;margin:20px 0 10px;">Top Spending Categories</h3>
        <table style="width:100%;background:#fff;border-radius:12px;overflow:hidden;border-collapse:collapse;">
          <thead><tr style="background:#f3f0fa;"><th style="padding:8px 12px;text-align:left;color:#7c6fa0;">Category</th><th style="padding:8px 12px;text-align:right;color:#7c6fa0;">Amount</th></tr></thead>
          <tbody>{cats_html}</tbody>
        </table>
        {"<div style='background:#fff8ec;border-radius:12px;padding:16px;margin-top:16px;'><p style='margin:0;color:#856404;'>👗 You have <strong>" + str(never_worn_count) + " unworn items</strong> in your wardrobe. Try wearing them before buying new clothes!</p></div>" if never_worn_count > 0 else ""}
        <div style="margin-top:24px;text-align:center;">
          <a href="http://localhost:5173" style="background:#7c6fa0;color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;">View Full Dashboard →</a>
        </div>
      </div>
      <div style="padding:16px;text-align:center;color:#aaa;font-size:12px;">fenora · Smart Budget & Wardrobe Intelligence</div>
    </div>
    """

    return {
        "subject": f"fenora: Your {month_name} Financial Recap 📊",
        "html_body": html_body
    }

# ─────────────────────────────────────────
# DB-CONNECTED SERVICES
# These functions require a DB connection
# and are called directly from app.py routes.
# ─────────────────────────────────────────

import os
import psycopg2
import psycopg2.extras
from datetime import timedelta


def _get_db():
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


def _f(val, default=0.0):
    if val is None:
        return float(default)
    from decimal import Decimal
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


# ── Spending Heatmap ──────────────────────────────────────────────

def get_spending_heatmap(user_id: int, days: int = 90) -> list:
    """Returns daily spending levels for a calendar heatmap."""
    conn = _get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            start = datetime.now() - timedelta(days=days)
            cur.execute(
                "SELECT DATE(created_at) AS day, COALESCE(SUM(amount), 0) AS total "
                "FROM expenses WHERE user_id=%s AND created_at >= %s "
                "GROUP BY DATE(created_at) ORDER BY day ASC",
                (user_id, start),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    amounts = [_f(r["total"]) for r in rows]
    max_amt = max(amounts) if amounts else 1

    result = []
    for r in rows:
        amt = _f(r["total"])
        if amt == 0:
            level = 0
        elif amt <= max_amt * 0.25:
            level = 1
        elif amt <= max_amt * 0.5:
            level = 2
        elif amt <= max_amt * 0.75:
            level = 3
        else:
            level = 4
        result.append({
            "date": r["day"].isoformat() if hasattr(r["day"], "isoformat") else str(r["day"]),
            "amount": amt,
            "level": level,
        })
    return result


# ── Spending Personality ──────────────────────────────────────────

def detect_spending_personality(user_id: int) -> dict:
    """Classifies user's spending style based on patterns."""
    conn = _get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get last 3 months of category data
            start = datetime.now() - timedelta(days=90)
            cur.execute(
                "SELECT category, COALESCE(SUM(amount),0) AS total, COUNT(*) AS cnt "
                "FROM expenses WHERE user_id=%s AND created_at >= %s "
                "GROUP BY category ORDER BY total DESC",
                (user_id, start),
            )
            rows = cur.fetchall()
            cur.execute("SELECT monthly_budget FROM users WHERE id=%s", (user_id,))
            u = cur.fetchone()
            budget = _f(u["monthly_budget"] if u else 0)
            cur.execute(
                "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
                "WHERE user_id=%s AND created_at >= %s",
                (user_id, start),
            )
            total_spent = _f(cur.fetchone()["t"])
    finally:
        conn.close()

    if not rows:
        return {"personality": "explorer", "label": "Financial Explorer", "description": "You're just getting started! Keep logging expenses to discover your spending style.", "traits": ["Getting started"], "icon": "🌱", "color": "#3db88a"}

    cat_totals = {r["category"]: _f(r["total"]) for r in rows}
    total = sum(cat_totals.values()) or 1
    food_pct = (cat_totals.get("Food", 0) / total) * 100
    shopping_pct = (cat_totals.get("Shopping", 0) / total) * 100
    ent_pct = (cat_totals.get("Entertainment", 0) / total) * 100
    monthly_avg = total_spent / 3
    budget_ratio = (monthly_avg / budget) if budget > 0 else 1

    if budget_ratio > 1.1:
        return {"personality": "overspender", "label": "The Overspender", "description": "You consistently spend more than your budget. Small, consistent cuts will make a huge difference.", "traits": ["Over budget", "Impulse buyer", "Needs discipline"], "icon": "🚨", "color": "#e05c7d"}
    elif food_pct > 40:
        return {"personality": "foodie", "label": "The Foodie", "description": "Food is your biggest joy and biggest expense! Consider meal prepping to keep the love alive while saving.", "traits": ["Food lover", "Delivery habit", "Social spender"], "icon": "🍜", "color": "#f0803c"}
    elif shopping_pct > 35:
        return {"personality": "shopaholic", "label": "The Shopaholic", "description": "Retail therapy is real for you. Before each purchase, ask: will I use this 10+ times?", "traits": ["Fashion forward", "Impulse buyer", "Trend chaser"], "icon": "🛍️", "color": "#6d4fc2"}
    elif ent_pct > 25:
        return {"personality": "entertainer", "label": "The Entertainer", "description": "Life's too short for bad Netflix shows — but maybe one subscription too many?", "traits": ["Experience seeker", "Social butterfly", "OTT addict"], "icon": "🎬", "color": "#4a9ede"}
    elif budget_ratio < 0.7:
        return {"personality": "saver", "label": "The Super Saver", "description": "You're crushing it! You consistently stay well under budget. Put that surplus to work in savings goals.", "traits": ["Budget master", "Disciplined", "Goal-oriented"], "icon": "💰", "color": "#3db88a"}
    else:
        return {"personality": "balanced", "label": "The Balanced Spender", "description": "You're doing well — spending mindfully across categories without any major red flags.", "traits": ["Balanced", "Consistent", "Mindful"], "icon": "⚖️", "color": "#9577e0"}


# ── Anomaly Detection ─────────────────────────────────────────────

def detect_anomalies(user_id: int) -> list:
    """Flags unusually large or frequent expenses."""
    conn = _get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, amount, category, note, created_at FROM expenses "
                "WHERE user_id=%s ORDER BY created_at DESC LIMIT 100",
                (user_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    # Calculate average per category
    cat_amounts = {}
    for r in rows:
        cat = r["category"]
        cat_amounts.setdefault(cat, []).append(_f(r["amount"]))

    cat_avg = {c: sum(v) / len(v) for c, v in cat_amounts.items()}

    anomalies = []
    for r in rows:
        cat = r["category"]
        amt = _f(r["amount"])
        avg = cat_avg.get(cat, amt)
        if avg > 0 and amt > avg * 2.5 and amt > 500:
            anomalies.append({
                "id": r["id"],
                "amount": amt,
                "category": cat,
                "note": r.get("note") or "",
                "date": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"]),
                "reason": f"₹{amt:,.0f} is {(amt/avg):.1f}x your usual {cat} spend (avg ₹{avg:,.0f})",
            })
    return anomalies[:5]


# ── Recurring Expenses ────────────────────────────────────────────

def detect_recurring_expenses(user_id: int) -> list:
    """Finds expenses that appear every month (subscriptions, rent, etc)."""
    conn = _get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT category, note, ROUND(AVG(amount)::numeric, 0) AS avg_amount, COUNT(*) AS occurrences "
                "FROM expenses WHERE user_id=%s AND created_at >= NOW() - INTERVAL '3 months' "
                "AND note IS NOT NULL AND note != '' "
                "GROUP BY category, note HAVING COUNT(*) >= 2 ORDER BY avg_amount DESC",
                (user_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [
        {
            "category": r["category"],
            "note": r["note"],
            "avg_amount": _f(r["avg_amount"]),
            "occurrences": int(r["occurrences"]),
            "label": f"{r['note']} — ₹{_f(r['avg_amount']):,.0f}/month (seen {r['occurrences']}x)",
        }
        for r in rows
    ]


# ── Savings Streak ────────────────────────────────────────────────

def calculate_savings_streak(user_id: int) -> dict:
    """Counts consecutive days the user stayed under their daily budget."""
    conn = _get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT monthly_budget FROM users WHERE id=%s", (user_id,))
            u = cur.fetchone()
            budget = _f(u["monthly_budget"] if u else 0)
            cur.execute(
                "SELECT DATE(created_at) AS day, COALESCE(SUM(amount),0) AS total "
                "FROM expenses WHERE user_id=%s AND created_at >= NOW() - INTERVAL '60 days' "
                "GROUP BY DATE(created_at) ORDER BY day DESC",
                (user_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    if budget <= 0 or not rows:
        return {"streak": 0, "best_streak": 0, "daily_budget": 0, "message": "Set a monthly budget to track your savings streak!"}

    daily_budget = budget / 30
    daily_spend = {r["day"]: _f(r["total"]) for r in rows}

    today = datetime.now().date()
    streak = 0
    best_streak = 0
    current = 0
    d = today

    for i in range(60):
        spend = daily_spend.get(d, 0)
        if spend <= daily_budget:
            current += 1
            best_streak = max(best_streak, current)
            if i < streak + 1:
                streak = current
        else:
            if i == 0:
                streak = 0
            current = 0
        d = d - timedelta(days=1)

    msg = (
        f"🔥 {streak}-day streak! You've stayed under ₹{daily_budget:,.0f}/day." if streak > 0
        else "Start your streak by staying under budget today!"
    )

    return {
        "streak": streak,
        "best_streak": best_streak,
        "daily_budget": round(daily_budget, 2),
        "message": msg,
    }


# ── Budget Suggestion ─────────────────────────────────────────────

def suggest_budget(user_id: int) -> dict:
    """Suggests a realistic monthly budget based on 3-month spending history."""
    conn = _get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            now = datetime.now()
            monthly_totals = []
            for i in range(1, 4):
                m = now.month - i
                y = now.year
                if m <= 0:
                    m += 12
                    y -= 1
                cur.execute(
                    "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
                    "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s",
                    (user_id, m, y),
                )
                t = _f(cur.fetchone()["t"])
                if t > 0:
                    monthly_totals.append(t)

            cur.execute(
                "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
                "WHERE user_id=%s AND created_at >= NOW() - INTERVAL '3 months' "
                "GROUP BY category ORDER BY total DESC",
                (user_id,),
            )
            cats = {r["category"]: _f(r["total"]) / 3 for r in cur.fetchall()}
    finally:
        conn.close()

    if not monthly_totals:
        return {"suggested": 10000, "reason": "Not enough history. Suggested ₹10,000 as a starting point.", "category_breakdown": {}}

    avg_monthly = sum(monthly_totals) / len(monthly_totals)
    suggested = round(avg_monthly * 1.1 / 500) * 500  # 10% buffer, rounded to nearest 500

    return {
        "suggested": suggested,
        "avg_spent_3mo": round(avg_monthly, 2),
        "reason": f"Based on your avg ₹{avg_monthly:,.0f}/month over the last {len(monthly_totals)} months, with a 10% buffer.",
        "category_breakdown": {k: round(v, 2) for k, v in cats.items()},
    }


# ── Weekly Report ─────────────────────────────────────────────────

def generate_weekly_report(user_id: int) -> dict:
    """Generates a structured weekly spending report with real data."""
    conn = _get_db()
    now = datetime.now()
    this_week_start = now - timedelta(days=7)
    last_week_start = now - timedelta(days=14)
    last_week_end = now - timedelta(days=7)

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
                "WHERE user_id=%s AND created_at >= %s",
                (user_id, this_week_start),
            )
            this_week = _f(cur.fetchone()["t"])

            cur.execute(
                "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
                "WHERE user_id=%s AND created_at >= %s AND created_at < %s",
                (user_id, last_week_start, last_week_end),
            )
            last_week = _f(cur.fetchone()["t"])

            cur.execute(
                "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
                "WHERE user_id=%s AND created_at >= %s "
                "GROUP BY category ORDER BY total DESC LIMIT 1",
                (user_id, this_week_start),
            )
            top_row = cur.fetchone()
            top_category = top_row["category"] if top_row else "—"

            cur.execute("SELECT monthly_budget FROM users WHERE id=%s", (user_id,))
            u = cur.fetchone()
            budget = _f(u["monthly_budget"] if u else 0)
    finally:
        conn.close()

    daily_avg = this_week / 7
    weekly_budget = budget / 4.33 if budget > 0 else 0
    change_pct = ((this_week - last_week) / last_week * 100) if last_week > 0 else 0

    insights = []
    if this_week == 0:
        insights.append({"icon": "💡", "text": "No expenses logged this week. Start tracking!"})
    elif weekly_budget > 0 and this_week > weekly_budget:
        insights.append({"icon": "⚠️", "text": f"Over weekly budget by ₹{this_week - weekly_budget:,.0f}."})
    elif change_pct > 20:
        insights.append({"icon": "📈", "text": f"Spending up {change_pct:.0f}% vs last week."})
    elif change_pct < -10:
        insights.append({"icon": "📉", "text": f"Spending down {abs(change_pct):.0f}% vs last week! Great job."})
    else:
        insights.append({"icon": "✅", "text": f"Spending steady at ₹{daily_avg:,.0f}/day this week."})

    return {
        "this_week_total": this_week,
        "last_week_total": last_week,
        "this_week": this_week,
        "last_week": last_week,
        "daily_avg": round(daily_avg, 2),
        "top_category": top_category,
        "weekly_budget": round(weekly_budget, 2),
        "change_pct": round(change_pct, 1),
        "weekly_insights": insights,
    }


# ── Category Budget Status ────────────────────────────────────────

def get_category_budget_status(user_id: int) -> list:
    """Returns each category cap vs actual spend this month."""
    conn = _get_db()
    now = datetime.now()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT category, cap_amount FROM category_budgets WHERE user_id=%s",
                (user_id,),
            )
            caps = {r["category"]: _f(r["cap_amount"]) for r in cur.fetchall()}

            cur.execute(
                "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
                "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s "
                "GROUP BY category",
                (user_id, now.month, now.year),
            )
            actuals = {r["category"]: _f(r["total"]) for r in cur.fetchall()}
    finally:
        conn.close()

    result = []
    for cat, cap in caps.items():
        actual = actuals.get(cat, 0)
        pct = (actual / cap * 100) if cap > 0 else 0
        result.append({
            "category": cat,
            "cap_amount": cap,
            "spent": actual,
            "remaining": max(0, cap - actual),
            "pct_used": round(pct, 1),
            "status": "danger" if pct >= 90 else "warning" if pct >= 70 else "ok",
        })
    return sorted(result, key=lambda x: -x["pct_used"])


# ── Monthly Recap ─────────────────────────────────────────────────

def get_monthly_recap(user_id: int, year: int, month: int) -> dict:
    """Full monthly recap with comparisons."""
    conn = _get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
                "WHERE user_id=%s AND EXTRACT(YEAR FROM created_at)=%s AND EXTRACT(MONTH FROM created_at)=%s "
                "GROUP BY category ORDER BY total DESC",
                (user_id, year, month),
            )
            cats = {r["category"]: _f(r["total"]) for r in cur.fetchall()}
            total = sum(cats.values())

            prev_month = month - 1 if month > 1 else 12
            prev_year = year if month > 1 else year - 1
            cur.execute(
                "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
                "WHERE user_id=%s AND EXTRACT(YEAR FROM created_at)=%s AND EXTRACT(MONTH FROM created_at)=%s",
                (user_id, prev_year, prev_month),
            )
            prev_total = _f(cur.fetchone()["t"])

            cur.execute("SELECT monthly_budget FROM users WHERE id=%s", (user_id,))
            u = cur.fetchone()
            budget = _f(u["monthly_budget"] if u else 0)

            cur.execute(
                "SELECT COUNT(*) AS c FROM wardrobe_items WHERE user_id=%s AND wear_count=0",
                (user_id,),
            )
            never_worn = int(cur.fetchone()["c"])
    finally:
        conn.close()

    mom_change = ((total - prev_total) / prev_total * 100) if prev_total > 0 else 0
    budget_pct = (total / budget * 100) if budget > 0 else 0

    return {
        "month": month,
        "year": year,
        "total": total,
        "budget": budget,
        "budget_pct": round(budget_pct, 1),
        "prev_month_total": prev_total,
        "mom_change_pct": round(mom_change, 1),
        "category_breakdown": cats,
        "never_worn_count": never_worn,
        "status": "over" if budget_pct > 100 else "warning" if budget_pct > 80 else "ok",
    }