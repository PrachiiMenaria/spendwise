"""
Flask Application for Wardrobe ML System.

Provides REST API endpoints for:
- Spending prediction
- User data retrieval
- Model management
- Health checks
"""

from flask import Flask, request, jsonify
from functools import wraps
import traceback
import os

from wardrobe_ml_system.model import SpendingPredictor
from wardrobe_ml_system.database import get_database
from wardrobe_ml_system.preprocessing import create_sample_data
from wardrobe_ml_system.ml_config import MODEL_PATH, SCALER_PATH, SPENDING_ALERT_THRESHOLD

# Initialize Flask app
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Global predictor instance (loaded once at startup)
predictor = None


def get_predictor() -> SpendingPredictor:
    """Get or initialize the global predictor."""
    global predictor
    if predictor is None:
        predictor = SpendingPredictor()
        
        # Try to load existing model
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            try:
                predictor.load_model()
                print("Loaded existing model from disk")
            except Exception as e:
                print(f"Failed to load model: {e}")
                print("Model needs to be trained via /train endpoint")
        else:
            print("No saved model found. Train via POST /train")
    
    return predictor


def handle_errors(f):
    """Decorator to handle exceptions uniformly across endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({
                "error": "Validation Error",
                "message": str(e)
            }), 400
        except FileNotFoundError as e:
            return jsonify({
                "error": "Resource Not Found",
                "message": str(e)
            }), 404
        except Exception as e:
            traceback.print_exc()
            return jsonify({
                "error": "Internal Server Error",
                "message": str(e)
            }), 500
    return decorated


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route("/", methods=["GET"])
def home():
    """API documentation endpoint."""
    return jsonify({
        "name": "Wardrobe Utilization and Responsible Clothing Consumption Analysis System",
        "version": "1.0.0",
        "endpoints": {
            "POST /predict_spending": "Predict next month's clothing spending",
            "GET /user/<user_id>": "Get user data from database",
            "POST /user/<user_id>/predict": "Predict for specific user from DB",
            "POST /train": "Train/retrain the model",
            "GET /model/status": "Get model status and metrics",
            "GET /health": "Health check"
        }
    })


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring."""
    pred = get_predictor()
    return jsonify({
        "status": "healthy",
        "model_loaded": pred.is_trained,
        "database": "connected"  # Would check actual connection in production
    })


@app.route("/predict_spending", methods=["POST"])
@handle_errors
def predict_spending():
    """
    Predict next month's spending from provided data.
    
    Expected JSON input:
    {
        "monthly_budget": float,
        "last_month_spending": float,
        "purchase_count": int,
        "wardrobe_size": int,
        "total_times_worn": int,
        "decision_time": float,
        "shopping_frequency": float
    }
    
    Returns:
    {
        "predicted_spending": float,
        "alert_triggered": bool,
        "alert_message": str (optional)
    }
    """
    # Get predictor
    pred = get_predictor()
    
    if not pred.is_trained:
        return jsonify({
            "error": "Model Not Ready",
            "message": "Model has not been trained. POST to /train first."
        }), 503
    
    # Parse request data
    data = request.get_json()
    
    if not data:
        return jsonify({
            "error": "Invalid Request",
            "message": "Request body must be JSON"
        }), 400
    
    # Map API field names to internal field names
    field_mapping = {
        "monthly_budget": "monthly_budget",
        "last_month_spending": "total_clothing_spent_last_month",
        "purchase_count": "number_of_purchases_last_month",
        "wardrobe_size": "wardrobe_size",
        "total_times_worn": "total_times_worn",
        "decision_time": "average_decision_time_minutes",
        "shopping_frequency": "shopping_frequency_per_month"
    }
    
    # Validate and transform input
    input_data = {}
    missing_fields = []
    
    for api_field, internal_field in field_mapping.items():
        if api_field in data:
            value = data[api_field]
            # Validate numeric type
            if not isinstance(value, (int, float)):
                return jsonify({
                    "error": "Validation Error",
                    "message": f"Field '{api_field}' must be a number"
                }), 400
            input_data[internal_field] = float(value)
        else:
            missing_fields.append(api_field)
    
    if missing_fields:
        return jsonify({
            "error": "Validation Error",
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    
    # Make prediction
    result = pred.predict_spending(input_data)
    
    # Format response
    response = {
        "predicted_spending": result["predicted_spending"],
        "alert_triggered": result["alert_triggered"]
    }
    
    if result["alert_triggered"]:
        response["alert_message"] = result["alert_message"]
    
    return jsonify(response)


@app.route("/user/<int:user_id>", methods=["GET"])
@handle_errors
def get_user_data(user_id: int):
    """
    Fetch user data from the database.
    
    Args:
        user_id: User ID from URL path
        
    Returns:
        User data if found, 404 if not
    """
    db = get_database()
    user_data = db.fetch_user_data(user_id)
    
    if user_data is None:
        return jsonify({
            "error": "Not Found",
            "message": f"User {user_id} not found"
        }), 404
    
    return jsonify({
        "user_id": user_id,
        "data": user_data
    })


@app.route("/user/<int:user_id>/predict", methods=["POST"])
@handle_errors
def predict_for_user(user_id: int):
    """
    Predict spending for a specific user using their database record.
    
    Fetches user data from database, makes prediction, and stores result.
    
    Args:
        user_id: User ID from URL path
        
    Returns:
        Prediction result
    """
    pred = get_predictor()
    
    if not pred.is_trained:
        return jsonify({
            "error": "Model Not Ready",
            "message": "Model has not been trained. POST to /train first."
        }), 503
    
    # Fetch user data from database
    db = get_database()
    user_data = db.fetch_user_data(user_id)
    
    if user_data is None:
        return jsonify({
            "error": "Not Found",
            "message": f"User {user_id} not found"
        }), 404
    
    # Remove user_id from prediction input
    prediction_input = {k: v for k, v in user_data.items() if k != "user_id"}
    
    # Make prediction
    result = pred.predict_spending(prediction_input)
    
    # Store prediction in database
    prediction_id = db.store_prediction(
        user_id=user_id,
        predicted_spending=result["predicted_spending"],
        alert_triggered=result["alert_triggered"],
        alert_message=result.get("alert_message")
    )
    
    # Format response
    response = {
        "user_id": user_id,
        "prediction_id": prediction_id,
        "predicted_spending": result["predicted_spending"],
        "alert_triggered": result["alert_triggered"],
        "monthly_budget": result["monthly_budget"],
        "spending_threshold": result["spending_threshold"]
    }
    
    if result["alert_triggered"]:
        response["alert_message"] = result["alert_message"]
    
    return jsonify(response)


@app.route("/user/<int:user_id>/history", methods=["GET"])
@handle_errors
def get_prediction_history(user_id: int):
    """
    Get prediction history for a user.
    
    Args:
        user_id: User ID from URL path
        
    Query params:
        limit: Maximum number of records (default 10)
    """
    limit = request.args.get("limit", 10, type=int)
    
    db = get_database()
    history = db.get_user_prediction_history(user_id, limit=limit)
    
    return jsonify({
        "user_id": user_id,
        "prediction_count": len(history),
        "history": history
    })


@app.route("/train", methods=["POST"])
@handle_errors
def train_model():
    """
    Train or retrain the model.
    
    Query params:
        source: "database" (use DB data) or "sample" (generate sample data)
        samples: Number of samples for sample data (default 1000)
    """
    global predictor
    
    source = request.args.get("source", "sample")
    n_samples = request.args.get("samples", 1000, type=int)
    
    if source == "database":
        # Fetch data from database
        db = get_database()
        df = db.fetch_all_users_data()
        
        if len(df) < 100:
            return jsonify({
                "error": "Insufficient Data",
                "message": f"Need at least 100 records, found {len(df)}"
            }), 400
    else:
        # Generate sample data
        df = create_sample_data(n_samples=n_samples)
    
    # Train model
    predictor = SpendingPredictor()
    X_train, X_test, y_train, y_test, _ = (
        predictor.preprocessor.preprocess_training_data(df)
    )
    metrics = predictor.train(X_train, y_train, X_test, y_test)
    
    # Save model
    predictor.save_model()
    
    return jsonify({
        "status": "success",
        "message": "Model trained successfully",
        "data_source": source,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "metrics": {
            "linear_regression": {
                "mae": round(metrics["linear_regression"]["mae"], 2),
                "r2_score": round(metrics["linear_regression"]["r2"], 4)
            },
            "decision_tree": {
                "mae": round(metrics["decision_tree"]["mae"], 2),
                "r2_score": round(metrics["decision_tree"]["r2"], 4)
            }
        }
    })


@app.route("/model/status", methods=["GET"])
@handle_errors
def model_status():
    """Get current model status and metrics."""
    pred = get_predictor()
    
    response = {
        "model_loaded": pred.is_trained,
        "model_type": "Linear Regression",
        "alert_threshold": SPENDING_ALERT_THRESHOLD
    }
    
    if pred.is_trained and pred.training_metrics:
        response["training_metrics"] = {
            "linear_regression": {
                "mae": round(pred.training_metrics["linear_regression"]["mae"], 2),
                "mse": round(pred.training_metrics["linear_regression"]["mse"], 2),
                "r2_score": round(pred.training_metrics["linear_regression"]["r2"], 4)
            }
        }
        
        # Include feature coefficients for interpretability
        if hasattr(pred.primary_model, "coef_"):
            coefficients = dict(zip(
                pred.preprocessor.feature_columns,
                [round(c, 4) for c in pred.primary_model.coef_]
            ))
            response["feature_coefficients"] = coefficients
            response["intercept"] = round(pred.primary_model.intercept_, 4)
    
    return jsonify(response)


# =============================================================================
# APPLICATION STARTUP
# =============================================================================

def initialize_app():
    """Initialize application components on startup."""
    print("\n" + "=" * 60)
    print("Initializing Wardrobe ML System...")
    print("=" * 60)
    
    # Initialize predictor (loads model if exists)
    get_predictor()
    
    # Try to initialize database (non-fatal if fails)
    try:
        db = get_database()
        db.create_tables()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("API will work but database features will be unavailable")
    
    print("=" * 60)
    print("System initialized. Ready to accept requests.")
    print("=" * 60 + "\n")


# Initialize on module load
initialize_app()
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        data = {
            "monthly_budget": float(request.form['monthly_budget']),
            "last_month_spending": float(request.form['last_spending']),
            "purchase_count": int(request.form['purchase_count']),
            "wardrobe_size": int(request.form['wardrobe_size']),
            "total_times_worn": int(request.form['total_times_worn']),
            "decision_time": float(request.form['decision_time']),
            "shopping_frequency": float(request.form['shopping_frequency'])
        }

        result = predict_spending(data)

        return render_template("result.html", result=result)

    return render_template("predict.html")

if __name__ == "__main__":
    # Run Flask development server
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
