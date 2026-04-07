from flask import Blueprint, request, jsonify
from app import db
from app.models import User

user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["POST"])
def create_user():
    """Create a new user."""
    data = request.get_json()

    required = ["name", "email", "password"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields: name, email, password"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        name=data["name"],
        email=data["email"],
        password=data["password"],  # Store hashed in production
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User created successfully", "user": user.to_dict()}), 201


@user_bp.route("/users", methods=["GET"])
def get_users():
    """Get all users."""
    users = User.query.all()
    return jsonify({"users": [u.to_dict() for u in users]}), 200
