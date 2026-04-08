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