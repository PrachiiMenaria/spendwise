"""
wardrobe_ml_system/model.py
─────────────────────────────────────────────────────────
SpendingPredictor class used by the original wardrobe_ml_system
(kept for backward compatibility with reudemo.py / apps.py).

The main prediction system now lives in ml_spending_alert/pipeline.py.
"""

import os
import pickle
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, r2_score

from wardrobe_ml_system.ml_config import (
    MODEL_PATH,
    SCALER_PATH,
    SPENDING_ALERT_THRESHOLD,
    FEATURE_COLUMNS,
)
from wardrobe_ml_system.preprocessing import DataPreprocessor


class SpendingPredictor:
    """
    Trains, saves, loads, and runs spending predictions.
    Uses LinearRegression as primary model.
    """

    def __init__(self):
        self.primary_model    = LinearRegression()
        self.secondary_model  = DecisionTreeRegressor(max_depth=5, random_state=42)
        self.preprocessor     = DataPreprocessor()
        self.is_trained       = False
        self.training_metrics = {}

    # ── TRAIN ────────────────────────────────
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test:  np.ndarray,
        y_test:  np.ndarray,
    ) -> dict:
        """Train both models and return evaluation metrics."""
        self.primary_model.fit(X_train, y_train)
        self.secondary_model.fit(X_train, y_train)

        metrics = {}
        for name, mdl in [
            ("linear_regression", self.primary_model),
            ("decision_tree",     self.secondary_model),
        ]:
            preds = mdl.predict(X_test)
            metrics[name] = {
                "mae": mean_absolute_error(y_test, preds),
                "mse": float(np.mean((y_test - preds) ** 2)),
                "r2":  r2_score(y_test, preds),
            }

        self.is_trained       = True
        self.training_metrics = metrics
        print(f"Trained  → LR MAE: {metrics['linear_regression']['mae']:.2f}  "
              f"R²: {metrics['linear_regression']['r2']:.4f}")
        return metrics

    # ── PREDICT ──────────────────────────────
    def predict_spending(self, input_dict: dict) -> dict:
        """
        Predict spending for a single user dict.

        Returns dict with keys:
            predicted_spending, alert_triggered, alert_message (optional),
            monthly_budget, spending_threshold
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")

        X = self.preprocessor.preprocess_single_input(input_dict)
        raw_pred = float(self.primary_model.predict(X)[0])
        predicted = max(raw_pred, 0.0)

        budget    = input_dict.get("monthly_budget", 0)
        threshold = budget * SPENDING_ALERT_THRESHOLD
        alert     = predicted > threshold

        result = {
            "predicted_spending": round(predicted, 2),
            "alert_triggered":    alert,
            "monthly_budget":     budget,
            "spending_threshold": round(threshold, 2),
        }
        if alert:
            result["alert_message"] = (
                f"⚠️ Predicted spending ₹{predicted:,.0f} exceeds "
                f"{SPENDING_ALERT_THRESHOLD*100:.0f}% of your "
                f"₹{budget:,.0f} budget."
            )
        return result

    # ── SAVE ─────────────────────────────────
    def save_model(self, model_path: str = None, scaler_path: str = None):
        """Save model and scaler to disk."""
        mp = model_path  or MODEL_PATH
        sp = scaler_path or SCALER_PATH
        os.makedirs(os.path.dirname(mp), exist_ok=True)

        with open(mp, "wb") as f:
            pickle.dump(self.primary_model, f)
        self.preprocessor.save_scaler(sp)
        print(f"Model saved → {mp}")

    # ── LOAD ─────────────────────────────────
    def load_model(self, model_path: str = None, scaler_path: str = None):
        """Load model and scaler from disk."""
        mp = model_path  or MODEL_PATH
        sp = scaler_path or SCALER_PATH

        with open(mp, "rb") as f:
            self.primary_model = pickle.load(f)
        self.preprocessor.load_scaler(sp)
        self.is_trained = True
        print(f"Model loaded ← {mp}")