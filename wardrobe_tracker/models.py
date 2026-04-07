from datetime import datetime
from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    wardrobe_items = db.relationship("WardrobeItem", backref="owner", lazy=True)
    expenses = db.relationship("Expense", backref="owner", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
        }


class WardrobeItem(db.Model):
    __tablename__ = "wardrobe_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # casual, formal, traditional, etc.
    purchase_price = db.Column(db.Float, nullable=False, default=0.0)
    times_worn = db.Column(db.Integer, default=0)
    last_worn_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "category": self.category,
            "purchase_price": self.purchase_price,
            "times_worn": self.times_worn,
            "last_worn_date": self.last_worn_date.isoformat() if self.last_worn_date else None,
            "cost_per_wear": round(self.purchase_price / self.times_worn, 2) if self.times_worn > 0 else None,
            "created_at": self.created_at.isoformat(),
        }


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # clothing, food, etc.
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    description = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "category": self.category,
            "date": self.date.isoformat(),
            "description": self.description,
        }
