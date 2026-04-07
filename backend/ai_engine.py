import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os


def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg2.connect(
            db_url.replace("postgres://", "postgresql://", 1),
            sslmode="require",
        )
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "wardrobe_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "wardrobe123"),
        port=os.getenv("DB_PORT", "5432"),
    )


def calculate_financial_health(uid, year, month):
    """Returns a 0–100 health score for the given user/month."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Budget
            cur.execute(
                "SELECT amount FROM budgets WHERE user_id=%s AND year=%s AND month=%s",
                (uid, year, month),
            )
            b_row = cur.fetchone()
            if not b_row:
                cur.execute("SELECT monthly_budget FROM users WHERE id=%s", (uid,))
                u_row = cur.fetchone()
                budget = float(u_row["monthly_budget"]) if u_row and u_row["monthly_budget"] else 0.0
            else:
                budget = float(b_row["amount"])

            # Total spent
            cur.execute(
                "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses "
                "WHERE user_id=%s AND expense_year=%s AND expense_month=%s",
                (uid, year, month),
            )
            spent = float(cur.fetchone()["total"])

            # Savings goals
            cur.execute(
                "SELECT COALESCE(SUM(saved_amount), 0) AS total_saved, "
                "COALESCE(SUM(target_amount), 0) AS total_target "
                "FROM goals WHERE user_id=%s",
                (uid,),
            )
            goals_data = cur.fetchone()
            total_saved = float(goals_data["total_saved"])
            total_target = float(goals_data["total_target"])
    finally:
        conn.close()

    if budget <= 0:
        return 50  # Default if no budget set

    score = 100
    utilization = spent / budget

    if utilization > 1.0:
        score -= min(50, (utilization - 1.0) * 100)  # Penalty for overspending
    elif utilization > 0.8:
        score -= (utilization - 0.8) * 50  # Small penalty for nearing limit

    # Savings boost
    if total_target > 0 and total_saved > 0:
        savings_ratio = total_saved / total_target
        score += min(15, savings_ratio * 15)

    return max(0, min(100, int(score)))


def generate_insights(uid):
    """Generate AI-style insights for a user based on their expenses and wardrobe."""
    today = datetime.now()
    month, year = today.month, today.year

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Expense by category
            cur.execute(
                "SELECT category, SUM(amount) AS total FROM expenses "
                "WHERE user_id=%s AND expense_year=%s AND expense_month=%s "
                "GROUP BY category",
                (uid, year, month),
            )
            cats = cur.fetchall()

            # Monthly budget
            cur.execute("SELECT monthly_budget FROM users WHERE id=%s", (uid,))
            b_row = cur.fetchone()
            budget = float(b_row["monthly_budget"]) if b_row and b_row["monthly_budget"] else 0.0

            # Wardrobe items
            cur.execute("SELECT * FROM wardrobe_items WHERE user_id=%s", (uid,))
            wardrobe = cur.fetchall()
    finally:
        conn.close()

    insights = []

    # --- Financial Recommendations ---
    total_spent = sum(float(c["total"]) for c in cats)
    if budget > 0:
        if total_spent > budget:
            insights.append({
                "type": "finance",
                "level": "danger",
                "message": (
                    f"You have overspent your budget by ₹{total_spent - budget:,.0f}. "
                    "Stop discretionary spending immediately."
                ),
            })
        elif total_spent > budget * 0.8:
            insights.append({
                "type": "finance",
                "level": "warning",
                "message": (
                    f"You have used {(total_spent / budget) * 100:.0f}% of your budget. "
                    "Slow down on non-essential purchases."
                ),
            })

        # Per-category alerts
        for c in cats:
            cat_total = float(c["total"])
            if cat_total > budget * 0.4:
                insights.append({
                    "type": "finance",
                    "level": "warning",
                    "message": (
                        f"You spent {(cat_total / budget) * 100:.0f}% of your budget on "
                        f"{c['category']}. Try reducing this by 15%."
                    ),
                })

    # --- Wardrobe + Shopping Cross-Insight ---
    shopping_spend = sum(
        float(c["total"]) for c in cats if c["category"].lower() == "shopping"
    )
    if shopping_spend > 0 and len(wardrobe) > 0:
        # FIX: was `for i in wardrobe` with `item['wear_count']` — variable mismatch
        total_wears = sum(int(item["wear_count"] or 0) for item in wardrobe)
        utilization_index = total_wears / len(wardrobe)
        if utilization_index < 3:
            insights.append({
                "type": "combined",
                "level": "warning",
                "message": (
                    f"You spent ₹{shopping_spend:,.0f} on shopping but wear your clothes "
                    f"rarely (avg {utilization_index:.1f} wears). Reuse items before buying new ones."
                ),
            })

    # --- Wardrobe Recommendations ---
    if len(wardrobe) > 0:
        unworn_items = [i for i in wardrobe if int(i["wear_count"] or 0) == 0]
        if unworn_items:
            insights.append({
                "type": "wardrobe",
                "level": "info",
                "message": (
                    f"You have {len(unworn_items)} unworn item(s). "
                    "Let's style them — start with something new tomorrow!"
                ),
            })

        high_cpw = []
        for item in wardrobe:
            price = float(item["purchase_price"] or 0)
            wears = int(item["wear_count"] or 0)
            cpw = price / wears if wears > 0 else price
            if cpw > 500:
                high_cpw.append(item)

        if high_cpw:
            insights.append({
                "type": "wardrobe",
                "level": "warning",
                "message": (
                    f"You have {len(high_cpw)} item(s) with very high cost-per-wear. "
                    "Avoid buying similar pieces until you wear these more."
                ),
            })

    # Fallback positive message
    if not insights:
        insights.append({
            "type": "finance",
            "level": "success",
            "message": "Your financial and wardrobe health looks great. Keep it up!",
        })

    # Sort by severity: danger first
    severity = {"danger": 0, "warning": 1, "info": 2, "success": 3}
    insights.sort(key=lambda x: severity.get(x["level"], 10))

    return insights


def get_outfit_suggestion(uid):
    """Return a suggested outfit using least-worn items."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM wardrobe_items WHERE user_id=%s ORDER BY wear_count ASC",
                (uid,),
            )
            items = cur.fetchall()

        top = next(
            (i for i in items if i["category"] and i["category"].lower() in
             ["top", "shirt", "tshirt", "blouse"]),
            None,
        )
        bottom = next(
            (i for i in items if i["category"] and i["category"].lower() in
             ["bottom", "jeans", "pants", "skirt", "trousers"]),
            None,
        )
        shoes = next(
            (i for i in items if i["category"] and i["category"].lower() in
             ["shoes", "sneakers", "boots", "heels"]),
            None,
        )
        return {"top": top, "bottom": bottom, "shoes": shoes}
    finally:
        conn.close()