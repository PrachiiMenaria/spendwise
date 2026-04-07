"""
reminder_engine.py
─────────────────────────────────────────────────────────
Reminder schedule logic.

  generate_reminders() — builds a personalised reminder list
                         based on risk level and behaviour signals.

Reminder vs Alert
─────────────────
Alerts  → triggered instantly on dashboard load / data entry.
          They are reactive: "you are about to exceed budget".

Reminders → scheduled for future delivery (weekly / monthly).
            They are proactive: "check in on Friday before shopping".
"""

import logging
from datetime import datetime, timedelta

from ml_spending_alert.constants import (
    FREQ_BIWEEKLY,
    FREQ_IMPULSE,
    FREQ_MONTHLY,
    FREQ_WEEKLY,
    HIGH_SHOPPING_FREQ,
    RISK_HIGH,
    RISK_MODERATE,
    RISK_SAFE,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# REMINDER GENERATION
# ─────────────────────────────────────────────
def generate_reminders(
    risk:  str,
    ratio: float,
    freq:  float,
) -> list[dict]:
    """
    Build a personalised reminder schedule for the next month.

    Schedule rules
    ──────────────
    High Risk  → 4 weekly reminders starting next week
    Moderate   → 2 bi-weekly reminders
    Safe       → 1 end-of-month summary reminder

    Extra trigger
    ─────────────
    shopping_frequency > HIGH_SHOPPING_FREQ
        → add an impulse-pause nudge 3 days from now

    Each reminder dict
    ──────────────────
    {
        "send_at":   "YYYY-MM-DD",
        "frequency": "weekly" | "bi-weekly" | "monthly" | "impulse-trigger",
        "message":   "<human-readable string>"
    }

    Parameters
    ----------
    risk  : str    output of classify_risk()
    ratio : float  predicted / budget
    freq  : float  shopping_frequency (purchases per week)
    """
    reminders = []
    today     = datetime.today()

    # ── Risk-based schedule ──────────────────
    if risk == RISK_HIGH:
        for week in range(1, 5):                    # 4 weekly nudges
            send_date = today + timedelta(weeks=week)
            reminders.append({
                "send_at":   send_date.strftime("%Y-%m-%d"),
                "frequency": FREQ_WEEKLY,
                "message": (
                    f"📅 Weekly Budget Check (week {week}/4): "
                    "Your spending is on a high-risk path. "
                    "Review this week's purchases and pause non-essential shopping."
                ),
            })

    elif risk == RISK_MODERATE:
        for i, label in enumerate(["mid-month", "end-of-month"], start=1):
            send_date = today + timedelta(weeks=i * 2)
            reminders.append({
                "send_at":   send_date.strftime("%Y-%m-%d"),
                "frequency": FREQ_BIWEEKLY,
                "message": (
                    f"📊 {label.title()} Spending Check: "
                    "You are on a moderate spending path. "
                    "Check your wardrobe before your next purchase — "
                    "you may already own what you need."
                ),
            })

    else:  # Safe
        end_of_month = today + timedelta(days=28)
        reminders.append({
            "send_at":   end_of_month.strftime("%Y-%m-%d"),
            "frequency": FREQ_MONTHLY,
            "message": (
                "📋 Monthly Wardrobe Summary: Great job staying within budget! "
                "Here is your spending and wardrobe utilisation report for the month."
            ),
        })

    # ── Impulse-trigger nudge ────────────────
    if freq > HIGH_SHOPPING_FREQ:
        nudge_date = today + timedelta(days=3)
        reminders.append({
            "send_at":   nudge_date.strftime("%Y-%m-%d"),
            "frequency": FREQ_IMPULSE,
            "message": (
                f"🛑 Shopping Pause Reminder: You currently shop "
                f"{freq:.1f}x per week. "
                "Before your next purchase, wait 48 hours — "
                "most impulse wants disappear by then."
            ),
        })

    logger.info(
        f"generate_reminders  risk={risk}  "
        f"reminders_scheduled={len(reminders)}"
    )
    return reminders
