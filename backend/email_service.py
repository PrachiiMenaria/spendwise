"""
email_service.py — fenora Smart Email Reminder System
=======================================================
Drop this file into: wardrobe-analysis-project/backend/

Setup:
  pip install apscheduler

Environment variables required:
  EMAIL_SENDER=your_gmail@gmail.com
  EMAIL_PASSWORD=your_app_password   ← Gmail App Password (not your real password)
  FRONTEND_URL=http://localhost:5173  (optional, used in email links)

Usage in app.py:
  from email_service import init_email_scheduler, send_test_email_for_user

  # After app is created:
  scheduler = init_email_scheduler(app, get_db)
"""

import os
import smtplib
import logging
import calendar
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────

def _f(val, default=0.0):
    if val is None:
        return float(default)
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


# ─────────────────────────────────────────────────────────────────────
# 1. INSIGHT GENERATION
# ─────────────────────────────────────────────────────────────────────

def generate_email_insights(user_id: int, get_db_fn) -> dict:
    """
    Pulls user data from DB and returns structured insights dict.
    
    Returns:
        {
            "user": {...},
            "summary": {...},
            "expense_insights": [...],
            "wardrobe_insights": [...],
            "recommendations": [...],
        }
    """
    conn = get_db_fn()
    try:
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        today = datetime.now()

        # ── User info & budget ─────────────────────────────────────
        cur.execute("SELECT id, name, email, monthly_budget FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            return None
        budget = _f(user.get("monthly_budget"))

        # ── This month's spending ──────────────────────────────────
        cur.execute(
            "SELECT category, COALESCE(SUM(amount), 0) AS total "
            "FROM expenses WHERE user_id = %s "
            "AND EXTRACT(YEAR FROM created_at) = %s AND EXTRACT(MONTH FROM created_at) = %s "
            "GROUP BY category ORDER BY total DESC",
            (user_id, today.year, today.month),
        )
        this_month_cats = {r["category"]: _f(r["total"]) for r in cur.fetchall()}
        this_month_total = sum(this_month_cats.values())

        # ── Last month's spending ──────────────────────────────────
        last_m = today.replace(day=1) - timedelta(days=1)
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses "
            "WHERE user_id = %s AND EXTRACT(YEAR FROM created_at) = %s AND EXTRACT(MONTH FROM created_at) = %s",
            (user_id, last_m.year, last_m.month),
        )
        row = cur.fetchone()
        last_month_total = _f(row["total"] if row else 0)

        # ── Wardrobe stats ─────────────────────────────────────────
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

    # ── Build expense insights ─────────────────────────────────────
    expense_insights = []

    if budget > 0:
        if budget_pct >= 100:
            expense_insights.append({
                "icon": "🚨", "type": "danger",
                "text": f"You overspent this month! Spent ₹{this_month_total:,.0f} vs budget of ₹{budget:,.0f} — that's ₹{this_month_total - budget:,.0f} over."
            })
        elif budget_pct >= 80:
            expense_insights.append({
                "icon": "⚠️", "type": "warning",
                "text": f"Budget alert! You've used {budget_pct:.0f}% of your ₹{budget:,.0f} budget. Only ₹{remaining:,.0f} left this month."
            })
        else:
            expense_insights.append({
                "icon": "✅", "type": "success",
                "text": f"Budget on track! You've used {budget_pct:.0f}% (₹{this_month_total:,.0f}) and have ₹{remaining:,.0f} still available. Great discipline! 🙌"
            })

    if this_month_cats:
        top_cat, top_amt = max(this_month_cats.items(), key=lambda x: x[1])
        pct_of_total = (top_amt / this_month_total * 100) if this_month_total > 0 else 0
        expense_insights.append({
            "icon": "📊", "type": "info",
            "text": f"Your biggest spend this month was {top_cat} at ₹{top_amt:,.0f} ({pct_of_total:.0f}% of total)."
        })

    if last_month_total > 0:
        change = ((this_month_total - last_month_total) / last_month_total * 100)
        if change > 20:
            expense_insights.append({
                "icon": "📈", "type": "warning",
                "text": f"Spending jumped {change:.0f}% vs last month. You spent ₹{this_month_total - last_month_total:,.0f} more than last month — what happened? 👀"
            })
        elif change < -10:
            expense_insights.append({
                "icon": "📉", "type": "success",
                "text": f"Lowkey slaying with budgeting! 🎉 Spending dropped {abs(change):.0f}% vs last month. That's ₹{last_month_total - this_month_total:,.0f} saved!"
            })

    # ── Build wardrobe insights ────────────────────────────────────
    wardrobe_insights = []

    if never_worn:
        wardrobe_insights.append({
            "icon": "😴", "type": "warning",
            "text": f"{len(never_worn)} wardrobe item(s) have never been worn — worth ₹{never_worn_value:,.0f} just sitting there. Wear them or let them go!"
        })

    worn_items = [i for i in wardrobe if (i.get("wear_count") or 0) > 0 and _f(i.get("purchase_price")) > 0]
    if worn_items:
        best = min(worn_items, key=lambda i: _f(i.get("purchase_price")) / max(i.get("wear_count") or 1, 1))
        cpw = _f(best.get("purchase_price")) / max(best.get("wear_count") or 1, 1)
        wardrobe_insights.append({
            "icon": "⭐", "type": "success",
            "text": f"Your best value piece is '{best['item_name']}' at only ₹{cpw:.0f}/wear. That's the energy we want! 💪"
        })

    if total_wardrobe_value > 0 and len(never_worn) > 0:
        waste_pct = (never_worn_value / total_wardrobe_value * 100)
        wardrobe_insights.append({
            "icon": "💸", "type": "info",
            "text": f"{waste_pct:.0f}% of your wardrobe value (₹{never_worn_value:,.0f}) is in unworn clothes. Make them work!"
        })

    # ── Build recommendations ──────────────────────────────────────
    recommendations = []

    food_spend = this_month_cats.get("Food", 0)
    if food_spend > 1500:
        recommendations.append({
            "icon": "🍕", "priority": "high",
            "title": "Cut food delivery costs",
            "text": f"₹{food_spend:,.0f} on food this month. Pack lunch 3x/week → save ~₹{int(food_spend * 0.25):,}/month."
        })

    shopping_spend = this_month_cats.get("Shopping", 0)
    if shopping_spend > 1000 and len(never_worn) >= 2:
        recommendations.append({
            "icon": "🛍️", "priority": "high",
            "title": "Pause new clothing purchases",
            "text": f"You spent ₹{shopping_spend:,.0f} on shopping but have {len(never_worn)} unworn items. Wear those first!"
        })

    if budget_pct > 85:
        recommendations.append({
            "icon": "🛑", "priority": "high",
            "title": "No-spend week recommended",
            "text": f"You've used {budget_pct:.0f}% of your budget. Try a 7-day no-spend challenge to close the month strong."
        })

    entertainment_spend = this_month_cats.get("Entertainment", 0)
    if entertainment_spend > 800:
        recommendations.append({
            "icon": "🎬", "priority": "medium",
            "title": "Audit your subscriptions",
            "text": f"₹{entertainment_spend:,.0f} on entertainment. Are you using all your OTT subscriptions? Cancel the ones you don't."
        })

    if not recommendations:
        recommendations.append({
            "icon": "💰", "priority": "success",
            "title": "Save the surplus",
            "text": f"You have ₹{remaining:,.0f} left this month. Move ₹{int(remaining * 0.5):,} to a savings goal before month end!"
        })

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


# ─────────────────────────────────────────────────────────────────────
# 2. EMAIL HTML BUILDER
# ─────────────────────────────────────────────────────────────────────

def build_email_html(insights: dict, is_weekly: bool = False) -> dict:
    """
    Converts insights dict → {"subject": ..., "html": ..., "text": ...}
    """
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

    # Status bar color
    if budget_pct >= 100:
        status_color = "#e74c3c"
        status_bg = "#fdf0f0"
        status_emoji = "🚨"
        status_text = f"Overspent by ₹{total - budget:,.0f}"
    elif budget_pct >= 80:
        status_color = "#f39c12"
        status_bg = "#fef9f0"
        status_emoji = "⚠️"
        status_text = f"{budget_pct:.0f}% of budget used"
    else:
        status_color = "#27ae60"
        status_bg = "#f0faf5"
        status_emoji = "✅"
        status_text = f"On track — {budget_pct:.0f}% used"

    # Category rows
    cat_rows = ""
    for cat, amt in sorted(summary["category_breakdown"].items(), key=lambda x: -x[1])[:5]:
        bar_pct = (amt / total * 100) if total > 0 else 0
        cat_rows += f"""
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid #f0eef8;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
              <span style="font-size:13px;color:#444;font-weight:500;">{cat}</span>
              <span style="font-size:13px;font-weight:700;color:#7c6fa0;">₹{amt:,.0f}</span>
            </div>
            <div style="background:#f0eef8;border-radius:4px;height:5px;overflow:hidden;">
              <div style="background:linear-gradient(90deg,#7c6fa0,#a89cc8);height:5px;width:{min(bar_pct, 100):.0f}%;border-radius:4px;"></div>
            </div>
          </td>
        </tr>"""

    # Insight rows
    def render_insights(items):
        if not items:
            return "<p style='color:#aaa;font-size:13px;margin:0;padding:12px 0;'>No insights yet — keep logging data!</p>"
        html = ""
        for ins in items:
            type_colors = {
                "danger": ("#fdf0f0", "#e74c3c"),
                "warning": ("#fef9f0", "#f39c12"),
                "success": ("#f0faf5", "#27ae60"),
                "info": ("#f3f0fa", "#7c6fa0"),
            }
            bg, border = type_colors.get(ins.get("type", "info"), ("#f3f0fa", "#7c6fa0"))
            html += f"""
            <div style="background:{bg};border-left:3px solid {border};border-radius:8px;padding:12px 14px;margin-bottom:10px;">
              <p style="margin:0;font-size:13px;line-height:1.6;color:#333;">{ins.get('icon','')} {ins.get('text','')}</p>
            </div>"""
        return html

    # Recommendation rows
    rec_html = ""
    for rec in recommendations[:3]:
        priority_colors = {
            "high": "#e74c3c",
            "medium": "#f39c12",
            "low": "#3498db",
            "success": "#27ae60",
        }
        color = priority_colors.get(rec.get("priority", "medium"), "#7c6fa0")
        rec_html += f"""
        <div style="background:#fff;border:1px solid #ede9f8;border-radius:10px;padding:14px;margin-bottom:10px;display:flex;gap:12px;align-items:flex-start;">
          <span style="font-size:22px;line-height:1;">{rec.get('icon','💡')}</span>
          <div>
            <p style="margin:0 0 4px;font-size:13px;font-weight:700;color:#1a1a2e;">{rec.get('title','')}</p>
            <p style="margin:0;font-size:12px;color:#666;line-height:1.5;">{rec.get('text','')}</p>
          </div>
          <span style="margin-left:auto;font-size:9px;font-weight:700;letter-spacing:0.5px;color:{color};text-transform:uppercase;white-space:nowrap;padding-top:2px;">{rec.get('priority','').upper()}</span>
        </div>"""

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    wardrobe_note = ""
    if summary.get("never_worn_count", 0) > 0:
        wardrobe_note = f"""
        <div style="background:#fff8ec;border:1px solid #fde68a;border-radius:10px;padding:14px;margin-bottom:16px;">
          <p style="margin:0;font-size:13px;color:#92400e;">👗 <strong>{summary['never_worn_count']} item(s)</strong> in your wardrobe worth <strong>₹{summary['never_worn_value']:,.0f}</strong> have never been worn. Wear them before buying more!</p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>fenora {email_type}</title></head>
<body style="margin:0;padding:24px 16px;background:#f5f3fc;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
  <div style="max-width:560px;margin:0 auto;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#6b5fa0 0%,#a89cc8 100%);border-radius:16px 16px 0 0;padding:32px 28px;text-align:center;">
      <div style="font-size:13px;color:rgba(255,255,255,0.7);letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">fenora · smart finance</div>
      <h1 style="color:#fff;margin:0;font-size:22px;font-weight:800;letter-spacing:-0.5px;">{email_type} 📊</h1>
      <p style="color:rgba(255,255,255,0.75);margin:6px 0 0;font-size:14px;">Hey {first_name}! Here's your {month_name} summary.</p>
    </div>

    <!-- Body -->
    <div style="background:#fff;padding:28px;border-radius:0 0 16px 16px;border:1px solid #ede9f8;border-top:none;">

      <!-- Budget Status Card -->
      <div style="background:{status_bg};border-radius:12px;padding:18px 20px;margin-bottom:22px;border-left:4px solid {status_color};">
        <div style="font-size:12px;color:#888;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">{status_emoji} Budget Status</div>
        <div style="font-size:28px;font-weight:800;color:#1a1a2e;letter-spacing:-1px;">₹{total:,.0f}</div>
        <div style="font-size:13px;color:#666;margin-top:4px;">{status_text} · Budget: ₹{budget:,.0f} · Remaining: ₹{remaining:,.0f}</div>
        <!-- Progress bar -->
        <div style="background:#e8e4f5;border-radius:6px;height:8px;margin-top:12px;overflow:hidden;">
          <div style="background:linear-gradient(90deg,{status_color},{status_color}cc);height:8px;width:{min(budget_pct, 100):.0f}%;border-radius:6px;"></div>
        </div>
      </div>

      <!-- Category Breakdown -->
      <h3 style="font-size:14px;font-weight:700;color:#7c6fa0;margin:0 0 10px;text-transform:uppercase;letter-spacing:0.5px;">💳 Where Your Money Went</h3>
      <table style="width:100%;border-collapse:collapse;margin-bottom:22px;">
        <tbody>{cat_rows if cat_rows else "<tr><td style='padding:12px 0;color:#aaa;font-size:13px;'>No expense data yet.</td></tr>"}</tbody>
      </table>

      <!-- Expense Insights -->
      <h3 style="font-size:14px;font-weight:700;color:#7c6fa0;margin:0 0 10px;text-transform:uppercase;letter-spacing:0.5px;">🧠 Spending Insights</h3>
      <div style="margin-bottom:22px;">{render_insights(expense_insights)}</div>

      <!-- Wardrobe Insights -->
      <h3 style="font-size:14px;font-weight:700;color:#7c6fa0;margin:0 0 10px;text-transform:uppercase;letter-spacing:0.5px;">👗 Wardrobe Insights</h3>
      <div style="margin-bottom:22px;">{render_insights(wardrobe_insights) if wardrobe_insights else "<p style='color:#aaa;font-size:13px;margin:0;padding:12px 0;'>Add wardrobe items to unlock insights!</p>"}</div>

      <!-- Wardrobe Nudge -->
      {wardrobe_note}

      <!-- Recommendations -->
      <h3 style="font-size:14px;font-weight:700;color:#7c6fa0;margin:0 0 12px;text-transform:uppercase;letter-spacing:0.5px;">🎯 Action Plan</h3>
      <div style="margin-bottom:24px;">{rec_html if rec_html else "<p style='color:#aaa;font-size:13px;'>Nothing critical to flag right now. Keep it up!</p>"}</div>

      <!-- CTA -->
      <div style="text-align:center;padding-top:8px;">
        <a href="{frontend_url}" style="display:inline-block;background:linear-gradient(135deg,#6b5fa0,#a89cc8);color:#fff;padding:13px 32px;border-radius:50px;text-decoration:none;font-size:14px;font-weight:700;letter-spacing:0.3px;box-shadow:0 4px 20px rgba(107,95,160,0.3);">Open Dashboard →</a>
      </div>
    </div>

    <!-- Footer -->
    <div style="text-align:center;padding:20px;color:#aaa;font-size:11px;">
      <p style="margin:0 0 4px;">fenora · Smart Budget & Wardrobe Intelligence</p>
      <p style="margin:0;">You're receiving this because you enabled email reminders.</p>
    </div>

  </div>
</body></html>"""

    # Plain text fallback
    text = f"""fenora {email_type} — {month_name}

Hi {first_name}!

BUDGET SUMMARY
--------------
Total Spent:   ₹{total:,.0f}
Budget:        ₹{budget:,.0f}
Remaining:     ₹{remaining:,.0f}
Budget Used:   {budget_pct:.0f}%

TOP CATEGORIES
--------------
""" + "\n".join(f"  {cat}: ₹{amt:,.0f}" for cat, amt in list(summary["category_breakdown"].items())[:5]) + f"""

WARDROBE
--------
Unworn items: {summary.get('never_worn_count', 0)} (worth ₹{summary.get('never_worn_value', 0):,.0f})

RECOMMENDATIONS
---------------
""" + "\n".join(f"  {r['icon']} {r['title']}: {r['text']}" for r in recommendations[:3]) + f"""

View your full dashboard: {frontend_url}

— fenora AI
"""

    return {"subject": subject, "html": html, "text": text}


# ─────────────────────────────────────────────────────────────────────
# 3. EMAIL SENDING (SMTP)
# ─────────────────────────────────────────────────────────────────────

def send_email(to_address: str, subject: str, html_content: str, text_content: str = "") -> dict:
    """
    Sends email via Gmail SMTP (TLS).
    Returns {"success": bool, "error": str | None}
    
    Setup: Enable 2FA on Gmail, then create an App Password at:
    https://myaccount.google.com/apppasswords
    Set EMAIL_SENDER and EMAIL_PASSWORD environment variables.
    """
    smtp_user = os.getenv("EMAIL_SENDER", "")
    smtp_pass = os.getenv("EMAIL_PASSWORD", "")

    if not smtp_user or not smtp_pass:
        return {
            "success": False,
            "error": "Email not configured. Set EMAIL_SENDER and EMAIL_PASSWORD environment variables."
        }

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"fenora AI <{smtp_user}>"
        msg["To"] = to_address
        msg["Subject"] = subject

        if text_content:
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_address, msg.as_string())

        logger.info(f"[email_service] Email sent to {to_address}: {subject}")
        return {"success": True, "error": None}

    except smtplib.SMTPAuthenticationError:
        err = "SMTP authentication failed. Check EMAIL_SENDER and EMAIL_PASSWORD (use Gmail App Password)."
        logger.error(f"[email_service] {err}")
        return {"success": False, "error": err}
    except smtplib.SMTPException as e:
        err = f"SMTP error: {str(e)}"
        logger.error(f"[email_service] {err}")
        return {"success": False, "error": err}
    except Exception as e:
        err = f"Unexpected error sending email: {str(e)}"
        logger.error(f"[email_service] {err}")
        return {"success": False, "error": err}


# ─────────────────────────────────────────────────────────────────────
# 4. CORE SEND FUNCTION (used by scheduler + test route)
# ─────────────────────────────────────────────────────────────────────

def send_insight_email(user_id: int, get_db_fn, is_weekly: bool = False) -> dict:
    """
    Full pipeline: fetch data → generate insights → build email → send.
    Returns result dict with status + generated content.
    """
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


# ─────────────────────────────────────────────────────────────────────
# 5. SCHEDULER SETUP
# ─────────────────────────────────────────────────────────────────────

def init_email_scheduler(app, get_db_fn):
    """
    Sets up APScheduler with two jobs:
      - Monthly recap: 1st of every month at 8:00 AM
      - Weekly check-in: Every Sunday at 9:00 AM
    
    Usage in app.py:
        from email_service import init_email_scheduler
        scheduler = init_email_scheduler(app, get_db)
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning("[email_service] apscheduler not installed. Run: pip install apscheduler")
        return None

    def run_monthly_job():
        logger.info("[scheduler] Running monthly email job...")
        conn = get_db_fn()
        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT id FROM users WHERE email_reminders_enabled = TRUE OR email_reminders_enabled IS NULL"
                )
                user_ids = [r["id"] for r in cur.fetchall()]
        except Exception:
            # Fallback: send to all users if column doesn't exist yet
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
                status = "✓" if result["success"] else "✗"
                logger.info(f"[scheduler] Monthly email user {uid}: {status}")
            except Exception as e:
                logger.error(f"[scheduler] Failed for user {uid}: {e}")

    def run_weekly_job():
        logger.info("[scheduler] Running weekly email job...")
        conn = get_db_fn()
        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT id FROM users WHERE email_frequency = 'weekly'"
                )
                user_ids = [r["id"] for r in cur.fetchall()]
        except Exception:
            logger.info("[scheduler] Weekly job skipped — email_frequency column may not exist yet.")
            return
        finally:
            conn.close()

        for uid in user_ids:
            try:
                result = send_insight_email(uid, get_db_fn, is_weekly=True)
                status = "✓" if result["success"] else "✗"
                logger.info(f"[scheduler] Weekly email user {uid}: {status}")
            except Exception as e:
                logger.error(f"[scheduler] Failed for user {uid}: {e}")

    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

    # Monthly: 1st of every month at 8:00 AM IST
    scheduler.add_job(
        run_monthly_job,
        trigger=CronTrigger(day=1, hour=8, minute=0),
        id="monthly_email",
        replace_existing=True,
    )

    # Weekly: Every Sunday at 9:00 AM IST
    scheduler.add_job(
        run_weekly_job,
        trigger=CronTrigger(day_of_week="sun", hour=9, minute=0),
        id="weekly_email",
        replace_existing=True,
    )

    try:
        scheduler.start()
        logger.info("[email_service] Scheduler started: monthly (1st @ 8 AM) + weekly (Sun @ 9 AM)")
    except Exception as e:
        logger.error(f"[email_service] Scheduler failed to start: {e}")
        return None

    return scheduler