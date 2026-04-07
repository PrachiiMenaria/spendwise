from flask import Blueprint, request, jsonify
from sqlalchemy import func
from app.models import WardrobeItem, Expense, User
from app import db

insight_bp = Blueprint("insights", __name__)

# Monthly clothing budget threshold for overspending detection
CLOTHING_BUDGET_THRESHOLD = 5000  # INR — adjust as needed


def get_overspending_alerts(user_id):
    """
    Detect overspending patterns:
    - Monthly clothing spend vs threshold
    - Items with 0 wears (dead stock)
    - High cost-per-wear items
    """
    alerts = []

    # 1. Monthly clothing expense overspending
    monthly_clothing = (
        db.session.query(
            func.strftime("%Y-%m", Expense.date).label("month"),
            func.sum(Expense.amount).label("total")
        )
        .filter(Expense.user_id == user_id, Expense.category == "clothing")
        .group_by("month")
        .all()
    )
    for row in monthly_clothing:
        if row.total and row.total > CLOTHING_BUDGET_THRESHOLD:
            alerts.append({
                "type": "overspending",
                "message": f"You spent ₹{round(row.total, 2)} on clothing in {row.month}, which exceeds the ₹{CLOTHING_BUDGET_THRESHOLD} threshold."
            })

    # 2. Never worn items (dead stock)
    never_worn = WardrobeItem.query.filter_by(user_id=user_id, times_worn=0).count()
    if never_worn > 0:
        alerts.append({
            "type": "dead_stock",
            "message": f"You have {never_worn} item(s) that have never been worn. Consider wearing or donating them."
        })

    # 3. High cost-per-wear items (worn <= 2 times but cost > 2000)
    expensive_low_use = WardrobeItem.query.filter(
        WardrobeItem.user_id == user_id,
        WardrobeItem.times_worn <= 2,
        WardrobeItem.times_worn > 0,
        WardrobeItem.purchase_price > 2000
    ).all()
    for item in expensive_low_use:
        cpw = round(item.purchase_price / item.times_worn, 2)
        alerts.append({
            "type": "high_cost_per_wear",
            "message": f"'{item.name}' has a high cost-per-wear of ₹{cpw}. Try wearing it more often."
        })

    return alerts


@insight_bp.route("/insights", methods=["GET"])
def get_insights():
    """
    Generate smart wardrobe and expense insights for a user.
    Query param: user_id (required)
    """
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id query parameter is required"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    items = WardrobeItem.query.filter_by(user_id=user_id).all()
    expenses = Expense.query.filter_by(user_id=user_id).all()

    # ── Wardrobe Insights ──────────────────────────────────────────────────────

    total_clothes = len(items)
    total_wardrobe_value = round(sum(i.purchase_price for i in items), 2)

    # Most worn (top 5)
    most_worn = sorted(items, key=lambda x: x.times_worn, reverse=True)[:5]

    # Least worn — exclude items with 0 wears in a separate bucket
    never_worn = [i for i in items if i.times_worn == 0]
    least_worn = sorted(
        [i for i in items if i.times_worn > 0],
        key=lambda x: x.times_worn
    )[:5]

    # Cost per wear for all items (only where times_worn > 0)
    cost_per_wear_list = [
        {
            "id": i.id,
            "name": i.name,
            "category": i.category,
            "purchase_price": i.purchase_price,
            "times_worn": i.times_worn,
            "cost_per_wear": round(i.purchase_price / i.times_worn, 2),
        }
        for i in items if i.times_worn > 0
    ]
    cost_per_wear_list.sort(key=lambda x: x["cost_per_wear"])

    avg_cost_per_wear = (
        round(sum(x["cost_per_wear"] for x in cost_per_wear_list) / len(cost_per_wear_list), 2)
        if cost_per_wear_list else None
    )

    # Category breakdown
    category_breakdown = {}
    for item in items:
        cat = item.category
        if cat not in category_breakdown:
            category_breakdown[cat] = {"count": 0, "total_value": 0}
        category_breakdown[cat]["count"] += 1
        category_breakdown[cat]["total_value"] = round(
            category_breakdown[cat]["total_value"] + item.purchase_price, 2
        )

    # ── Expense Insights ───────────────────────────────────────────────────────

    total_expenses = round(sum(e.amount for e in expenses), 2)

    expense_by_category = {}
    for exp in expenses:
        cat = exp.category
        expense_by_category[cat] = round(expense_by_category.get(cat, 0) + exp.amount, 2)

    # ── Overspending Alerts ────────────────────────────────────────────────────

    alerts = get_overspending_alerts(user_id)

    return jsonify({
        "user": user.to_dict(),
        "wardrobe": {
            "total_clothes": total_clothes,
            "total_wardrobe_value": total_wardrobe_value,
            "never_worn_count": len(never_worn),
            "never_worn_items": [i.to_dict() for i in never_worn],
            "most_worn_items": [i.to_dict() for i in most_worn],
            "least_worn_items": [i.to_dict() for i in least_worn],
            "average_cost_per_wear": avg_cost_per_wear,
            "cost_per_wear_breakdown": cost_per_wear_list,
            "category_breakdown": category_breakdown,
        },
        "expenses": {
            "total_expenses": total_expenses,
            "by_category": expense_by_category,
        },
        "alerts": alerts,
    }), 200
