"""
ml_spending.py
─────────────────────────────────────────────────────────
Run ONCE before starting app.py to train and save the model.

    python ml_spending.py

Then start the app:

    python app.py
"""

import logging, sys
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)])

from ml_spending_alert.db_handler import create_tables, seed_database, load_behavior_data
from ml_spending_alert.pipeline   import generate_synthetic_data, train_model


def main():
    print("\n" + "═"*55)
    print("  WardrobeIQ — ML Model Training")
    print("═"*55)

    print("\n[1/4] Verifying database tables...")
    create_tables()

    print("\n[2/4] Generating & seeding synthetic data...")
    synthetic_df = generate_synthetic_data()
    seed_database(synthetic_df)

    print("\n[3/4] Loading data from PostgreSQL...")
    db_df = load_behavior_data()
    db_df = db_df.merge(synthetic_df[["user_id","next_month_spending"]], on="user_id", how="left")

    print("\n[4/4] Training Linear Regression model...")
    model, scaler, metrics = train_model(db_df)

    print(f"\n{'═'*55}")
    print(f"  ✅  Training complete!")
    print(f"      MAE  : ₹{metrics['mae']}")
    print(f"      R²   : {metrics['r2']}")
    print(f"      Train: {metrics['n_train']} samples")
    print(f"      Test : {metrics['n_test']} samples")
    print(f"\n  Model saved to: ml_spending_alert/saved_model.pkl")
    print(f"  Now run: python app.py")
    print("═"*55 + "\n")


if __name__ == "__main__":
    main()