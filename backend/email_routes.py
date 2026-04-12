"""
email_routes.py — fenora Email System Routes
Place this file in: wardrobe-analysis-project/backend/email_routes.py
"""

from flask import Blueprint, request, jsonify, session
from functools import wraps
import logging
import psycopg2.extras

logger = logging.getLogger(__name__)

email_bp = Blueprint("fenora_email", __name__)


import os

def _login_required(f):
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
            jwt.decode(token, os.environ.get('SECRET_KEY', 'dev-key-123'), algorithms=["HS256"])
        except Exception as e:
            return jsonify({"error": "Invalid or expired token"}), 401
        return f(*a, **kw)
    return dec


def _get_uid():
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            import jwt
            data = jwt.decode(token, os.environ.get('SECRET_KEY', 'dev-key-123'), algorithms=["HS256"])
            return data["user_id"]
        except:
            pass
    return 1


# ── Test Email ────────────────────────────────────────────────────────

@email_bp.route("/api/test-email", methods=["POST"])
@_login_required
def api_test_email():
    from email_service import send_insight_email
    from app import get_db

    uid = _get_uid()
    is_weekly = (request.json or {}).get("weekly", False)

    try:
        result = send_insight_email(uid, get_db, is_weekly=is_weekly)
        return jsonify({
            "success": result.get("success", False),
            "message": (
                f"Test email sent to {result.get('to', 'your inbox')}! Check your email 📧"
                if result.get("success")
                else result.get("error", "Unknown error")
            ),
            "subject": result.get("subject", ""),
            "insights_summary": result.get("insights_summary", {}),
            "to": result.get("to", ""),
        })
    except Exception as e:
        logger.error(f"Test email error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ── Email Settings GET ────────────────────────────────────────────────

@email_bp.route("/api/email-settings", methods=["GET"])
@_login_required
def api_email_settings_get():
    from app import get_db

    uid = _get_uid()
    conn = get_db()
    row = None
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT email_reminders_enabled, email_frequency FROM users WHERE id = %s",
                (uid,),
            )
            row = cur.fetchone()
    except Exception:
        pass
    finally:
        conn.close()

    return jsonify({
        "email_reminders_enabled": row.get("email_reminders_enabled", True) if row else True,
        "email_frequency": row.get("email_frequency", "monthly") if row else "monthly",
    })


# ── Email Settings POST ───────────────────────────────────────────────

@email_bp.route("/api/email-settings", methods=["POST"])
@_login_required
def api_email_settings_post():
    from app import get_db

    uid = _get_uid()
    data = request.json or {}
    enabled = bool(data.get("email_reminders_enabled", True))
    frequency = data.get("email_frequency", "monthly")

    if frequency not in ("monthly", "weekly"):
        return jsonify({"error": "Frequency must be 'monthly' or 'weekly'"}), 400

    conn = get_db()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET email_reminders_enabled = %s, email_frequency = %s WHERE id = %s",
                (enabled, frequency, uid),
            )
        conn.close()
        return jsonify({"success": True, "message": "Settings saved!", "email_reminders_enabled": enabled, "email_frequency": frequency})
    except Exception as e:
        logger.error(f"Email settings save error: {e}")
        return jsonify({
            "success": False,
            "error": "Run this SQL first: ALTER TABLE users ADD COLUMN IF NOT EXISTS email_reminders_enabled BOOLEAN DEFAULT TRUE, ADD COLUMN IF NOT EXISTS email_frequency VARCHAR(10) DEFAULT 'monthly';"
        }), 500


# ── Email Preview (no send) ───────────────────────────────────────────

@email_bp.route("/api/email-preview", methods=["GET"])
@_login_required
def api_email_preview():
    from email_service import generate_email_insights, build_email_html
    from app import get_db

    uid = _get_uid()
    try:
        insights = generate_email_insights(uid, get_db)
        if not insights:
            return jsonify({"error": "Could not generate insights"}), 500
        content = build_email_html(insights)
        return jsonify({
            "subject": content["subject"],
            "html": content["html"],
            "insights": {
                "expense_insights": insights["expense_insights"],
                "wardrobe_insights": insights["wardrobe_insights"],
                "recommendations": insights["recommendations"],
                "summary": insights["summary"],
            }
        })
    except Exception as e:
        logger.error(f"Email preview error: {e}")
        return jsonify({"error": str(e)}), 500