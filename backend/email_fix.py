"""
email_fix.py — fenora Production Email System
===============================================
Drop into: wardrobe-analysis-project/backend/email_fix.py

Paste the routes into app.py BEFORE `from email_routes import email_bp`

This replaces all previous email logic with a single, battle-tested implementation.

SETUP:
  1. Go to https://myaccount.google.com/apppasswords
  2. Generate an App Password (requires 2FA to be ON)
  3. In your .env:
       EMAIL_SENDER=your_gmail@gmail.com
       EMAIL_PASSWORD=abcd efgh ijkl mnop   (16 chars, spaces are fine)

The code strips spaces from the password automatically.
"""

import os
import smtplib
import logging
import calendar as _cal
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from decimal import Decimal
from flask import jsonify, request, session

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# SMTP CORE SENDER
# ─────────────────────────────────────────────────────────────────────

def _get_smtp_credentials():
    """
    Reads email credentials from environment.
    Tries multiple env variable names for maximum compatibility.
    Returns (user, password) or (None, None).
    """
    user = (
        os.getenv("EMAIL_SENDER") or
        os.getenv("EMAIL_USER") or
        os.getenv("MAIL_USERNAME") or
        os.getenv("SMTP_USER")
    )
    password = (
        os.getenv("EMAIL_PASSWORD") or
        os.getenv("EMAIL_PASS") or
        os.getenv("MAIL_PASSWORD") or
        os.getenv("SMTP_PASS")
    )

    # Strip spaces from App Password (Gmail allows "abcd efgh ijkl mnop")
    if password:
        password = password.replace(" ", "").strip()

    return user, password


def send_email_smtp(to_address: str, subject: str, html_body: str, plain_body: str = "") -> dict:
    """
    Sends an email via Gmail SMTP with STARTTLS (port 587).
    Returns {"success": bool, "error": str|None, "hint": str|None}

    Why port 587 + STARTTLS and not 465 + SSL?
    - Port 587 is the modern submission standard
    - STARTTLS upgrades the plain connection to TLS
    - More compatible with Gmail App Passwords
    - 465 (SSL_SSL) sometimes gets blocked by ISPs/VPNs
    """
    user, password = _get_smtp_credentials()

    if not user:
        hint = (
            "Set EMAIL_SENDER in your .env file. "
            "Example: EMAIL_SENDER=your@gmail.com"
        )
        logger.error("[email_fix] EMAIL_SENDER not set")
        return {"success": False, "error": "Email sender not configured.", "hint": hint}

    if not password:
        hint = (
            "Set EMAIL_PASSWORD in your .env file. "
            "Use a Gmail App Password (not your real password). "
            "Get one at: myaccount.google.com/apppasswords"
        )
        logger.error("[email_fix] EMAIL_PASSWORD not set")
        return {"success": False, "error": "Email password not configured.", "hint": hint}

    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = f"fenora AI <{user}>"
        msg["To"]      = to_address
        msg["Subject"] = subject

        # Attach plain text first (fallback), then HTML
        if plain_body:
            msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Connect with STARTTLS on port 587
        logger.info(f"[email_fix] Connecting to smtp.gmail.com:587 for {to_address}")

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.ehlo()                       # identify ourselves
            server.starttls()                   # upgrade to TLS
            server.ehlo()                       # re-identify after TLS
            server.login(user, password)        # authenticate
            server.sendmail(user, to_address, msg.as_string())

        logger.info(f"[email_fix] ✅ Email sent to {to_address}: {subject}")
        return {"success": True, "error": None, "hint": None}

    except smtplib.SMTPAuthenticationError as e:
        hint = (
            "Gmail rejected the password. "
            "Make sure you're using an App Password (16 chars), NOT your real Gmail password. "
            "Get one at: myaccount.google.com/apppasswords — requires 2FA to be ON."
        )
        logger.error(f"[email_fix] Auth failed: {e}")
        return {"success": False, "error": f"Gmail authentication failed: {str(e)}", "hint": hint}

    except smtplib.SMTPConnectError as e:
        hint = "Could not connect to Gmail. Check your internet connection and firewall settings."
        logger.error(f"[email_fix] Connect error: {e}")
        return {"success": False, "error": f"SMTP connection failed: {str(e)}", "hint": hint}

    except smtplib.SMTPRecipientsRefused as e:
        hint = f"The recipient address {to_address!r} was rejected. Check the email address."
        logger.error(f"[email_fix] Recipient refused: {e}")
        return {"success": False, "error": f"Recipient refused: {str(e)}", "hint": hint}

    except smtplib.SMTPException as e:
        hint = "An SMTP error occurred. Check your credentials and try again."
        logger.error(f"[email_fix] SMTP error: {e}")
        return {"success": False, "error": f"SMTP error: {str(e)}", "hint": hint}

    except TimeoutError:
        hint = "Connection timed out. Gmail SMTP may be blocked on your network or VPN."
        logger.error("[email_fix] Connection timed out")
        return {"success": False, "error": "Connection timed out.", "hint": hint}

    except Exception as e:
        hint = "Unexpected error. Check backend logs for details."
        logger.error(f"[email_fix] Unexpected error: {type(e).__name__}: {e}")
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}", "hint": hint}


# ─────────────────────────────────────────────────────────────────────
# HTML EMAIL BUILDER
# ─────────────────────────────────────────────────────────────────────

def _build_snapshot_email(user_data: dict) -> tuple:
    """
    Builds (subject, html_body, plain_body) for a financial snapshot email.
    user_data keys: name, email, budget, spent, remaining, budget_pct,
                    categories, never_worn, month_name
    """
    name       = user_data.get("name", "there").split()[0]
    budget     = float(user_data.get("budget", 0))
    spent      = float(user_data.get("spent", 0))
    remaining  = float(user_data.get("remaining", 0))
    budget_pct = float(user_data.get("budget_pct", 0))
    categories = user_data.get("categories", {})
    never_worn = int(user_data.get("never_worn", 0))
    month_name = user_data.get("month_name", datetime.now().strftime("%B %Y"))

    # Status color
    if budget_pct >= 90:
        status_color = "#e74c3c"
        status_bg    = "#fdf0f0"
        status_emoji = "🚨"
        status_text  = f"Over {budget_pct:.0f}% — spending too fast!"
    elif budget_pct >= 70:
        status_color = "#f39c12"
        status_bg    = "#fef9f0"
        status_emoji = "⚠️"
        status_text  = f"{budget_pct:.0f}% used — getting tight"
    else:
        status_color = "#27ae60"
        status_bg    = "#f0faf5"
        status_emoji = "✅"
        status_text  = f"On track — {budget_pct:.0f}% used"

    # Category rows
    cat_rows = ""
    for cat, amt in sorted(categories.items(), key=lambda x: -x[1])[:5]:
        pct_cat = (amt / spent * 100) if spent > 0 else 0
        bar_w   = min(int(pct_cat), 100)
        cat_rows += f"""
        <tr>
          <td style="padding:9px 0;border-bottom:1px solid #f5f3ff;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
              <span style="font-size:13px;color:#444;">{cat}</span>
              <span style="font-size:13px;font-weight:700;color:#7c6fa0;">₹{amt:,.0f}</span>
            </div>
            <div style="background:#ece8f5;border-radius:4px;height:5px;overflow:hidden;">
              <div style="background:linear-gradient(90deg,#7c6fa0,#a89cc8);height:5px;width:{bar_w}%;border-radius:4px;"></div>
            </div>
          </td>
        </tr>"""

    wardrobe_block = ""
    if never_worn > 0:
        wardrobe_block = f"""
        <div style="background:#fff8ec;border:1px solid #fde68a;border-radius:10px;padding:14px 16px;margin-bottom:16px;">
          <p style="margin:0;font-size:13px;color:#92400e;">
            👗 <strong>{never_worn} wardrobe item{'s' if never_worn > 1 else ''}</strong> never worn. 
            Wear them before buying anything new!
          </p>
        </div>"""

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    subject = f"fenora: Your {month_name} Financial Snapshot 📊"

    html_body = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>fenora Snapshot</title></head>
<body style="margin:0;padding:20px 10px;background:#f5f3fc;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
<div style="max-width:540px;margin:0 auto;">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#6b5fa0 0%,#a89cc8 100%);border-radius:16px 16px 0 0;padding:28px 24px;text-align:center;">
    <div style="font-size:11px;color:rgba(255,255,255,0.7);letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">fenora · smart finance</div>
    <h1 style="color:#fff;margin:0;font-size:20px;font-weight:800;">Financial Snapshot 📊</h1>
    <p style="color:rgba(255,255,255,0.75);margin:6px 0 0;font-size:13px;">Hey {name}! Here's your {month_name} summary.</p>
  </div>

  <!-- Body -->
  <div style="background:#fff;padding:24px;border-radius:0 0 16px 16px;border:1px solid #ede9f8;border-top:none;">

    <!-- Budget Status Card -->
    <div style="background:{status_bg};border-left:4px solid {status_color};border-radius:10px;padding:16px 18px;margin-bottom:20px;">
      <div style="font-size:11px;color:#888;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">
        {status_emoji} Budget Status
      </div>
      <div style="font-size:26px;font-weight:800;color:#1a1a2e;">₹{spent:,.0f}</div>
      <div style="font-size:12px;color:#666;margin-top:4px;">
        of ₹{budget:,.0f} budget · {budget_pct:.0f}% used · ₹{remaining:,.0f} remaining
      </div>
      <div style="font-size:12px;font-weight:600;color:{status_color};margin-top:6px;">{status_text}</div>
      <!-- Progress bar -->
      <div style="background:#e8e4f5;border-radius:6px;height:7px;margin-top:10px;overflow:hidden;">
        <div style="background:{status_color};height:7px;width:{min(budget_pct, 100):.0f}%;border-radius:6px;"></div>
      </div>
    </div>

    <!-- Category Breakdown -->
    <h3 style="font-size:13px;font-weight:700;color:#7c6fa0;text-transform:uppercase;letter-spacing:0.5px;margin:0 0 10px;">
      💳 Where Your Money Went
    </h3>
    <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
      <tbody>
        {cat_rows if cat_rows else "<tr><td style='padding:12px 0;color:#aaa;font-size:13px;'>No expenses this month</td></tr>"}
      </tbody>
    </table>

    <!-- Wardrobe Nudge -->
    {wardrobe_block}

    <!-- CTA -->
    <div style="text-align:center;margin-top:8px;">
      <a href="{frontend_url}" style="display:inline-block;background:linear-gradient(135deg,#6b5fa0,#a89cc8);color:#fff;padding:12px 28px;border-radius:50px;text-decoration:none;font-size:13px;font-weight:700;box-shadow:0 4px 16px rgba(107,95,160,0.3);">
        Open Dashboard →
      </a>
    </div>
  </div>

  <!-- Footer -->
  <div style="text-align:center;padding:16px;color:#bbb;font-size:11px;">
    fenora · Smart Budget & Wardrobe Intelligence<br>
    You're receiving this because you enabled email reminders.
  </div>

</div>
</body></html>"""

    plain_body = (
        f"fenora Financial Snapshot — {month_name}\n\n"
        f"Hi {name}!\n\n"
        f"Budget: ₹{budget:,.0f}\n"
        f"Spent:  ₹{spent:,.0f} ({budget_pct:.0f}%)\n"
        f"Left:   ₹{remaining:,.0f}\n\n"
        + ("TOP CATEGORIES\n" + "\n".join(f"  • {c}: ₹{v:,.0f}" for c, v in sorted(categories.items(), key=lambda x: -x[1])[:5]) + "\n\n" if categories else "")
        + (f"⚠️ {never_worn} wardrobe items never worn — wear them first!\n\n" if never_worn > 0 else "")
        + f"View dashboard: {frontend_url}\n\n— fenora AI"
    )

    return subject, html_body, plain_body


# ─────────────────────────────────────────────────────────────────────
# FLASK ROUTES  (paste these into app.py)
# ─────────────────────────────────────────────────────────────────────

def _f(val, default=0.0):
    if val is None:
        return float(default)
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


def register_email_routes(app, get_db, login_required, get_uid, _safe_json_fn):
    """
    Call this from app.py:
        from email_fix import register_email_routes
        register_email_routes(app, get_db, login_required, get_uid, _safe_json)
    """
    import psycopg2.extras

    @app.route("/api/test-email", methods=["POST"])
    @login_required
    def api_test_email_v2():
        """
        Sends a test email to the logged-in user.
        Returns detailed success/error info.
        POST /api/test-email
        """
        uid = get_uid()
        try:
            conn = get_db()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # User info
                cur.execute("SELECT name, email, monthly_budget FROM users WHERE id=%s", (uid,))
                user = cur.fetchone()
                if not user:
                    return jsonify({"success": False, "message": "User not found"}), 404

                today = datetime.now()

                # This month spending
                cur.execute(
                    "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
                    "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s",
                    (uid, today.month, today.year),
                )
                spent = _f(cur.fetchone()["t"])

                # Categories
                cur.execute(
                    "SELECT category, COALESCE(SUM(amount),0) AS total FROM expenses "
                    "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s "
                    "GROUP BY category ORDER BY total DESC LIMIT 5",
                    (uid, today.month, today.year),
                )
                categories = {r["category"]: _f(r["total"]) for r in cur.fetchall()}

                # Never worn
                cur.execute(
                    "SELECT COUNT(*) AS c FROM wardrobe_items WHERE user_id=%s AND wear_count=0",
                    (uid,),
                )
                never_worn = int(cur.fetchone()["c"])

            conn.close()
        except Exception as e:
            logger.error(f"[test-email] DB error: {e}")
            return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500

        budget     = _f(user["monthly_budget"])
        remaining  = max(0.0, budget - spent)
        budget_pct = (spent / budget * 100) if budget > 0 else 0

        user_data = {
            "name":       user["name"],
            "email":      user["email"],
            "budget":     budget,
            "spent":      spent,
            "remaining":  remaining,
            "budget_pct": budget_pct,
            "categories": categories,
            "never_worn": never_worn,
            "month_name": today.strftime("%B %Y"),
        }

        subject, html_body, plain_body = _build_snapshot_email(user_data)

        result = send_email_smtp(
            to_address=user["email"],
            subject=subject,
            html_body=html_body,
            plain_body=plain_body,
        )

        if result["success"]:
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
        else:
            # Return rich error so the UI can show actionable help
            return jsonify({
                "success": False,
                "message": result["error"] or "Email failed to send.",
                "hint":    result.get("hint", ""),
                "debug": {
                    "sender_set": bool(os.getenv("EMAIL_SENDER") or os.getenv("EMAIL_USER") or os.getenv("MAIL_USERNAME")),
                    "password_set": bool(os.getenv("EMAIL_PASSWORD") or os.getenv("EMAIL_PASS") or os.getenv("MAIL_PASSWORD")),
                    "recipient": user["email"],
                },
            }), 400

    @app.route("/api/email-debug", methods=["GET"])
    @login_required
    def api_email_debug():
        """
        Returns email configuration status WITHOUT exposing credentials.
        GET /api/email-debug
        """
        user, password = _get_smtp_credentials()
        return jsonify({
            "sender_configured":   bool(user),
            "password_configured": bool(password),
            "sender_preview":      (user[:3] + "***" + user[user.index("@"):]) if user and "@" in user else None,
            "env_var_checked": [
                "EMAIL_SENDER", "EMAIL_USER", "MAIL_USERNAME", "SMTP_USER",
                "EMAIL_PASSWORD", "EMAIL_PASS", "MAIL_PASSWORD", "SMTP_PASS",
            ],
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "method":    "STARTTLS",
            "hint": (
                "All good! Try sending a test email." if user and password
                else "Set EMAIL_SENDER and EMAIL_PASSWORD in your .env file. "
                     "Use a Gmail App Password from myaccount.google.com/apppasswords"
            ),
        })

    @app.route("/api/send-budget-alert", methods=["POST"])
    @login_required
    def api_send_budget_alert():
        """
        Sends a budget alert email when triggered manually or by scheduler.
        POST /api/send-budget-alert
        """
        uid = get_uid()
        try:
            conn = get_db()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT name, email, monthly_budget FROM users WHERE id=%s", (uid,))
                user = cur.fetchone()
                today = datetime.now()
                cur.execute(
                    "SELECT COALESCE(SUM(amount),0) AS t FROM expenses "
                    "WHERE user_id=%s AND EXTRACT(MONTH FROM created_at)=%s AND EXTRACT(YEAR FROM created_at)=%s",
                    (uid, today.month, today.year),
                )
                spent = _f(cur.fetchone()["t"])
            conn.close()
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

        budget     = _f(user["monthly_budget"])
        budget_pct = (spent / budget * 100) if budget > 0 else 0

        if budget_pct < 70:
            return jsonify({"success": False, "message": f"No alert needed — only {budget_pct:.0f}% used."})

        alert_level = "🚨 CRITICAL" if budget_pct >= 90 else "⚠️ WARNING"
        subject = f"fenora Budget Alert: {budget_pct:.0f}% Used {alert_level}"
        name = user["name"].split()[0]
        remaining = max(0.0, budget - spent)

        html = f"""
        <div style="font-family:sans-serif;max-width:500px;margin:auto;padding:20px;">
          <h2 style="color:#e74c3c;">{alert_level}: Budget Running {'Low' if budget_pct < 100 else 'Over'}!</h2>
          <p>Hi {name},</p>
          <p>Your fenora budget is at <strong style="color:#e74c3c;">{budget_pct:.0f}%</strong> this month.</p>
          <ul>
            <li>Budget: ₹{budget:,.0f}</li>
            <li>Spent: ₹{spent:,.0f}</li>
            <li>Remaining: ₹{remaining:,.0f}</li>
          </ul>
          <p>{'Avoid ALL non-essential spending for the rest of the month.' if budget_pct >= 90 else 'Slow down on non-essential purchases.'}</p>
          <p style="color:#888;font-size:12px;">— fenora AI</p>
        </div>"""

        plain = f"Budget Alert: {budget_pct:.0f}% Used\n\nBudget: ₹{budget:,.0f}\nSpent: ₹{spent:,.0f}\nRemaining: ₹{remaining:,.0f}\n\n— fenora AI"

        result = send_email_smtp(user["email"], subject, html, plain)
        if result["success"]:
            return jsonify({"success": True, "message": f"Alert sent to {user['email']}"})
        else:
            return jsonify({"success": False, "message": result["error"], "hint": result.get("hint")}), 400

    # Make jsonify available inside registered functions
    from flask import jsonify as _jsonify
    # Patch jsonify reference (since it's used inside nested functions)
    # This is handled automatically since flask.jsonify is imported at module level in app.py