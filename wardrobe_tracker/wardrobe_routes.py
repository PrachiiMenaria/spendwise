from datetime import datetime
from flask import Blueprint, request, jsonify
from app import db
from app.models import WardrobeItem, User

wardrobe_bp = Blueprint("wardrobe", __name__)

VALID_CATEGORIES = {"casual", "formal", "traditional", "sportswear", "ethnic", "western", "other"}


@wardrobe_bp.route("/add", methods=["POST"])
def add_wardrobe_item():
    """Add a new wardrobe item for a user."""
    data = request.get_json()

    required = ["user_id", "name", "category", "purchase_price"]
    if not all(k in data for k in required):
        return jsonify({"error": f"Missing required fields: {', '.join(required)}"}), 400

    if not User.query.get(data["user_id"]):
        return jsonify({"error": "User not found"}), 404

    category = data["category"].lower()
    if category not in VALID_CATEGORIES:
        return jsonify({
            "error": f"Invalid category. Valid options: {', '.join(VALID_CATEGORIES)}"
        }), 400

    last_worn = None
    if data.get("last_worn_date"):
        try:
            last_worn = datetime.strptime(data["last_worn_date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    item = WardrobeItem(
        user_id=data["user_id"],
        name=data["name"],
        category=category,
        purchase_price=float(data["purchase_price"]),
        times_worn=int(data.get("times_worn", 0)),
        last_worn_date=last_worn,
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({"message": "Wardrobe item added", "item": item.to_dict()}), 201


@wardrobe_bp.route("", methods=["GET"])
def get_wardrobe_items():
    """Get all wardrobe items. Filter by user_id via query param."""
    user_id = request.args.get("user_id")

    query = WardrobeItem.query
    if user_id:
        if not User.query.get(user_id):
            return jsonify({"error": "User not found"}), 404
        query = query.filter_by(user_id=user_id)

    items = query.order_by(WardrobeItem.created_at.desc()).all()
    return jsonify({
        "total": len(items),
        "items": [i.to_dict() for i in items]
    }), 200


@wardrobe_bp.route("/<int:item_id>/wear", methods=["PATCH"])
def log_wear(item_id):
    """Increment times_worn and update last_worn_date for an item."""
    item = WardrobeItem.query.get_or_404(item_id)

    item.times_worn += 1
    item.last_worn_date = datetime.utcnow().date()
    db.session.commit()

    return jsonify({"message": "Wear logged", "item": item.to_dict()}), 200


@wardrobe_bp.route("/<int:item_id>", methods=["DELETE"])
def delete_wardrobe_item(item_id):
    """Delete a wardrobe item."""
    item = WardrobeItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item deleted"}), 200
