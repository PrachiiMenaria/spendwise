"""
ml_spending_alert/constants.py
──────────────────────────────────────────────────────────
FIX: MODEL_PATH and SCALER_PATH now point to the ACTUAL locations
     as seen in your VS Code file tree:
     ml_spending_alert/saved_model.pkl
     ml_spending_alert/saved_scaler.pkl
"""

import os

# ── Database ──
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     os.getenv("DB_PORT",     "5432"),
    "database": os.getenv("DB_NAME",     "wardrobe_db"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "wardrobe123"),
}

# ── Model paths — matches your actual VS Code file tree ──
# Your saved_model.pkl is in ml_spending_alert/ (same level as this file)
MODEL_PATH  = os.path.join(os.path.dirname(__file__), "saved_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "saved_scaler.pkl")

# ── Thresholds ──
SAFE_LIMIT = 0.80
WARN_LIMIT = 1.00

RISK_SAFE     = "Safe"
RISK_MODERATE = "Moderate"
RISK_HIGH     = "High Risk"

LEVEL_INFO     = "info"
LEVEL_WARNING  = "warning"
LEVEL_CRITICAL = "critical"

FREQ_WEEKLY   = "weekly"
FREQ_BIWEEKLY = "bi-weekly"
FREQ_MONTHLY  = "monthly"
FREQ_IMPULSE  = "impulse-trigger"

LOW_UTILIZATION_RATE   = 2.0
HIGH_SHOPPING_FREQ     = 3.0
HIGH_DECISION_TIME_MIN = 20

BASE_FEATURES = [
    "monthly_budget",
    "last_month_spending",
    "num_purchases",
    "wardrobe_size",
    "total_times_worn",
    "avg_outfit_decision_min",
    "shopping_frequency",
]
ENGINEERED_FEATURES = [
    "utilization_rate",
    "spending_to_budget_ratio",
    "purchase_rate_per_item",
]
ALL_FEATURES = BASE_FEATURES + ENGINEERED_FEATURES

SYNTHETIC_N_USERS = 300
SYNTHETIC_SEED    = 42