"""
db_handler.py
─────────────────────────────────────────────────────────
All PostgreSQL operations:
  - Connection helper
  - Table creation / DDL
  - Seed synthetic data
  - Load data for training
  - Save predictions and alert logs
"""

import json
import logging

import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras

from ml_spending_alert.constants import DB_CONFIG

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────
def get_connection():
    """Return a live psycopg2 connection using DB_CONFIG."""
    return psycopg2.connect(**DB_CONFIG)


# ─────────────────────────────────────────────
# DDL — create tables
# ─────────────────────────────────────────────
def create_tables():
    """
    Create all required tables if they do not already exist.
    Safe to call on every startup.
    """
    ddl = """
    CREATE TABLE IF NOT EXISTS user_behavior (
        id                      SERIAL PRIMARY KEY,
        user_id                 INTEGER NOT NULL,
        monthly_budget          FLOAT   NOT NULL,
        last_month_spending     FLOAT   NOT NULL,
        num_purchases           INTEGER NOT NULL,
        wardrobe_size           INTEGER NOT NULL,
        total_times_worn        INTEGER NOT NULL,
        avg_outfit_decision_min FLOAT   NOT NULL,
        shopping_frequency      FLOAT   NOT NULL,
        created_at              TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS ml_predictions (
        id                  SERIAL PRIMARY KEY,
        user_id             INTEGER      NOT NULL,
        predicted_spending  FLOAT        NOT NULL,
        risk_category       VARCHAR(20)  NOT NULL,
        budget_ratio        FLOAT        NOT NULL,
        alerts              JSONB,
        reminders           JSONB,
        predicted_at        TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS alert_log (
        id           SERIAL PRIMARY KEY,
        user_id      INTEGER     NOT NULL,
        alert_type   VARCHAR(20) NOT NULL,
        alert_level  VARCHAR(20) NOT NULL,
        message      TEXT        NOT NULL,
        is_read      BOOLEAN     DEFAULT FALSE,
        created_at   TIMESTAMP   DEFAULT NOW()
    );
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()
    logger.info("Tables verified / created successfully.")


# ─────────────────────────────────────────────
# SEED
# ─────────────────────────────────────────────
def seed_database(df: pd.DataFrame):
    """
    Insert synthetic records into user_behavior.
    Skips silently if the table already contains rows.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain all BASE_FEATURES columns plus user_id.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM user_behavior;")
            if cur.fetchone()[0] > 0:
                logger.info("user_behavior already populated – skipping seed.")
                return

            records = [
                (
                    int(row.user_id),
                    float(row.monthly_budget),
                    float(row.last_month_spending),
                    int(row.num_purchases),
                    int(row.wardrobe_size),
                    int(row.total_times_worn),
                    float(row.avg_outfit_decision_min),
                    float(row.shopping_frequency),
                )
                for row in df.itertuples(index=False)
            ]

            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO user_behavior
                    (user_id, monthly_budget, last_month_spending,
                     num_purchases, wardrobe_size, total_times_worn,
                     avg_outfit_decision_min, shopping_frequency)
                VALUES %s
                """,
                records,
            )
        conn.commit()
    logger.info(f"Seeded {len(df)} rows into user_behavior.")


# ─────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────
def load_behavior_data() -> pd.DataFrame:
    """
    Load all rows from user_behavior and return as DataFrame.
    """
    with get_connection() as conn:
        df = pd.read_sql(
            "SELECT * FROM user_behavior ORDER BY id;", conn
        )
    logger.info(f"Loaded {len(df)} rows from user_behavior.")
    return df


def load_user_by_id(user_id: int) -> dict:
    """
    Fetch a single user's latest behavior record as a plain dict.
    Raises ValueError if user not found.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM user_behavior
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 1;
                """,
                (user_id,),
            )
            row = cur.fetchone()

    if row is None:
        raise ValueError(f"No behavior data found for user_id={user_id}.")
    return dict(row)


# ─────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────
def save_prediction(
    user_id:   int,
    predicted: float,
    risk:      str,
    ratio:     float,
    alerts:    list,
    reminders: list,
):
    """
    Persist one prediction record to ml_predictions.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ml_predictions
                    (user_id, predicted_spending, risk_category,
                     budget_ratio, alerts, reminders)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    round(predicted, 2),
                    risk,
                    round(ratio, 4),
                    json.dumps(alerts),
                    json.dumps(reminders),
                ),
            )
        conn.commit()
    logger.info(f"Prediction saved  →  user_id={user_id}  risk={risk}")


def log_alerts(user_id: int, alerts: list):
    """
    Write each alert dict to alert_log for dashboard consumption.
    Each dict must have keys: type, level, message.
    """
    if not alerts:
        return

    with get_connection() as conn:
        with conn.cursor() as cur:
            records = [
                (user_id, a["type"], a["level"], a["message"])
                for a in alerts
            ]
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO alert_log
                    (user_id, alert_type, alert_level, message)
                VALUES %s
                """,
                records,
            )
        conn.commit()
    logger.info(f"{len(alerts)} alert(s) logged  →  user_id={user_id}")


# ─────────────────────────────────────────────
# FETCH RESULTS  (for Flask routes / dashboard)
# ─────────────────────────────────────────────
def fetch_latest_prediction(user_id: int) -> dict | None:
    """
    Return the most recent ml_predictions row for a user, or None.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM ml_predictions
                WHERE user_id = %s
                ORDER BY predicted_at DESC
                LIMIT 1;
                """,
                (user_id,),
            )
            row = cur.fetchone()
    return dict(row) if row else None


def fetch_unread_alerts(user_id: int) -> list[dict]:
    """
    Return all unread alerts for a user ordered by newest first.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM alert_log
                WHERE user_id = %s AND is_read = FALSE
                ORDER BY created_at DESC;
                """,
                (user_id,),
            )
            rows = cur.fetchall()
    return [dict(r) for r in rows]
