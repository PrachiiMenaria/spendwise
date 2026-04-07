"""
alert_engine.py
─────────────────────────────────────────────────────────
Risk classification and intelligent alert generation.

  classify_risk()     — Safe / Moderate / High Risk
  generate_alerts()   — context-aware alert messages
"""

import logging

from ml_spending_alert.constants import (
    HIGH_DECISION_TIME_MIN,
    HIGH_SHOPPING_FREQ,
    LEVEL_CRITICAL,
    LEVEL_INFO,
    LEVEL_WARNING,
    LOW_UTILIZATION_RATE,
    RISK_HIGH,
    RISK_MODERATE,
    RISK_SAFE,
    SAFE_LIMIT,
    WARN_LIMIT,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# RISK CLASSIFICATION
# ─────────────────────────────────────────────
def classify_risk(predicted: float, budget: float) -> tuple[str, float]:
    """
    Compare predicted spending against the user's budget and
    return a risk category with the budget-usage ratio.

    Thresholds (set in constants.py)
    ─────────────────────────────────
    ratio < SAFE_LIMIT            → Safe
    SAFE_LIMIT ≤ ratio < WARN_LIMIT → Moderate
    ratio ≥ WARN_LIMIT            → High Risk

    Parameters
    ----------
    predicted : float   next month's predicted spending
    budget    : float   user's monthly budget

    Returns
    -------
    (risk_category: str, budget_ratio: float)
    """
    ratio = predicted / max(budget, 1.0)

    if ratio < SAFE_LIMIT:
        category = RISK_SAFE
    elif ratio < WARN_LIMIT:
        category = RISK_MODERATE
    else:
        category = RISK_HIGH

    logger.debug(
        f"classify_risk  predicted={predicted:.0f}  "
        f"budget={budget:.0f}  ratio={ratio:.2%}  → {category}"
    )
    return category, round(ratio, 4)


# ─────────────────────────────────────────────
# ALERT GENERATION
# ─────────────────────────────────────────────
def generate_alerts(
    user_data: dict,
    predicted: float,
    risk:      str,
    ratio:     float,
) -> list[dict]:
    """
    Generate contextual, intelligent alerts by combining the
    ML prediction with domain-level behavioural signals.

    Alert triggers
    ──────────────
    1. Budget / risk level          → always fires (info / warning / critical)
    2. Low wardrobe utilization
       + moderate-or-high spending  → warning
    3. High shopping frequency      → warning  (impulse buying signal)
    4. High outfit decision time    → info     (wardrobe clutter signal)

    Each alert dict
    ───────────────
    {
        "type":    "info" | "warning" | "critical",
        "level":   "info" | "warning" | "critical",
        "message": "<human-readable string>"
    }

    Parameters
    ----------
    user_data : dict   raw user record (all BASE_FEATURES keys)
    predicted : float  predicted next-month spending
    risk      : str    output of classify_risk()
    ratio     : float  predicted / budget
    """
    alerts = []

    budget       = user_data["monthly_budget"]
    utilization  = (
        user_data["total_times_worn"]
        / max(user_data["wardrobe_size"], 1)
    )
    freq         = user_data["shopping_frequency"]
    decision_min = user_data["avg_outfit_decision_min"]

    # ── 1. Budget / risk ─────────────────────
    if risk == RISK_HIGH:
        over_pct = (ratio - 1.0) * 100
        alerts.append({
            "type":    LEVEL_CRITICAL,
            "level":   LEVEL_CRITICAL,
            "message": (
                f"🚨 You are likely to EXCEED your budget next month. "
                f"Predicted spend ₹{predicted:,.0f} is "
                f"{over_pct:.1f}% over your ₹{budget:,.0f} budget."
            ),
        })

    elif risk == RISK_MODERATE:
        used_pct = ratio * 100
        alerts.append({
            "type":    LEVEL_WARNING,
            "level":   LEVEL_WARNING,
            "message": (
                f"⚠️  You are approaching your budget limit. "
                f"Predicted spend ₹{predicted:,.0f} is "
                f"{used_pct:.1f}% of your ₹{budget:,.0f} budget."
            ),
        })

    else:  # Safe
        alerts.append({
            "type":    LEVEL_INFO,
            "level":   LEVEL_INFO,
            "message": (
                f"✅ You are on track! Predicted spend ₹{predicted:,.0f} "
                f"is comfortably within your ₹{budget:,.0f} budget "
                f"({ratio * 100:.1f}% used)."
            ),
        })

    # ── 2. Under-utilization + high spend ────
    if utilization < LOW_UTILIZATION_RATE and ratio >= SAFE_LIMIT:
        alerts.append({
            "type":    LEVEL_WARNING,
            "level":   LEVEL_WARNING,
            "message": (
                f"👗 You are under-utilising your wardrobe "
                f"(avg {utilization:.1f} wears/item) but still spending heavily. "
                "Wear what you own before buying new items."
            ),
        })

    # ── 3. Frequent shopping ─────────────────
    if freq > HIGH_SHOPPING_FREQ:
        alerts.append({
            "type":    LEVEL_WARNING,
            "level":   LEVEL_WARNING,
            "message": (
                f"🛍️  Frequent shopping detected ({freq:.1f}x/week). "
                "Impulse purchases are likely driving up your monthly spend."
            ),
        })

    # ── 4. High decision time → clutter ──────
    if decision_min > HIGH_DECISION_TIME_MIN:
        alerts.append({
            "type":    LEVEL_INFO,
            "level":   LEVEL_INFO,
            "message": (
                f"⏱️  Your average outfit decision time is {decision_min:.0f} min. "
                "A cluttered wardrobe wastes time and leads to buying duplicates — "
                "consider a declutter session."
            ),
        })

    logger.info(
        f"generate_alerts  user_id={user_data.get('user_id', '?')}  "
        f"risk={risk}  alerts_generated={len(alerts)}"
    )
    return alerts
