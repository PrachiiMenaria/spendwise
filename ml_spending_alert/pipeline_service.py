from ml_spending_alert.pipeline import load_trained_model, predict_spending
from ml_spending_alert.alert_engine import classify_risk, generate_alerts
from ml_spending_alert.reminder_engine import generate_reminders

def run_pipeline(user_data):
    model, scaler = load_trained_model()

    predicted = predict_spending(user_data, model, scaler)
    risk, ratio = classify_risk(predicted, user_data["monthly_budget"])
    alerts = generate_alerts(user_data, predicted, risk, ratio)
    reminders = generate_reminders(risk, ratio, user_data["shopping_frequency"])

    return {
        "prediction": predicted,
        "risk": risk,
        "alerts": alerts,
        "reminders": reminders
    }