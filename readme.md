# 💸 finora — Complete Rebuild Guide

## ✅ NEW PROJECT STRUCTURE

```
Finora/
├── app.py                          ← REPLACE entirely with new version
├── requirements.txt
├── static/
│   ├── css/
│   │   └── main.css               ← REPLACE
│   └── js/
│       └── main.js                ← REPLACE
├── templates/
│   ├── base.html                  ← REPLACE
│   ├── index.html                 ← REPLACE (landing page, shown first)
│   ├── login.html                 ← REPLACE
│   ├── register.html              ← REPLACE
│   ├── dashboard.html             ← REPLACE
│   ├── expense_list.html          ← REPLACE
│   ├── expense_add.html           ← REPLACE
│   ├── analytics.html             ← REPLACE
│   ├── budget.html                ← REPLACE
│   └── admin.html                 ← keep existing (or minimal)
└── ml_spending_alert/             ← KEEP AS IS (your models)
    ├── pipeline.py
    ├── alert_engine.py
    ├── reminder_engine.py
    ├── ml_spending.py
    └── saved_model.pkl / saved_scaler.pkl
```

---

## 🗑️ FILES TO DELETE (from your wardrobe-analysis-project)

These are wardrobe-specific files that are NOT needed in ExpenseWise:

### Templates to DELETE:
- `templates/wardrobe.html`
- `templates/wardrobe_add.html`
- `templates/wardrobe_edit.html`
- `templates/cpw.html`
- `templates/spending_alert.html` (wardrobe-specific)
- `templates/result.html`
- `templates/decision.html`
- `templates/predict.html`
- `templates/survey.html`
- `templates/chat.html`
- `templates/nav_update.html`

### CSS to DELETE:
- `static/css/dashboard.css`      (replaced by main.css)
- `static/css/decision.css`
- `static/css/index.css`
- `static/css/register.css`
- `static/css/spending_alert.css`
- `static/css/style.css`

### Python files to DELETE or ARCHIVE:
- `dashboard_routes.py`           (routes are now all in app.py)
- `App_chatbot_integration.py`    (not needed for ExpenseWise)
- `chatbot.py`                    (remove if not using chat)
- `test_db.py`                    (dev only, don't ship)

### wardrobe_ml_system/ — KEEP but don't import in app.py
(Your new app.py no longer imports wardrobe ML, only ml_spending_alert)

---

## 🔧 ALL ROUTING FIXES

| Old (broken)              | New (fixed)              |
|---------------------------|--------------------------|
| `url_for('budget_view')`  | ✅ `budget_view` works   |
| `url_for('expenses_view')`| ✅ renamed to `expense_list` |
| `url_for('expenses_list')`| ✅ `expense_list`        |
| `url_for('analytics')`    | ✅ `analytics_page`      |
| Login shown first         | ✅ `/` → index.html      |

---

## 🎨 AI IMAGE PROMPTS (use Midjourney/DALL-E/Stable Diffusion)

### Landing Page Hero:
```
minimal aesthetic finance dashboard background, soft gradient of dusty rose 
and warm gold, glassmorphism UI cards floating, cinematic lighting, 
soft bokeh, financial storytelling theme, premium lifestyle feel, 
pastel tones, clean modern composition, 16:9
```

### Dashboard Background (subtle):
```
abstract watercolor texture in ivory and warm gold tones, 
very light and minimal, suitable as web dashboard background, 
soft geometric shapes, premium finance app aesthetic
```

### Feature Section Illustrations:
```
isometric financial charts and graphs illustration, 
warm rose gold and cream color palette, minimal flat design, 
clean white background, modern fintech aesthetic
```

### Analytics Page:
```
data visualization aesthetic background, flowing abstract lines 
in gold and blush pink, soft gradient, modern dashboard feel, 
professional yet warm, cinematic quality
```

---

## 🎨 DESIGN SYSTEM

### Color Palette (from your reference image):
| Name            | Hex      | Usage                      |
|-----------------|----------|----------------------------|
| Lunar Lander    | #DBCEA0  | Gold light, cards, accents |
| Nonpareil Apple | #C4A659  | Primary gold, CTA buttons  |
| Fallen Blossoms | #EEB4C3  | Pink light, metric cards   |
| Taffeta Darling | #AF7B82  | Pink, category badges      |
| Autumn Leaves   | #6E423E  | Dark rose, headings, nav   |
| Off-White       | #FAF8F3  | Background, base           |

### Typography:
- **Display**: Cormorant Garamond (headings, brand, numbers)
- **Body**: DM Sans (UI text, labels, buttons)

---

## 🔧 TEMPLATE DATA — GUARANTEED NON-NULL

### dashboard.html receives:
```python
analytics     = { budget, total_spent, remaining, pct_used, mom_delta, 
                  mom_pct, category_breakdown, trend_labels, trend_values }
data          = { labels, values, cat_labels, cat_values, budget, total_spent }
data_json     = json.dumps(data)            # ✅ never undefined
recommendations = [...]
health_score  = int (0-100)
health_label  = str
health_color  = hex color str
```

### analytics.html receives:
```python
analytics_data = { monthly, categories, risk_signals, avg_monthly, peak_month }
analytics_json = json.dumps(analytics_data)  # ✅ never undefined
month_names    = ["Jan","Feb",...,"Dec"]      # ✅ always set
month          = int
year           = int
```

### expense_list.html receives:
```python
summary       = get_expense_summary(...)     # ✅ dict, never None
summary_json  = json.dumps(summary)          # ✅ for JS charts
expenses      = [...]
month_options = [...]
```

---

## 🚀 HOW TO RUN

```bash
# 1. Install dependencies
pip install flask psycopg2-binary werkzeug

# 2. Set environment variables (or use .env)
export DB_HOST=localhost
export DB_NAME=expensewise_db
export DB_USER=postgres
export DB_PASSWORD=yourpassword
export SECRET_KEY=your_secret_key

# 3. Run
python app.py
```

Then visit: http://localhost:5000 → Landing Page (no login forced!)