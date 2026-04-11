"""
email_service.py - fenora Smart Email Reminder System
======================================================
Uses Resend SDK instead of SMTP (works on Render free tier).

Environment variables required:
  RESEND_API_KEY=re_xxxxxxxxxxxx   <- from resend.com
  FRONTEND_URL=https://spendwise-beryl-six.vercel.app
"""

import os
import logging
import calendar
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------

def _f(val, default=0.0):
    if val is None:
        return float(default)
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


# -----------------------------------------------------------------------
# 1. INSIGHT GENERATION
# -----------------------------------------------------------------------

def generate_email_insights(user_id: int, get_db_fn) -> dict:
    conn = get_db_fn()
    try:
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        today = datetime.now()

        cur.execute("SELECT id, name, email, monthly_budget FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            return None
        budget = _f(user.get("monthly_budget"))

        cur.execute(
            "SELECT category, COALESCE(SUM(amount), 0) AS total "
            "FROM expenses WHERE user_id = %s "
            "AND EXTRACT(YEAR FROM created_at) = %s AND EXTRACT(MONTH FROM created_at) = %s "
            "GROUP BY category ORDER BY total DESC",
            (user_id, today.year, today.month),
        )
        this_month_cats = {r["category"]: _f(r["total"]) for r in cur.fetchall()}
        this_month_total = sum(this_month_cats.values())

        last_m = today.replace(day=1) - timedelta(days=1)
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses "
            "WHERE user_id = %s AND EXTRACT(YEAR FROM created_at) = %s AND EXTRACT(MONTH FROM created_at) = %s",
            (user_id, last_m.year, last_m.month),
        )
        row = cur.fetchone()
        last_month_total = _f(row["total"] if row else 0)

        cur.execute(
            "SELECT item_name, category, purchase_price, wear_count FROM wardrobe_items WHERE user_id = %s",
            (user_id,),
        )
        wardrobe = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    never_worn = [i for i in wardrobe if (i.get("wear_count") or 0) == 0]
    never_worn_value = sum(_f(i.get("purchase_price")) for i in never_worn)
    total_wardrobe_value = sum(_f(i.get("purchase_price")) for i in wardrobe)
    budget_pct = round((this_month_total / budget * 100), 1) if budget > 0 else 0
    remaining = max(0.0, budget - this_month_total)

    expense_insights = []
    if budget > 0:
        if budget_pct >= 100:
            expense_insights.append({"icon": "🚨", "type": "danger",
                "text": f"You overspent this month! Spent ₹{this_month_total:,.0f} vs budget of ₹{budget:,.0f}."})
        elif budget_pct >= 80:
            expense_insights.append({"icon": "⚠️", "type": "warning",
                "text": f"Budget alert! You've used {budget_pct:.0f}% of your ₹{budget:,.0f} budget. Only ₹{remaining:,.0f} left."})
        else:
            expense_insights.append({"icon": "✅", "type": "success",
                "text": f"Budget on track! You've used {budget_pct:.0f}% (₹{this_month_total:,.0f}) and have ₹{remaining:,.0f} still available. Great discipline! 🙌"})

    if this_month_cats:
        top_cat, top_amt = max(this_month_cats.items(), key=lambda x: x[1])
        pct_of_total = (top_amt / this_month_total * 100) if this_month_total > 0 else 0
        expense_insights.append({"icon": "📊", "type": "info",
            "text": f"Your biggest spend this month was {top_cat} at ₹{top_amt:,.0f} ({pct_of_total:.0f}% of total)."})

    if last_month_total > 0:
        change = ((this_month_total - last_month_total) / last_month_total * 100)
        if change > 20:
            expense_insights.append({"icon": "📈", "type": "warning",
                "text": f"Spending jumped {change:.0f}% vs last month. ₹{this_month_total - last_month_total:,.0f} more than last month."})
        elif change < -10:
            expense_insights.append({"icon": "📉", "type": "success",
                "text": f"Spending dropped {abs(change):.0f}% vs last month. That's ₹{last_month_total - this_month_total:,.0f} saved!"})

    wardrobe_insights = []
    if never_worn:
        wardrobe_insights.append({"icon": "😴", "type": "warning",
            "text": f"{len(never_worn)} wardrobe item(s) have never been worn — worth ₹{never_worn_value:,.0f} just sitting there."})

    worn_items = [i for i in wardrobe if (i.get("wear_count") or 0) > 0 and _f(i.get("purchase_price")) > 0]
    if worn_items:
        best = min(worn_items, key=lambda i: _f(i.get("purchase_price")) / max(i.get("wear_count") or 1, 1))
        cpw = _f(best.get("purchase_price")) / max(best.get("wear_count") or 1, 1)
        wardrobe_insights.append({"icon": "⭐", "type": "success",
            "text": f"Your best value piece is '{best['item_name']}' at only ₹{cpw:.0f}/wear!"})

    if total_wardrobe_value > 0 and len(never_worn) > 0:
        waste_pct = (never_worn_value / total_wardrobe_value * 100)
        wardrobe_insights.append({"icon": "💸", "type": "info",
            "text": f"{waste_pct:.0f}% of your wardrobe value (₹{never_worn_value:,.0f}) is in unworn clothes."})

    recommendations = []
    food_spend = this_month_cats.get("Food", 0)
    if food_spend > 1500:
        recommendations.append({"icon": "🍕", "priority": "high", "title": "Cut food delivery costs",
            "text": f"₹{food_spend:,.0f} on food this month. Pack lunch 3x/week → save ~₹{int(food_spend * 0.25):,}/month."})

    shopping_spend = this_month_cats.get("Shopping", 0)
    if shopping_spend > 1000 and len(never_worn) >= 2:
        recommendations.append({"icon": "🛍️", "priority": "high", "title": "Pause new clothing purchases",
            "text": f"₹{shopping_spend:,.0f} on shopping but {len(never_worn)} unworn items. Wear those first!"})

    if budget_pct > 85:
        recommendations.append({"icon": "🛑", "priority": "high", "title": "No-spend week recommended",
            "text": f"You've used {budget_pct:.0f}% of your budget. Try a 7-day no-spend challenge."})

    if not recommendations:
        recommendations.append({"icon": "💰", "priority": "success", "title": "Save the surplus",
            "text": f"You have ₹{remaining:,.0f} left this month. Move ₹{int(remaining * 0.5):,} to a savings goal!"})

    return {
        "user": dict(user),
        "summary": {
            "this_month_total": this_month_total,
            "last_month_total": last_month_total,
            "budget": budget,
            "budget_pct": budget_pct,
            "remaining": remaining,
            "category_breakdown": this_month_cats,
            "never_worn_count": len(never_worn),
            "never_worn_value": never_worn_value,
        },
        "expense_insights": expense_insights,
        "wardrobe_insights": wardrobe_insights,
        "recommendations": recommendations,
    }


# -----------------------------------------------------------------------
# 2. EMAIL HTML BUILDER
# -----------------------------------------------------------------------

def build_email_html(insights: dict, is_weekly: bool = False) -> dict:
    user = insights["user"]
    summary = insights["summary"]
    expense_insights = insights["expense_insights"]
    wardrobe_insights = insights["wardrobe_insights"]
    recommendations = insights["recommendations"]

    month_name = datetime.now().strftime("%B %Y")
    first_name = user.get("name", "there").split()[0]
    email_type = "Weekly Check-in" if is_weekly else "Monthly Recap"
    subject = f"fenora {email_type}: {month_name} 📊"

    budget = summary["budget"]
    total = summary["this_month_total"]
    budget_pct = summary["budget_pct"]
    remaining = summary["remaining"]

    if budget_pct >= 100:
        status_color = "#e74c3c"; status_bg = "#fdf0f0"
        status_emoji = "🚨"; status_text = f"Overspent by ₹{total - budget:,.0f}"
    elif budget_pct >= 80:
        status_color = "#f39c12"; status_bg = "#fef9f0"
        status_emoji = "⚠️"; status_text = f"{budget_pct:.0f}% of budget used"
    else:
        status_color = "#27ae60"; status_bg = "#f0faf5"
        status_emoji = "✅"; status_text = f"On track — {budget_pct:.0f}% used"

    cat_rows = ""
    for cat, amt in sorted(summary["category_breakdown"].items(), key=lambda x: -x[1])[:5]:
        bar_pct = (amt / total * 100) if total > 0 else 0
        cat_rows += f"""
        <tr><td style="padding:10px 0;border-bottom:1px solid #f0eef8;">
          <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
            <span style="font-size:13px;color:#444;">{cat}</span>
            <span style="font-size:13px;font-weight:700;color:#7c6fa0;">₹{amt:,.0f}</span>
          </div>
          <div style="background:#f0eef8;border-radius:4px;height:5px;">
            <div style="background:#7c6fa0;height:5px;width:{min(bar_pct,100):.0f}%;border-radius:4px;"></div>
          </div>
        </td></tr>"""

    def render_insights(items):
        if not items:
            return "<p style='color:#aaa;font-size:13px;'>No insights yet.</p>"
        html = ""
        for ins in items:
            colors = {"danger":("#fdf0f0","#e74c3c"),"warning":("#fef9f0","#f39c12"),
                      "success":("#f0faf5","#27ae60"),"info":("#f3f0fa","#7c6fa0")}
            bg, border = colors.get(ins.get("type","info"), ("#f3f0fa","#7c6fa0"))
            html += f'<div style="background:{bg};border-left:3px solid {border};border-radius:8px;padding:12px 14px;margin-bottom:10px;"><p style="margin:0;font-size:13px;color:#333;">{ins.get("icon","")} {ins.get("text","")}</p></div>'
        return html

    rec_html = ""
    for rec in recommendations[:3]:
        priority_colors = {"high":"#e74c3c","medium":"#f39c12","low":"#3498db","success":"#27ae60"}
        color = priority_colors.get(rec.get("priority","medium"), "#7c6fa0")
        rec_html += f'<div style="background:#fff;border:1px solid #ede9f8;border-radius:10px;padding:14px;margin-bottom:10px;"><p style="margin:0 0 4px;font-size:13px;font-weight:700;color:#1a1a2e;">{rec.get("icon","💡")} {rec.get("title","")}</p><p style="margin:0;font-size:12px;color:#666;">{rec.get("text","")}</p></div>'

    frontend_url = os.getenv("FRONTEND_URL", "https://spendwise-beryl-six.vercel.app")

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:24px 16px;background:#f5f3fc;font-family:Arial,sans-serif;">
<div style="max-width:560px;margin:0 auto;">
  <div style="background:linear-gradient(135deg,#6b5fa0,#a89cc8);border-radius:16px 16px 0 0;padding:32px 28px;text-align:center;">
    <h1 style="color:#fff;margin:0;font-size:22px;">fenora {email_type} 📊</h1>
    <p style="color:rgba(255,255,255,0.75);margin:6px 0 0;font-size:14px;">Hey {first_name}! Here's your {month_name} summary.</p>
  </div>
  <div style="background:#fff;padding:28px;border-radius:0 0 16px 16px;border:1px solid #ede9f8;border-top:none;">
    <div style="background:{status_bg};border-radius:12px;padding:18px 20px;margin-bottom:22px;border-left:4px solid {status_color};">
      <div style="font-size:28px;font-weight:800;color:#1a1a2e;">₹{total:,.0f}</div>
      <div style="font-size:13px;color:#666;">{status_emoji} {status_text} · Budget: ₹{budget:,.0f} · Remaining: ₹{remaining:,.0f}</div>
      <div style="background:#e8e4f5;border-radius:6px;height:8px;margin-top:12px;">
        <div style="background:{status_color};height:8px;width:{min(budget_pct,100):.0f}%;border-radius:6px;"></div>
      </div>
    </div>
    <h3 style="font-size:14px;font-weight:700;color:#7c6fa0;margin:0 0 10px;">💳 Where Your Money Went</h3>
    <table style="width:100%;border-collapse:collapse;margin-bottom:22px;"><tbody>
      {cat_rows if cat_rows else "<tr><td style='color:#aaa;font-size:13px;padding:12px 0;'>No expense data yet.</td></tr>"}
    </tbody></table>
    <h3 style="font-size:14px;font-weight:700;color:#7c6fa0;margin:0 0 10px;">🧠 Spending Insights</h3>
    <div style="margin-bottom:22px;">{render_insights(expense_insights)}</div>
    <h3 style="font-size:14px;font-weight:700;color:#7c6fa0;margin:0 0 10px;">👗 Wardrobe Insights</h3>
    <div style="margin-bottom:22px;">{render_insights(wardrobe_insights) if wardrobe_insights else "<p style='color:#aaa;font-size:13px;'>Add wardrobe items to unlock insights!</p>"}</div>
    <h3 style="font-size:14px;font-weight:700;color:#7c6fa0;margin:0 0 12px;">🎯 Action Plan</h3>
    <div style="margin-bottom:24px;">{rec_html}</div>
    <div style="text-align:center;padding-top:8px;">
      <a href="{frontend_url}" style="display:inline-block;background:linear-gradient(135deg,#6b5fa0,#a89cc8);color:#fff;padding:13px 32px;border-radius:50px;text-decoration:none;font-size:14px;font-weight:700;">Open Dashboard →</a>
    </div>
  </div>
  <div style="text-align:center;padding:20px;color:#aaa;font-size:11px;">
    <p style="margin:0;">fenora · Smart Budget & Wardrobe Intelligence</p>
  </div>
</div></body></html>"""

    text = f"fenora {email_type} - {month_name}\n\nHi {first_name}!\n\nSpent: ₹{total:,.0f} / Budget: ₹{budget:,.0f}\nRemaining: ₹{remaining:,.0f}\n\nView dashboard: {frontend_url}"

    return {"subject": subject, "html": html, "text": text}


# -----------------------------------------------------------------------
# 3. EMAIL SENDING — RESEND (replaces SMTP)
# -----------------------------------------------------------------------

def send_email(to_address: str, subject: str, html_content: str, text_content: str = "") -> dict:
    """
    Sends email via Resend SDK.
    Requires RESEND_API_KEY environment variable.
    Get your free API key at resend.com
    """
    api_key = os.getenv("RESEND_API_KEY", "")

    if not api_key:
        return {
            "success": False,
            "error": "Email not configured. Set RESEND_API_KEY environment variable."
        }

    try:
        import resend
        resend.api_key = api_key

        result = resend.Emails.send({
            "from": "fenora <onboarding@resend.dev>",
            "to": [to_address],
            "subject": subject,
            "html": html_content,
            "text": text_content or "",
        })

        logger.info(f"[email_service] Email sent to {to_address} via Resend: {subject}")
        return {"success": True, "error": None, "id": str(result)}

    except Exception as e:
        err = f"Resend error: {str(e)}"
        logger.error(f"[email_service] {err}")
        return {"success": False, "error": err}


# -----------------------------------------------------------------------
# 4. CORE SEND FUNCTION
# -----------------------------------------------------------------------

def send_insight_email(user_id: int, get_db_fn, is_weekly: bool = False) -> dict:
    try:
        insights = generate_email_insights(user_id, get_db_fn)
    except Exception as e:
        return {"success": False, "error": f"Could not generate insights: {e}"}

    if not insights:
        return {"success": False, "error": "User not found."}

    try:
        email_content = build_email_html(insights, is_weekly=is_weekly)
    except Exception as e:
        return {"success": False, "error": f"Could not build email HTML: {e}"}

    user_email = insights["user"].get("email", "")
    if not user_email:
        return {"success": False, "error": "User has no email address."}

    result = send_email(
        to_address=user_email,
        subject=email_content["subject"],
        html_content=email_content["html"],
        text_content=email_content["text"],
    )

    return {
        **result,
        "to": user_email,
        "subject": email_content["subject"],
        "preview_html": email_content["html"],
        "insights_summary": {
            "this_month_total": insights["summary"]["this_month_total"],
            "budget_pct": insights["summary"]["budget_pct"],
            "expense_insights_count": len(insights["expense_insights"]),
            "wardrobe_insights_count": len(insights["wardrobe_insights"]),
            "recommendations_count": len(insights["recommendations"]),
        }
    }


# -----------------------------------------------------------------------
# 5. SCHEDULER SETUP
# -----------------------------------------------------------------------

def init_email_scheduler(app, get_db_fn):
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning("[email_service] apscheduler not installed.")
        return None

    def run_monthly_job():
        logger.info("[scheduler] Running monthly email job...")
        conn = get_db_fn()
        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id FROM users WHERE email_reminders_enabled = TRUE OR email_reminders_enabled IS NULL")
                user_ids = [r["id"] for r in cur.fetchall()]
        except Exception:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users")
                    user_ids = [r[0] for r in cur.fetchall()]
            except Exception as e:
                logger.error(f"[scheduler] Could not fetch users: {e}")
                return
        finally:
            conn.close()

        for uid in user_ids:
            try:
                result = send_insight_email(uid, get_db_fn, is_weekly=False)
                logger.info(f"[scheduler] Monthly email user {uid}: {'✓' if result['success'] else '✗'}")
            except Exception as e:
                logger.error(f"[scheduler] Failed for user {uid}: {e}")

    def run_weekly_job():
        logger.info("[scheduler] Running weekly email job...")
        conn = get_db_fn()
        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id FROM users WHERE email_frequency = 'weekly'")
                user_ids = [r["id"] for r in cur.fetchall()]
        except Exception:
            logger.info("[scheduler] Weekly job skipped.")
            return
        finally:
            conn.close()

        for uid in user_ids:
            try:
                result = send_insight_email(uid, get_db_fn, is_weekly=True)
                logger.info(f"[scheduler] Weekly email user {uid}: {'✓' if result['success'] else '✗'}")
            except Exception as e:
                logger.error(f"[scheduler] Failed for user {uid}: {e}")

    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
    scheduler.add_job(run_monthly_job, trigger=CronTrigger(day=1, hour=8, minute=0),
                      id="monthly_email", replace_existing=True)
    scheduler.add_job(run_weekly_job, trigger=CronTrigger(day_of_week="sun", hour=9, minute=0),
                      id="weekly_email", replace_existing=True)

    try:
        scheduler.start()
        logger.info("[email_service] Scheduler started: monthly (1st @ 8 AM) + weekly (Sun @ 9 AM)")
    except Exception as e:
        logger.error(f"[email_service] Scheduler failed to start: {e}")
        return None

    return scheduler