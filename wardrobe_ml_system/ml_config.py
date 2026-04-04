"""
wardrobe_ml_system/ml_config.py
─────────────────────────────────────────────────────────
Configuration for the wardrobe_ml_system sub-package.

FIX: MODEL_PATH and SPENDING_ALERT_THRESHOLD were defined
     TWICE in the original file — second definition silently
     overwrote the first. Now each constant appears exactly once.
"""

import os

# ─── Database ────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     os.getenv("DB_PORT",     "5432"),
    "database": os.getenv("DB_NAME",     "wardrobe_db"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "wardrobe123"),
}

# ─── Model file paths ────────────────────────
MODEL_PATH            = "models/model.pkl"
SCALER_PATH           = "models/scaler.pkl"
FEATURE_COLUMNS_PATH  = "models/feature_columns.pkl"

# ─── Alert threshold ─────────────────────────
# Trigger warning when predicted > SPENDING_ALERT_THRESHOLD × budget
SPENDING_ALERT_THRESHOLD = 0.80     # 80 % of budget

# ─── Feature columns (must match preprocessing.py) ───
FEATURE_COLUMNS = [
    "monthly_budget",
    "total_clothing_spent_last_month",
    "number_of_purchases_last_month",
    "wardrobe_size",
    "total_times_worn",
    "average_decision_time_minutes",
    "shopping_frequency_per_month",
    "wardrobe_utilization_index",   # engineered
    "spending_ratio",               # engineered
]