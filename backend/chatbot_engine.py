"""
chatbot_engine.py — fenora Smart Financial Chatbot Engine
==========================================================
Drop into: wardrobe-analysis-project/backend/chatbot_engine.py

Import in app.py with one line:
    from chatbot_engine import handle_chat_message

Then register the route:
    @app.route("/api/smart-chat", methods=["POST"])
    @login_required
    def api_smart_chat():
        uid  = get_uid()
        data = request.json or {}
        msg  = (data.get("message") or data.get("question_key") or "").strip()
        result = handle_chat_message(uid, msg, get_db)
        return jsonify(result)
"""

import re
import os
import logging
import calendar as _cal
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# HELPER UTILITIES
# ─────────────────────────────────────────────────────────────────────

def _f(val, default=0.0):
    if val is None:
        return float(default)
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


def _inr(n):
    """Format a number as Indian Rupees string."""
    return "₹{:,.0f}".format(float(n or 0))


def _extract_amount(text: str) -> float:
    """
    Extract a rupee amount from a natural language string.
    Handles: '₹2000', 'rs 2000', '2,000', '2k', '2.5k', '15000'
    Returns 0.0 if not found.
    """
    text_lower = text.lower().strip()

    # Handle "2k", "2.5k", "5k" format
    k_match = re.search(r'(\d+(?:\.\d+)?)\s*k\b', text_lower)
    if k_match:
        return float(k_match.group(1)) * 1000

    # Handle "2 lakh", "2.5 lakh" format
    lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*lakh', text_lower)
    if lakh_match:
        return float(lakh_match.group(1)) * 100000

    # Handle ₹ or Rs or rs followed by number
    rupee_match = re.search(r'(?:₹|rs\.?|inr)\s*(\d[\d,]*(?:\.\d+)?)', text_lower)
    if rupee_match:
        return float(rupee_match.group(1).replace(",", ""))

    # Find any standalone number in the string (last resort)
    numbers = re.findall(r'\b(\d[\d,]*(?:\.\d+)?)\b', text)
    if numbers:
        # Return the largest number found (most likely the amount)
        candidates = [float(n.replace(",", "")) for n in numbers]
        return max(candidates)

    return 0.0


# ─────────────────────────────────────────────────────────────────────
# DATABASE DATA FETCHER
# ─────────────────────────────────────────────────────────────────────

def _fetch_user_context(uid: int, get_db_fn) -> dict:
    """
    Fetches all financial context needed to answer any question.
    Returns a rich context dict.
    """
    import psycopg2.extras

    conn = get_db_fn()
    ctx = {}

    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        today = datetime.now()

        # ── User info ──────────────────────────────────────────────
        cur.execute("SELECT name, email, monthly_budget FROM users WHERE id=%s", (uid,))
        user = cur.fetchone()
        ctx["budget"]     = _f(user["monthly_budget"] if user else 0)
        ctx["name"]       = (user.get("name") or "there").split()[0] if user else "there"
        ctx["user_email"] = user.get("email", "") if user else ""

        # ── This month spending ────────────────────────────────────
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
            "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s",
            (uid, today.month, today.year),
        )
        ctx["spent"] = _f(cur.fetchone()["t"])

        # ── Category breakdown this month ──────────────────────────
        cur.execute(
            "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
            "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s "
            "GROUP BY category ORDER BY total DESC",
            (uid, today.month, today.year),
        )
        ctx["categories"] = {r["category"]: _f(r["total"]) for r in cur.fetchall()}
        ctx["top_category"] = max(ctx["categories"].items(), key=lambda x: x[1]) if ctx["categories"] else None

        # ── Last month spending ────────────────────────────────────
        last_m = today.replace(day=1) - timedelta(days=1)
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
            "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s",
            (uid, last_m.month, last_m.year),
        )
        ctx["last_month_spent"] = _f(cur.fetchone()["t"])

        # ── Today's spending ───────────────────────────────────────
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
            "WHERE user_id=%s AND DATE(created_at) = %s",
            (uid, today.date()),
        )
        ctx["today_spent"] = _f(cur.fetchone()["t"])

        # ── Last 7 days ────────────────────────────────────────────
        week_start = today - timedelta(days=7)
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
            "WHERE user_id=%s AND created_at >= %s",
            (uid, week_start),
        )
        ctx["week_spent"] = _f(cur.fetchone()["t"])

        # ── Wardrobe ───────────────────────────────────────────────
        cur.execute(
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN wear_count=0 THEN 1 ELSE 0 END) AS never_worn "
            "FROM wardrobe_items WHERE user_id=%s",
            (uid,),
        )
        row = cur.fetchone()
        ctx["wardrobe_total"]  = int(row["total"] or 0)
        ctx["never_worn"]      = int(row["never_worn"] or 0)

        # ── Savings goals ──────────────────────────────────────────
        try:
            cur.execute(
                "SELECT name, target_amount, saved_amount, months FROM savings_goals "
                "WHERE user_id=%s ORDER BY created_at DESC LIMIT 3",
                (uid,),
            )
            ctx["goals"] = cur.fetchall()
        except Exception:
            ctx["goals"] = []

        # ── Mood spending (if column exists) ───────────────────────
        try:
            cur.execute(
                "SELECT mood, COALESCE(SUM(amount),0) AS t FROM expenses "
                "WHERE user_id=%s AND mood IS NOT NULL AND mood != '' "
                "AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s "
                "GROUP BY mood ORDER BY t DESC",
                (uid, today.month, today.year),
            )
            ctx["mood_spending"] = {r["mood"]: _f(r["t"]) for r in cur.fetchall()}
        except Exception:
            ctx["mood_spending"] = {}

        cur.close()

        # ── Derived values ─────────────────────────────────────────
        ctx["remaining"]   = max(0.0, ctx["budget"] - ctx["spent"])
        ctx["budget_pct"]  = (ctx["spent"] / ctx["budget"] * 100) if ctx["budget"] > 0 else 0
        ctx["days_left"]   = _cal.monthrange(today.year, today.month)[1] - today.day
        ctx["daily_budget"] = ctx["budget"] / _cal.monthrange(today.year, today.month)[1] if ctx["budget"] > 0 else 0
        ctx["daily_remaining"] = ctx["remaining"] / max(ctx["days_left"], 1)
        ctx["today"]       = today

    except Exception as e:
        logger.error(f"[chatbot_engine] Context fetch error for uid={uid}: {e}")
        ctx.setdefault("budget", 0)
        ctx.setdefault("spent", 0)
        ctx.setdefault("remaining", 0)
        ctx.setdefault("budget_pct", 0)
        ctx.setdefault("categories", {})
        ctx.setdefault("top_category", None)
        ctx.setdefault("last_month_spent", 0)
        ctx.setdefault("today_spent", 0)
        ctx.setdefault("week_spent", 0)
        ctx.setdefault("wardrobe_total", 0)
        ctx.setdefault("never_worn", 0)
        ctx.setdefault("goals", [])
        ctx.setdefault("mood_spending", {})
        ctx.setdefault("days_left", 15)
        ctx.setdefault("daily_budget", 0)
        ctx.setdefault("daily_remaining", 0)
        ctx.setdefault("name", "there")
        ctx.setdefault("user_email", "")
        ctx.setdefault("today", datetime.now())
    finally:
        conn.close()

    return ctx


# ─────────────────────────────────────────────────────────────────────
# INTENT DETECTION
# ─────────────────────────────────────────────────────────────────────

def _detect_intent(message: str) -> str:
    """
    Maps a user message to one of 15 intent categories.
    Returns the intent string.
    """
    msg = message.lower().strip()

    # ── AFFORD CHECK (highest priority — check first) ──────────────
    afford_patterns = [
        "can i afford", "can i buy", "should i buy",
        "is it okay to buy", "worth buying", "can i spend",
        "is ₹", "is rs", "purchase",
    ]
    if any(p in msg for p in afford_patterns):
        return "afford_check"

    # ── DAILY BUDGET ───────────────────────────────────────────────
    if any(p in msg for p in ["how much today", "spend today", "daily budget", "today's budget",
                               "how much can i spend today", "left for today"]):
        return "daily_budget"

    # ── REMAINING BUDGET ───────────────────────────────────────────
    if any(p in msg for p in ["how much left", "remaining budget", "budget left",
                               "how much do i have", "what's remaining", "how much remaining",
                               "balance", "left in budget"]):
        return "remaining_budget"

    # ── BUDGET STATUS ──────────────────────────────────────────────
    if any(p in msg for p in ["budget status", "show budget", "my budget", "budget okay",
                               "how is my budget", "budget check", "am i within budget"]):
        return "budget_status"

    # ── OVERSPENDING CHECK ─────────────────────────────────────────
    if any(p in msg for p in ["am i overspending", "overspend", "spending too much",
                               "am i over", "exceeded budget", "over budget"]):
        return "overspending_check"

    # ── MONTHLY SPENDING ───────────────────────────────────────────
    if any(p in msg for p in ["how much did i spend", "this month", "monthly spending",
                               "spent this month", "total spent", "total expenses", "what did i spend"]):
        return "monthly_spending"

    # ── TOP SPENDING CATEGORY ──────────────────────────────────────
    if any(p in msg for p in ["where am i spending", "top category", "most on",
                               "biggest expense", "spending the most", "where is my money",
                               "where does my money go"]):
        return "top_category"

    # ── HOW TO REDUCE / SAVE MORE ──────────────────────────────────
    if any(p in msg for p in ["how to reduce", "reduce expense", "cut spending",
                               "save more", "how to save", "saving tips",
                               "reduce my expenses", "spend less", "cut down"]):
        return "save_tips"

    # ── SAVINGS GOALS ─────────────────────────────────────────────
    if any(p in msg for p in ["goal", "goals", "saving for", "save for",
                               "target", "how much should i save"]):
        return "savings_goals"

    # ── SPENDING ADVICE (general) ──────────────────────────────────
    if any(p in msg for p in ["advice", "suggest", "recommendation",
                               "what should i do", "financial advice", "help me", "tips"]):
        return "spending_advice"

    # ── WEEK SUMMARY ───────────────────────────────────────────────
    if any(p in msg for p in ["this week", "weekly", "past 7 days", "last 7"]):
        return "weekly_summary"

    # ── MOOD SPENDING ─────────────────────────────────────────────
    if any(p in msg for p in ["mood", "stressed", "emotional", "sad shopping", "happy"]):
        return "mood_spending"

    # ── WARDROBE ──────────────────────────────────────────────────
    if any(p in msg for p in ["wardrobe", "clothes", "clothing", "outfit",
                               "never worn", "unworn"]):
        return "wardrobe_advice"

    # ── GREETING ──────────────────────────────────────────────────
    if any(p in msg for p in ["hi ", "hello", "hey ", "good morning",
                               "good afternoon", "good evening", "namaste", "hii"]):
        return "greeting"

    # ── GENERIC FALLBACK ─────────────────────────────────────────
    return "general_status"


# ─────────────────────────────────────────────────────────────────────
# RESPONSE GENERATORS  (one function per intent)
# ─────────────────────────────────────────────────────────────────────

def _reply_afford_check(ctx: dict, message: str) -> str:
    """
    THE CORE FEATURE.
    Calculates from live DB data whether the user can afford an amount.
    """
    amount = _extract_amount(message)
    budget    = ctx["budget"]
    spent     = ctx["spent"]
    remaining = ctx["remaining"]
    name      = ctx["name"]

    if budget == 0:
        return (
            "You haven't set a monthly budget yet! "
            "Set one from your dashboard first, then I can give you a proper afford-check. 💡"
        )

    if amount <= 0:
        # No amount extracted — give a generic "here's what you have" reply
        return (
            f"You currently have {_inr(remaining)} left in your budget this month "
            f"({_inr(spent)} spent of {_inr(budget)}). "
            "Tell me the exact amount and I'll check if you can afford it! "
            "E.g. 'Can I afford ₹2000?'"
        )

    # Core logic
    pct_of_remaining = (amount / remaining * 100) if remaining > 0 else 999
    new_pct = ((spent + amount) / budget * 100) if budget > 0 else 999

    if amount > remaining:
        shortfall = amount - remaining
        return (
            f"❌ Not recommended, {name}. "
            f"A {_inr(amount)} purchase would exceed your budget.\n\n"
            f"• You've already spent {_inr(spent)} of your {_inr(budget)} budget ({ctx['budget_pct']:.0f}%)\n"
            f"• Remaining: {_inr(remaining)}\n"
            f"• Shortfall: {_inr(shortfall)}\n\n"
            f"💡 Either wait until next month, or cut {_inr(shortfall)} from another category first."
        )
    elif pct_of_remaining > 70:
        return (
            f"⚠️ Technically yes, but risky, {name}. "
            f"A {_inr(amount)} purchase would use {pct_of_remaining:.0f}% of your remaining budget.\n\n"
            f"• Remaining before: {_inr(remaining)}\n"
            f"• Remaining after: {_inr(remaining - amount)}\n"
            f"• Budget used after: {new_pct:.0f}%\n\n"
            f"You'd only have {_inr(remaining - amount)} for the rest of the month. "
            f"{'That might be tight with ' + str(ctx['days_left']) + ' days to go.' if ctx['days_left'] > 5 else 'Month is almost over — should be fine!'}"
        )
    else:
        return (
            f"✅ Yes, you can afford {_inr(amount)}!\n\n"
            f"• Current remaining budget: {_inr(remaining)}\n"
            f"• After this purchase: {_inr(remaining - amount)} left\n"
            f"• Budget used after: {new_pct:.0f}%\n\n"
            f"You're still within a healthy range. Go for it! 🎉"
        )


def _reply_daily_budget(ctx: dict) -> str:
    budget     = ctx["budget"]
    remaining  = ctx["remaining"]
    days_left  = ctx["days_left"]
    today_spent = ctx["today_spent"]
    daily_rem  = ctx["daily_remaining"]
    daily_bud  = ctx["daily_budget"]

    if budget == 0:
        return "Set a monthly budget first to see your daily allowance! 💡"

    if days_left <= 0:
        return f"It's the last day of the month! You have {_inr(remaining)} remaining."

    over_today = today_spent > daily_bud

    return (
        f"📅 Here's your daily budget breakdown:\n\n"
        f"• Daily allowance (total): {_inr(daily_bud)}\n"
        f"• Already spent today: {_inr(today_spent)}\n"
        f"• You can spend today: {_inr(max(0, daily_bud - today_spent))}\n\n"
        f"Based on your remaining {_inr(remaining)} over {days_left} days:\n"
        f"• Flexible daily limit: {_inr(daily_rem)}/day\n\n"
        + ("⚠️ You've already exceeded today's daily limit!" if over_today
           else "✅ You're on track for today!")
    )


def _reply_remaining_budget(ctx: dict) -> str:
    budget    = ctx["budget"]
    spent     = ctx["spent"]
    remaining = ctx["remaining"]
    days_left = ctx["days_left"]
    name      = ctx["name"]

    if budget == 0:
        return "You haven't set a monthly budget yet. Go to your dashboard and set one! 💡"

    status = (
        "🚨 Budget critical!" if ctx["budget_pct"] >= 90
        else "⚠️ Getting tight!" if ctx["budget_pct"] >= 70
        else "✅ Looking healthy!"
    )

    return (
        f"{status}\n\n"
        f"💰 Budget Snapshot for {ctx['today'].strftime('%B')}:\n"
        f"• Total budget: {_inr(budget)}\n"
        f"• Spent so far: {_inr(spent)} ({ctx['budget_pct']:.0f}%)\n"
        f"• Remaining: {_inr(remaining)}\n"
        f"• Days left: {days_left}\n"
        f"• You can spend: {_inr(ctx['daily_remaining'])}/day\n\n"
        + (f"💡 You've spent {ctx['budget_pct']:.0f}% of your budget — be careful!"
           if ctx["budget_pct"] >= 70
           else f"Keep it up, {name}! You're managing well 🎉")
    )


def _reply_budget_status(ctx: dict) -> str:
    return _reply_remaining_budget(ctx)  # same logic, different entry point


def _reply_overspending(ctx: dict) -> str:
    budget    = ctx["budget"]
    spent     = ctx["spent"]
    remaining = ctx["remaining"]
    last_mo   = ctx["last_month_spent"]
    pct       = ctx["budget_pct"]
    days_left = ctx["days_left"]
    today     = ctx["today"]

    if budget == 0:
        return "Set a budget first so I can check if you're overspending! 💡"

    # Compare pace: expected vs actual
    days_elapsed = _cal.monthrange(today.year, today.month)[1] - days_left
    expected_pct = (days_elapsed / _cal.monthrange(today.year, today.month)[1]) * 100
    pace_gap = pct - expected_pct

    lines = [f"📊 Overspending check for {today.strftime('%B')}:\n"]

    if spent > budget:
        lines.append(f"🚨 YES — You're {_inr(spent - budget)} OVER budget!")
        lines.append(f"Stop all non-essential spending immediately.")
    elif pace_gap > 15:
        lines.append(f"⚠️ You're spending {pace_gap:.0f}% faster than your daily pace.")
        lines.append(f"At this rate, you'd overspend by month end.")
    else:
        lines.append(f"✅ No, you're within budget so far!")
        lines.append(f"Spent {pct:.0f}% with {days_left} days left — on track.")

    lines.append(f"\n• Spent: {_inr(spent)} of {_inr(budget)}")
    lines.append(f"• Remaining: {_inr(remaining)}")

    if last_mo > 0:
        mom = ((spent - last_mo) / last_mo) * 100
        if mom > 10:
            lines.append(f"📈 {mom:.0f}% more than last month's pace ({_inr(last_mo)})")
        elif mom < -10:
            lines.append(f"📉 {abs(mom):.0f}% less than last month — great improvement!")

    return "\n".join(lines)


def _reply_monthly_spending(ctx: dict) -> str:
    spent = ctx["spent"]
    budget = ctx["budget"]
    categories = ctx["categories"]
    today = ctx["today"]

    if spent == 0:
        return (
            f"No expenses logged yet for {today.strftime('%B')}! "
            "Start tracking your spending to get insights. 💡"
        )

    lines = [
        f"📋 Your {today.strftime('%B')} spending:\n",
        f"• Total spent: {_inr(spent)}",
    ]
    if budget > 0:
        lines.append(f"• Budget: {_inr(budget)} ({ctx['budget_pct']:.0f}% used)")
        lines.append(f"• Remaining: {_inr(ctx['remaining'])}")

    if categories:
        lines.append("\n📂 By category:")
        for cat, amt in sorted(categories.items(), key=lambda x: -x[1]):
            pct_cat = (amt / spent * 100) if spent > 0 else 0
            lines.append(f"  • {cat}: {_inr(amt)} ({pct_cat:.0f}%)")

    return "\n".join(lines)


def _reply_top_category(ctx: dict) -> str:
    categories = ctx["categories"]
    spent = ctx["spent"]
    top = ctx["top_category"]

    if not categories or spent == 0:
        return "No expenses logged yet this month. Start tracking to see where your money goes! 💡"

    lines = ["📊 Your top spending categories this month:\n"]
    rank = 1
    for cat, amt in sorted(categories.items(), key=lambda x: -x[1]):
        pct = (amt / spent * 100) if spent > 0 else 0
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        lines.append(f"{rank}. {cat}: {_inr(amt)} ({pct:.0f}%) {bar}")
        rank += 1

    if top:
        cat_name, cat_amt = top
        pct_top = (cat_amt / spent * 100) if spent > 0 else 0
        if pct_top > 40:
            lines.append(f"\n⚠️ {cat_name} is {pct_top:.0f}% of your total — consider cutting here first.")
        else:
            lines.append(f"\n💡 Your spending is relatively balanced across categories.")

    return "\n".join(lines)


def _reply_save_tips(ctx: dict) -> str:
    budget     = ctx["budget"]
    spent      = ctx["spent"]
    remaining  = ctx["remaining"]
    categories = ctx["categories"]
    never_worn = ctx["never_worn"]
    top        = ctx["top_category"]
    last_mo    = ctx["last_month_spent"]
    pct        = ctx["budget_pct"]

    tips = ["💡 Personalised saving tips:\n"]

    # Tip 1: Top category
    if top:
        cat_name, cat_amt = top
        save_potential = int(cat_amt * 0.25)
        tips.append(f"1. 🔪 Cut {cat_name} by 25% → save ~{_inr(save_potential)}/month")

    # Tip 2: Food delivery
    food = categories.get("Food", 0)
    if food > 1500:
        tips.append(f"2. 🍱 Cook at home 3x/week → save {_inr(int(food * 0.3))}/month on food")

    # Tip 3: Shopping + wardrobe
    shopping = categories.get("Shopping", 0)
    if shopping > 1000 or never_worn >= 2:
        tips.append(
            f"3. 👗 {'You have ' + str(never_worn) + ' unworn clothes — ' if never_worn >= 2 else ''}"
            f"Pause shopping this week{' → save ' + _inr(shopping) if shopping > 0 else ''}"
        )

    # Tip 4: Entertainment / subscriptions
    ent = categories.get("Entertainment", 0)
    if ent > 500:
        tips.append(f"4. 📺 Audit subscriptions → could free up {_inr(ent)}/month")

    # Tip 5: Budget pace
    if pct > 75:
        tips.append(f"5. 🛑 No-spend day challenge — try 2 days this week without spending anything")

    # Tip 6: Month-end savings
    if remaining > 500:
        save_now = int(remaining * 0.5)
        tips.append(f"6. 💰 Move {_inr(save_now)} to savings now before you spend it!")

    # Tip 7: Compare to last month
    if last_mo > 0 and spent > last_mo:
        diff = spent - last_mo
        tips.append(f"7. 📈 You're spending {_inr(diff)} more than last month — find what changed")

    if len(tips) == 1:
        tips.append("1. ✅ Keep logging every expense — awareness is the first step to saving!")
        tips.append("2. 💳 Set a category budget cap for your biggest spend category")
        tips.append("3. 🎯 Create a savings goal to stay motivated")

    return "\n".join(tips)


def _reply_savings_goals(ctx: dict) -> str:
    goals = ctx["goals"]
    remaining = ctx["remaining"]
    budget = ctx["budget"]

    if not goals:
        return (
            "You haven't set any savings goals yet! 🎯\n\n"
            "Go to your dashboard → 'Goal-Based Saving' to create one.\n"
            "Whether it's a trip, laptop, or emergency fund — a clear goal makes saving 3x easier!"
            + (f"\n\nWith {_inr(remaining)} left this month, you could start right now!" if remaining > 500 else "")
        )

    lines = ["🎯 Your savings goals:\n"]
    for g in goals:
        target  = _f(g.get("target_amount"))
        saved   = _f(g.get("saved_amount"))
        months  = max(int(g.get("months") or 1), 1)
        need    = max(0, target - saved)
        monthly = need / months if months > 0 else need
        daily   = monthly / 30
        pct     = (saved / target * 100) if target > 0 else 0

        lines.append(f"• {g['name']}")
        lines.append(f"  Target: {_inr(target)} | Saved: {_inr(saved)} ({pct:.0f}%)")
        lines.append(f"  Need: {_inr(monthly)}/month ({_inr(daily)}/day) for {months} month{'s' if months > 1 else ''}")
        on_track = remaining >= monthly
        lines.append(f"  {'✅ On track!' if on_track else '⚠️ Tight — you need to set aside more'}")

    return "\n".join(lines)


def _reply_spending_advice(ctx: dict) -> str:
    budget    = ctx["budget"]
    spent     = ctx["spent"]
    remaining = ctx["remaining"]
    pct       = ctx["budget_pct"]
    top       = ctx["top_category"]
    days_left = ctx["days_left"]
    name      = ctx["name"]

    if budget == 0:
        return (
            f"Hey {name}! Here's where to start:\n\n"
            "1. Set a monthly budget on your dashboard\n"
            "2. Log every expense — even small ones\n"
            "3. Check your AI Insights page weekly\n"
            "4. Create a savings goal to stay motivated\n\n"
            "Once you have data, I can give personalised advice! 🚀"
        )

    advice = [f"💬 Personalised advice for {name}:\n"]

    if pct >= 90:
        advice.append("🚨 URGENT: You've nearly exhausted your budget!")
        advice.append("→ Switch to essentials only (food, transport, bills)")
        advice.append("→ No discretionary spending until next month")
    elif pct >= 70:
        advice.append("⚠️ Budget is getting tight — time to be careful")
        if top:
            advice.append(f"→ {top[0]} is your biggest spend — cut it by 20%")
        advice.append(f"→ Aim for max {_inr(ctx['daily_remaining'])} per day for the next {days_left} days")
    else:
        advice.append(f"✅ You're managing well ({pct:.0f}% used so far)")
        advice.append(f"→ Stick to {_inr(ctx['daily_remaining'])}/day to finish strong")
        if remaining > 1000:
            advice.append(f"→ Put aside {_inr(int(remaining * 0.3))} into savings before month end")

    if top and top[1] > 0:
        advice.append(f"\n💡 Your biggest expense category is {top[0]} ({_inr(top[1])})")
        advice.append("   Focus your cuts here for maximum impact.")

    return "\n".join(advice)


def _reply_weekly_summary(ctx: dict) -> str:
    week_spent = ctx["week_spent"]
    budget     = ctx["budget"]
    daily_bud  = ctx["daily_budget"]
    name       = ctx["name"]

    if week_spent == 0:
        return "No expenses logged in the past 7 days. Either you're saving brilliantly, or you forgot to log! 😄"

    daily_avg = week_spent / 7
    weekly_budget = budget / 4.33 if budget > 0 else 0
    on_track = week_spent <= weekly_budget if weekly_budget > 0 else True

    return (
        f"📅 Past 7 days summary:\n\n"
        f"• Total spent: {_inr(week_spent)}\n"
        f"• Daily average: {_inr(daily_avg)}\n"
        + (f"• Weekly budget target: {_inr(weekly_budget)}\n" if weekly_budget > 0 else "")
        + (f"• Daily budget: {_inr(daily_bud)}\n" if daily_bud > 0 else "")
        + "\n"
        + (f"✅ On track — you're spending within your weekly pace!" if on_track
           else f"⚠️ You're {_inr(week_spent - weekly_budget)} over your weekly pace. Slow down!")
    )


def _reply_mood_spending(ctx: dict) -> str:
    mood = ctx["mood_spending"]

    if not mood:
        return (
            "No mood-tagged expenses yet! 😊\n\n"
            "When logging an expense, select your mood (Happy / Neutral / Stressed / Sad / Excited). "
            "Over time, I'll show you when you tend to overspend emotionally — "
            "super useful for avoiding impulse buys!"
        )

    total_mood = sum(mood.values())
    lines = ["😊 Your mood-based spending this month:\n"]
    emoji_map = {"happy": "😊", "stressed": "😤", "sad": "😔", "neutral": "😑", "excited": "🤩"}

    for m, amt in sorted(mood.items(), key=lambda x: -x[1]):
        pct = (amt / total_mood * 100) if total_mood > 0 else 0
        em = emoji_map.get(m, "💭")
        lines.append(f"• {em} {m.capitalize()}: {_inr(amt)} ({pct:.0f}%)")

    # Insight
    worst = max(mood.items(), key=lambda x: x[1])
    if worst[0] in ("stressed", "sad"):
        lines.append(
            f"\n⚠️ You spend the most when {worst[0]}! "
            "Try a 10-minute pause before buying when you feel this way."
        )
    else:
        lines.append("\n💡 Keep tagging moods — patterns become clearer over time!")

    return "\n".join(lines)


def _reply_wardrobe_advice(ctx: dict) -> str:
    never_worn = ctx["never_worn"]
    total      = ctx["wardrobe_total"]
    categories = ctx["categories"]
    shopping   = categories.get("Shopping", 0)

    if total == 0:
        return (
            "Your wardrobe is empty! Start tracking your clothes to get utilization insights. 👗\n"
            "Go to Wardrobe → Add Item."
        )

    lines = ["👗 Wardrobe advice:\n"]

    if never_worn > 0:
        utilization = ((total - never_worn) / total * 100) if total > 0 else 0
        lines.append(f"• {never_worn} of {total} items ({100-utilization:.0f}%) have never been worn")
        lines.append(f"• Try wearing something new this week before buying more!")
    else:
        lines.append(f"• Great job — all {total} items have been worn! ✅")

    if shopping > 1000 and never_worn >= 2:
        lines.append(
            f"\n⚠️ You spent {_inr(shopping)} on shopping this month "
            f"but have {never_worn} unworn items. Pause clothing purchases!"
        )

    lines.append("\n💡 Tips:")
    lines.append("• Log +1 wear every time you wear something")
    lines.append("• Items worn < 3 times are 'underutilized' — style them differently")
    lines.append("• Low cost-per-wear = great value investment")

    return "\n".join(lines)


def _reply_greeting(ctx: dict) -> str:
    name = ctx["name"]
    budget = ctx["budget"]
    spent  = ctx["spent"]
    pct    = ctx["budget_pct"]
    remaining = ctx["remaining"]
    today  = ctx["today"]

    hour = today.hour
    time_greet = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"

    if budget == 0:
        return (
            f"Good {time_greet}, {name}! 👋 I'm Fenora AI, your personal finance assistant.\n\n"
            "It looks like you haven't set a budget yet. Head to your dashboard to get started!\n\n"
            "Once set up, I can answer questions like:\n"
            "• 'Can I afford ₹2000?'\n"
            "• 'How much do I have left?'\n"
            "• 'Where am I spending the most?'"
        )

    status = "🚨 Budget critical!" if pct >= 90 else "⚠️ Getting tight" if pct >= 70 else "✅ Looking good"

    return (
        f"Good {time_greet}, {name}! 👋\n\n"
        f"Quick update: {status}\n"
        f"• Spent: {_inr(spent)} / {_inr(budget)} ({pct:.0f}%)\n"
        f"• Remaining: {_inr(remaining)}\n\n"
        "What would you like to know?\n"
        "• 'Can I afford ₹X?'\n"
        "• 'Where am I spending most?'\n"
        "• 'How to save more?'"
    )


def _reply_general_status(ctx: dict) -> str:
    """Fallback: give a helpful snapshot with suggestions."""
    budget    = ctx["budget"]
    spent     = ctx["spent"]
    remaining = ctx["remaining"]
    pct       = ctx["budget_pct"]
    top       = ctx["top_category"]

    if budget == 0 and spent == 0:
        return (
            "Hey! I'm Fenora AI 🤖 — your personal finance assistant.\n\n"
            "I can help you with:\n"
            "• 'Can I afford ₹2000?' — real calculation\n"
            "• 'How much do I have left?' — live budget check\n"
            "• 'Where am I spending the most?' — category breakdown\n"
            "• 'How to save more?' — personalized tips\n"
            "• 'Am I overspending?' — pace analysis\n\n"
            "Start by logging some expenses and setting your budget! 💡"
        )

    status = "🚨 Critical" if pct >= 90 else "⚠️ Tight" if pct >= 70 else "✅ Healthy"

    lines = [
        f"📊 Your financial snapshot:\n",
        f"• Budget: {_inr(budget)} | Spent: {_inr(spent)} ({pct:.0f}%) | Left: {_inr(remaining)}",
        f"• Status: {status}",
    ]
    if top:
        lines.append(f"• Biggest category: {top[0]} ({_inr(top[1])})")

    lines.append(
        "\nAsk me anything:\n"
        "• 'Can I afford ₹X?' • 'How to save?' • 'Where am I spending most?'"
    )

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
# MAIN PUBLIC FUNCTION
# ─────────────────────────────────────────────────────────────────────

def handle_chat_message(user_id: int, message: str, get_db_fn) -> dict:
    """
    Main entry point. Call this from the Flask route.

    Returns:
        {
            "reply": "...",      # The response text
            "intent": "...",     # What intent was detected
            "data": {...}        # Optional data context
        }
    """
    if not message or not message.strip():
        return {
            "reply": (
                "Hi! Ask me anything about your finances:\n"
                "• 'Can I afford ₹2000?'\n"
                "• 'How much do I have left?'\n"
                "• 'Where am I spending the most?'\n"
                "• 'How to save more?'"
            ),
            "intent": "empty",
            "data": {},
        }

    # Detect intent
    intent = _detect_intent(message)

    # Fetch live user data from DB
    try:
        ctx = _fetch_user_context(user_id, get_db_fn)
    except Exception as e:
        logger.error(f"[chatbot_engine] Failed to fetch context: {e}")
        return {
            "reply": "Couldn't connect to your data right now. Make sure you're logged in and have some expenses logged.",
            "intent": "error",
            "data": {},
        }

    # Route to correct handler
    try:
        if intent == "afford_check":
            reply = _reply_afford_check(ctx, message)
        elif intent == "daily_budget":
            reply = _reply_daily_budget(ctx)
        elif intent == "remaining_budget":
            reply = _reply_remaining_budget(ctx)
        elif intent == "budget_status":
            reply = _reply_budget_status(ctx)
        elif intent == "overspending_check":
            reply = _reply_overspending(ctx)
        elif intent == "monthly_spending":
            reply = _reply_monthly_spending(ctx)
        elif intent == "top_category":
            reply = _reply_top_category(ctx)
        elif intent == "save_tips":
            reply = _reply_save_tips(ctx)
        elif intent == "savings_goals":
            reply = _reply_savings_goals(ctx)
        elif intent == "spending_advice":
            reply = _reply_spending_advice(ctx)
        elif intent == "weekly_summary":
            reply = _reply_weekly_summary(ctx)
        elif intent == "mood_spending":
            reply = _reply_mood_spending(ctx)
        elif intent == "wardrobe_advice":
            reply = _reply_wardrobe_advice(ctx)
        elif intent == "greeting":
            reply = _reply_greeting(ctx)
        else:
            reply = _reply_general_status(ctx)

    except Exception as e:
        logger.error(f"[chatbot_engine] Handler error for intent={intent}: {e}")
        reply = (
            "Something went wrong generating your response. "
            "Make sure you have a budget set and some expenses logged!"
        )

    return {
        "reply": reply,
        "intent": intent,
        "data": {
            "budget":    ctx.get("budget", 0),
            "spent":     ctx.get("spent", 0),
            "remaining": ctx.get("remaining", 0),
            "budget_pct": round(ctx.get("budget_pct", 0), 1),
        },
    }
