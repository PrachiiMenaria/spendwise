# Wardrobe Utilization and Expense Tracking System

A clean Flask + PostgreSQL backend for tracking clothes usage, expenses, and generating smart insights.

---

## Folder Structure

```
wardrobe_tracker/
├── app/
│   ├── __init__.py          # App factory + SQLAlchemy init
│   ├── models.py            # User, WardrobeItem, Expense models
│   └── routes/
│       ├── __init__.py
│       ├── user_routes.py
│       ├── wardrobe_routes.py
│       ├── expense_routes.py
│       └── insight_routes.py
├── app.py                   # Entry point
├── config.py                # DB config
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure database
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

### 3. Create the database (PostgreSQL)
```sql
CREATE DATABASE wardrobe_db;
```

### 4. Run the app
```bash
python app.py
```
Tables are auto-created on first run. Or use:
```bash
flask init-db
```

---

## API Reference

### Users

#### Create User
```
POST /api/users
Body: { "name": "Rahul", "email": "rahul@example.com", "password": "secret" }
```

#### Get All Users
```
GET /api/users
```

---

### Wardrobe

#### Add Wardrobe Item
```
POST /api/wardrobe/add
Body:
{
  "user_id": 1,
  "name": "Blue Kurta",
  "category": "traditional",       # casual | formal | traditional | sportswear | ethnic | western | other
  "purchase_price": 1200,
  "times_worn": 3,                  # optional, default 0
  "last_worn_date": "2025-12-01"    # optional, YYYY-MM-DD
}
```

#### Get All Wardrobe Items
```
GET /api/wardrobe
GET /api/wardrobe?user_id=1         # filter by user
```

#### Log a Wear (increment times_worn)
```
PATCH /api/wardrobe/<item_id>/wear
```

#### Delete Item
```
DELETE /api/wardrobe/<item_id>
```

---

### Expenses

#### Add Expense
```
POST /api/expenses/add
Body:
{
  "user_id": 1,
  "amount": 2500,
  "category": "clothing",           # clothing | food | transport | entertainment | utilities | health | other
  "date": "2025-12-15",             # optional, defaults to today
  "description": "Bought jacket"    # optional
}
```

#### Get All Expenses
```
GET /api/expenses
GET /api/expenses?user_id=1
GET /api/expenses?user_id=1&category=clothing
```

#### Delete Expense
```
DELETE /api/expenses/<expense_id>
```

---

### Insights

#### Get Smart Insights
```
GET /api/insights?user_id=1
```

**Response includes:**
- `wardrobe.total_clothes` — total items owned
- `wardrobe.total_wardrobe_value` — total money spent on clothes
- `wardrobe.never_worn_items` — items with 0 wears (dead stock)
- `wardrobe.most_worn_items` — top 5 most worn items
- `wardrobe.least_worn_items` — top 5 least worn items (excluding 0)
- `wardrobe.average_cost_per_wear` — average ₹ per wear across wardrobe
- `wardrobe.cost_per_wear_breakdown` — per-item CPW sorted cheapest first
- `wardrobe.category_breakdown` — count and value per category
- `expenses.total_expenses` — total all-time spend
- `expenses.by_category` — spend per category
- `alerts[]` — overspending warnings (monthly clothing budget, dead stock, high CPW)

---

## Health Check
```
GET /health
```

---

## Sample Insights Response
```json
{
  "user": { "id": 1, "name": "Rahul", "email": "rahul@example.com" },
  "wardrobe": {
    "total_clothes": 12,
    "total_wardrobe_value": 45000.0,
    "never_worn_count": 2,
    "most_worn_items": [...],
    "least_worn_items": [...],
    "average_cost_per_wear": 180.5,
    "category_breakdown": {
      "formal": { "count": 3, "total_value": 12000 },
      "casual": { "count": 7, "total_value": 25000 }
    }
  },
  "expenses": {
    "total_expenses": 72000.0,
    "by_category": { "clothing": 45000.0, "food": 18000.0 }
  },
  "alerts": [
    {
      "type": "overspending",
      "message": "You spent ₹6500 on clothing in 2025-12, exceeding the ₹5000 threshold."
    },
    {
      "type": "dead_stock",
      "message": "You have 2 item(s) that have never been worn."
    }
  ]
}
```
