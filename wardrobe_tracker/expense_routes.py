from datetime import datetime
from flask import Blueprint, request, jsonify
from app import db
from app.models import Expense, User

expense_bp = Blueprint("expenses", __name__)

VALID_CATEGORIES = {"clothing", "food", "transport", "entertainment", "utilities", "health", "other"}


@expense_bp.route("/add", methods=["POST"])
def add_expense():
    """Add a new expense for a user."""
    data = request.get_json()

    required = ["user_id", "amount", "category"]
    if not all(k in data for k in required):
        return jsonify({"error": f"Missing required fields: {', '.join(required)}"}), 400

    if not User.query.get(data["user_id"]):
        return jsonify({"error": "User not found"}), 404

    category = data["category"].lower()
    if category not in VALID_CATEGORIES:
        return jsonify({
            "error": f"Invalid category. Valid options: {', '.join(VALID_CATEGORIES)}"
        }), 400

    expense_date = datetime.utcnow().date()
    if data.get("date"):
        try:
            expense_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    expense = Expense(
        user_id=data["user_id"],
        amount=float(data["amount"]),
        category=category,
        date=expense_date,
        description=data.get("description", ""),
    )
    db.session.add(expense)
    db.session.commit()

    return jsonify({"message": "Expense added", "expense": expense.to_dict()}), 201


@expense_bp.route("", methods=["GET"])
def get_expenses():
    """Get all expenses. Filter by user_id or category via query params."""
    user_id = request.args.get("user_id")
    category = request.args.get("category")

    query = Expense.query
    if user_id:
        if not User.query.get(user_id):
            return jsonify({"error": "User not found"}), 404
        query = query.filter_by(user_id=user_id)
    if category:
        query = query.filter_by(category=category.lower())

    expenses = query.order_by(Expense.date.desc()).all()
    total = sum(e.amount for e in expenses)

    return jsonify({
        "total_count": len(expenses),
        "total_amount": round(total, 2),
        "expenses": [e.to_dict() for e in expenses]
    }), 200


@expense_bp.route("/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    """Delete an expense."""
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense deleted"}), 200
