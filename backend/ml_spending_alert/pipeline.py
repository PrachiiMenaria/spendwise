import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from ml_spending_alert.constants import (
    ALL_FEATURES,
    MODEL_PATH,
    SCALER_PATH,
    SYNTHETIC_N_USERS,
    SYNTHETIC_SEED,
)

logger = logging.getLogger(__name__)


def load_trained_model():
    import os
    for path in (MODEL_PATH, SCALER_PATH):
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} not found. Train model first.")

    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    return model, scaler

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# SYNTHETIC DATA GENERATION
# ─────────────────────────────────────────────
def generate_synthetic_data(
    n_users: int = SYNTHETIC_N_USERS,
    seed:    int = SYNTHETIC_SEED,
) -> pd.DataFrame:
    """
    Generate realistic synthetic user-behaviour records.

    The target column (next_month_spending) is derived from a
    domain-weighted formula plus controlled Gaussian noise so
    that Linear Regression can meaningfully learn from it.

    Returns
    -------
    pd.DataFrame with columns:
        user_id, monthly_budget, last_month_spending,
        num_purchases, wardrobe_size, total_times_worn,
        avg_outfit_decision_min, shopping_frequency,
        next_month_spending  ← training target
    """
    rng = np.random.default_rng(seed)

    monthly_budget          = rng.uniform(3_000,  15_000, n_users)
    last_month_spending     = monthly_budget * rng.uniform(0.5, 1.3, n_users)
    num_purchases           = rng.integers(1, 20,  n_users)
    wardrobe_size           = rng.integers(20, 150, n_users)
    total_times_worn        = rng.integers(10, 500, n_users)
    avg_outfit_decision_min = rng.uniform(2, 30,   n_users)
    shopping_frequency      = rng.uniform(0.5, 5,  n_users)   # per week

    # Ground-truth spending formula (domain rules baked in)
    next_month_spending = (
        0.55 * last_month_spending
        + 200  * shopping_frequency
        + 150  * num_purchases
        + 0.05 * avg_outfit_decision_min * 1_000
        - 0.3  * (total_times_worn / np.maximum(wardrobe_size, 1)) * 1_000
        + rng.normal(0, 500, n_users)               # noise
    ).clip(500, 25_000)

    df = pd.DataFrame({
        "user_id":                 np.arange(1, n_users + 1),
        "monthly_budget":          monthly_budget.round(2),
        "last_month_spending":     last_month_spending.round(2),
        "num_purchases":           num_purchases,
        "wardrobe_size":           wardrobe_size,
        "total_times_worn":        total_times_worn,
        "avg_outfit_decision_min": avg_outfit_decision_min.round(2),
        "shopping_frequency":      shopping_frequency.round(2),
        "next_month_spending":     next_month_spending.round(2),
    })

    logger.info(f"Generated {len(df)} synthetic records.")
    return df


# ─────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived columns that improve model accuracy.

    New columns
    ───────────
    utilization_rate        — avg times each wardrobe item is worn
    spending_to_budget_ratio — last month's spend as fraction of budget
    purchase_rate_per_item  — purchases relative to wardrobe size
    """
    df = df.copy()

    df["utilization_rate"] = (
        df["total_times_worn"] / df["wardrobe_size"].clip(lower=1)
    ).round(4)

    df["spending_to_budget_ratio"] = (
        df["last_month_spending"] / df["monthly_budget"].clip(lower=1)
    ).round(4)

    df["purchase_rate_per_item"] = (
        df["num_purchases"] / df["wardrobe_size"].clip(lower=1)
    ).round(4)

    return df


# ─────────────────────────────────────────────
# TRAIN
# ─────────────────────────────────────────────
def train_model(df: pd.DataFrame) -> tuple[LinearRegression, StandardScaler, dict]:
    """
    Train a Linear Regression model on df and persist it with joblib.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ALL_FEATURES columns AND a target column
        (next_month_spending preferred; falls back to last_month_spending).

    Returns
    -------
    (model, scaler, metrics)
        metrics keys: mae, r2, n_train, n_test
    """
    df = engineer_features(df)

    target_col = (
        "next_month_spending"
        if "next_month_spending" in df.columns
        else "last_month_spending"
    )

    X = df[ALL_FEATURES].fillna(0)
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    scaler      = StandardScaler()
    X_train_sc  = scaler.fit_transform(X_train)
    X_test_sc   = scaler.transform(X_test)

    model = LinearRegression()
    model.fit(X_train_sc, y_train)

    y_pred  = model.predict(X_test_sc)
    metrics = {
        "mae":     round(mean_absolute_error(y_test, y_pred), 2),
        "r2":      round(r2_score(y_test, y_pred), 4),
        "n_train": len(X_train),
        "n_test":  len(X_test),
    }

    joblib.dump(model,  MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    logger.info(
        f"Model trained  →  MAE: ₹{metrics['mae']}  |  R²: {metrics['r2']}  "
        f"| train: {metrics['n_train']}  test: {metrics['n_test']}"
    )
    logger.info(f"Saved → {MODEL_PATH}  {SCALER_PATH}")
    return model, scaler, metrics


# ─────────────────────────────────────────────
# LOAD SAVED MODEL
# ─────────────────────────────────────────────
def load_trained_model() -> tuple[LinearRegression, StandardScaler]:
    """
    Load a previously trained model and scaler from disk.
    Raises FileNotFoundError if train_model() has not been run yet.
    """
    import os
    for path in (MODEL_PATH, SCALER_PATH):
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"{path} not found. Run train_model() first."
            )
    model  = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    logger.info("Model and scaler loaded from disk.")
    return model, scaler


# ─────────────────────────────────────────────
# PREDICT — single user
# ─────────────────────────────────────────────
def predict_spending(
    user_data: dict,
    model:     LinearRegression,
    scaler:    StandardScaler,
) -> float:
    """
    Predict next month's spending for one user.

    Parameters
    ----------
    user_data : dict
        Must contain all BASE_FEATURES keys.

    Returns
    -------
    float  — predicted spending (clipped to >= 0)
    """
    row  = pd.DataFrame([user_data])
    row  = engineer_features(row)
    X    = row[ALL_FEATURES].fillna(0)
    X_sc = scaler.transform(X)
    return float(max(model.predict(X_sc)[0], 0.0))


# ─────────────────────────────────────────────
# PREDICT — batch (all users in a DataFrame)
# ─────────────────────────────────────────────
def predict_batch(
    df:     pd.DataFrame,
    model:  LinearRegression,
    scaler: StandardScaler,
) -> np.ndarray:
    """
    Predict next month's spending for every row in df.

    Returns
    -------
    np.ndarray of floats, same length as df, all >= 0.
    """
    df_eng  = engineer_features(df)
    X       = df_eng[ALL_FEATURES].fillna(0)
    X_sc    = scaler.transform(X)
    preds   = model.predict(X_sc).clip(min=0)
    return preds
