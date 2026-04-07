"""
Quick demonstration of the Wardrobe ML System.
Runs without PostgreSQL - uses sample data only.
"""

from preprocessing import create_sample_data, DataPreprocessor
from model import SpendingPredictor

def main():
    print("=" * 60)
    print("WARDROBE ML SYSTEM - Quick Demo")
    print("=" * 60)
    
    # Generate sample data
    print("\n1. Generating sample data...")
    df = create_sample_data(n_samples=1000)
    print(f"   Created {len(df)} samples")
    
    # Initialize and preprocess
    print("\n2. Preprocessing data...")
    predictor = SpendingPredictor()
    X_train, X_test, y_train, y_test, _ = (
        predictor.preprocessor.preprocess_training_data(df)
    )
    
    # Train
    print("\n3. Training models...")
    metrics = predictor.train(X_train, y_train, X_test, y_test)
    
    # Save
    print("\n4. Saving model...")
    predictor.save_model()
    
    # Test prediction
    print("\n5. Testing prediction...")
    test_cases = [
        {
            "name": "Low spender",
            "data": {
                "monthly_budget": 300,
                "total_clothing_spent_last_month": 50,
                "number_of_purchases_last_month": 1,
                "wardrobe_size": 40,
                "total_times_worn": 200,
                "average_decision_time_minutes": 5,
                "shopping_frequency_per_month": 0.5
            }
        },
        {
            "name": "High spender",
            "data": {
                "monthly_budget": 500,
                "total_clothing_spent_last_month": 400,
                "number_of_purchases_last_month": 8,
                "wardrobe_size": 100,
                "total_times_worn": 50,
                "average_decision_time_minutes": 25,
                "shopping_frequency_per_month": 6
            }
        }
    ]
    
    for case in test_cases:
        result = predictor.predict_spending(case["data"])
        print(f"\n   {case['name']}:")
        print(f"   Budget: ${case['data']['monthly_budget']}")
        print(f"   Predicted: ${result['predicted_spending']}")
        print(f"   Alert: {'⚠️ YES' if result['alert_triggered'] else '✓ No'}")
    
    print("\n" + "=" * 60)
    print("Demo complete! Model saved to models/ directory.")
    print("Run 'python app.py' to start the Flask API.")
    print("=" * 60)

if __name__ == "__main__":
    main()
