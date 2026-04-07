"""
main.py
─────────────────────────────────────────────────────────
Entry point for the ML-Based Spending Reminder & Alert System.

Run modes
─────────
  python -m ml_spending_alert.main               ← full setup + demo user
  python -m ml_spending_alert.main --train-only  ← setup & train, no demo
  python -m ml_spending_alert.main --user 5      ← predict for user_id=5

What this does on a fresh run
──────────────────────────────
  1. Create PostgreSQL tables (safe to re-run)
  2. Generate 300 synthetic users and seed the DB
  3. Load data and train a Linear Regression model
  4. Run the full pipeline for a demo user
  5. Run batch predictions for all users and print a summary
"""

import argparse
import logging
import sys

import pandas as pd

from ml_spending_alert.alert_engine   import classify_risk, generate_alerts
from ml_spending_alert.db_handler     import (
    create_tables,
    fetch_latest_prediction,
    load_behavior_data,
    load_user_by_id,
    log_alerts,
    save_prediction,
    seed_database,
)
from ml_spending_alert.pipeline       import (
    generate_synthetic_data,
    load_trained_model,
    predict_batch,
    predict_spending,
    train_model,
)
from ml_spending_alert.reminder_engine import generate_reminders

# ─────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# DEMO USER  (edit to test different scenarios)
# ─────────────────────────────────────────────
DEMO_USER = {
    "user_id":                 1,
    "monthly_budget":          8_000.0,
    "last_month_spending":     7_200.0,
    "num_purchases":           12,
    "wardrobe_size":           60,
    "total_times_worn":        90,
    "avg_outfit_decision_min": 22.0,
    "shopping_frequency":      3.8,
}


# ═════════════════════════════════════════════
# CORE PIPELINE  (single user)
# ═════════════════════════════════════════════
def run_pipeline(user_data: dict, model=None, scaler=None) -> dict:
    """
    Full ML pipeline for one user.

    Steps
    ─────
    predict → classify → generate alerts → generate reminders
    → save to DB → return result dict

    Parameters
    ----------
    user_data : dict   must contain all BASE_FEATURES keys + user_id
    model, scaler      pass in if already loaded; loads from disk otherwise

    Returns
    -------
    dict with keys:
        user_id, predicted_spending, risk_category,
        budget_ratio, budget, alerts, reminders
    """
    if model is None or scaler is None:
        model, scaler = load_trained_model()

    user_id = user_data.get("user_id", 0)
    budget  = user_data["monthly_budget"]

    predicted          = predict_spending(user_data, model, scaler)
    risk, ratio        = classify_risk(predicted, budget)
    alerts             = generate_alerts(user_data, predicted, risk, ratio)
    reminders          = generate_reminders(risk, ratio, user_data["shopping_frequency"])

    save_prediction(user_id, predicted, risk, ratio, alerts, reminders)
    log_alerts(user_id, alerts)

    result = {
        "user_id":            user_id,
        "predicted_spending": round(predicted, 2),
        "risk_category":      risk,
        "budget_ratio":       ratio,
        "budget":             budget,
        "alerts":             alerts,
        "reminders":          reminders,
    }
    _print_result(result)
    return result


# ═════════════════════════════════════════════
# BATCH PIPELINE  (all users in DB)
# ═════════════════════════════════════════════
def run_batch_pipeline(model=None, scaler=None) -> pd.DataFrame:
    """
    Run the full pipeline for every user in user_behavior
    and return a summary DataFrame.
    """
    if model is None or scaler is None:
        model, scaler = load_trained_model()

    df    = load_behavior_data()
    preds = predict_batch(df, model, scaler)

    rows = []
    for i, row in df.iterrows():
        user_data          = row.to_dict()
        user_data["user_id"] = int(row.get("user_id", i))
        predicted          = float(preds[i])
        risk, ratio        = classify_risk(predicted, row["monthly_budget"])
        alerts             = generate_alerts(user_data, predicted, risk, ratio)
        reminders          = generate_reminders(risk, ratio, row["shopping_frequency"])

        save_prediction(user_data["user_id"], predicted, risk,
                        ratio, alerts, reminders)
        log_alerts(user_data["user_id"], alerts)

        rows.append({
            "user_id":            user_data["user_id"],
            "budget":             round(row["monthly_budget"], 2),
            "predicted_spending": round(predicted, 2),
            "risk_category":      risk,
            "budget_ratio_%":     round(ratio * 100, 1),
            "num_alerts":         len(alerts),
            "num_reminders":      len(reminders),
        })

    summary = pd.DataFrame(rows)

    safe_n     = (summary["risk_category"] == "Safe").sum()
    moderate_n = (summary["risk_category"] == "Moderate").sum()
    high_n     = (summary["risk_category"] == "High Risk").sum()

    logger.info(
        f"Batch complete — {len(summary)} users  |  "
        f"Safe: {safe_n}  Moderate: {moderate_n}  High Risk: {high_n}"
    )
    return summary


# ─────────────────────────────────────────────
# PRETTY PRINT
# ─────────────────────────────────────────────
def _print_result(r: dict):
    sep = "─" * 62
    print(f"\n{sep}")
    print(f"  User ID           : {r['user_id']}")
    print(f"  Monthly Budget    : ₹{r['budget']:>10,.2f}")
    print(f"  Predicted Spending: ₹{r['predicted_spending']:>10,.2f}")
    print(f"  Budget Used       : {r['budget_ratio'] * 100:>6.1f}%")
    print(f"  Risk Category     : {r['risk_category']}")

    print(f"\n  ALERTS  ({len(r['alerts'])})")
    for a in r["alerts"]:
        tag = f"[{a['level'].upper():8s}]"
        print(f"    {tag}  {a['message']}")

    print(f"\n  REMINDERS  ({len(r['reminders'])})")
    for rem in r["reminders"]:
        print(f"    [{rem['send_at']}]  {rem['message']}")

    print(sep + "\n")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def _parse_args():
    parser = argparse.ArgumentParser(
        description="ML Spending Reminder & Alert System"
    )
    parser.add_argument(
        "--train-only", action="store_true",
        help="Setup + train the model, then exit without running predictions."
    )
    parser.add_argument(
        "--user", type=int, default=None,
        help="Run pipeline for a specific user_id already in the DB."
    )
    return parser.parse_args()


# ═════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════
def main():
    args = _parse_args()

    # ── Step 1: DB setup ──────────────────────
    logger.info("Step 1/5 — Verifying database tables...")
    create_tables()

    # ── Step 2: Seed synthetic data ───────────
    logger.info("Step 2/5 — Seeding synthetic data...")
    synthetic_df = generate_synthetic_data()
    seed_database(synthetic_df)

    # ── Step 3: Load + train ──────────────────
    logger.info("Step 3/5 — Loading data and training model...")
    db_df = load_behavior_data()

    # Attach target column from synthetic generation for training
    db_df = db_df.merge(
        synthetic_df[["user_id", "next_month_spending"]],
        on="user_id", how="left",
    )
    model, scaler, metrics = train_model(db_df)
    print(
        f"\n  ✔  Training complete — "
        f"MAE: ₹{metrics['mae']}  |  R²: {metrics['r2']}\n"
    )

    if args.train_only:
        logger.info("--train-only flag set. Exiting after training.")
        return

    # ── Step 4: Single-user prediction ────────
    if args.user:
        logger.info(f"Step 4/5 — Running pipeline for user_id={args.user}...")
        user_data = load_user_by_id(args.user)
        run_pipeline(user_data, model, scaler)
    else:
        logger.info("Step 4/5 — Running pipeline for demo user...")
        run_pipeline(DEMO_USER, model, scaler)

    # ── Step 5: Batch predictions ─────────────
    logger.info("Step 5/5 — Running batch predictions for all users...")
    summary = run_batch_pipeline(model, scaler)

    print("\n  BATCH SUMMARY (first 10 users)")
    print(summary.head(10).to_string(index=False))
    print()


if __name__ == "__main__":
    main()
