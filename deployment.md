# fenora — Deployment Guide

## Files Delivered This Session
| File | Where to put it |
|------|-----------------|
| `Dashboard.jsx` | `frontend/src/pages/Dashboard.jsx` |
| `Wardrobe.jsx` | `frontend/src/pages/Wardrobe.jsx` |
| `production_routes.py` | Paste contents into `backend/app.py` before `from email_routes import email_bp` |
| `requirements.txt` | `backend/requirements.txt` |
| `Procfile` | `backend/Procfile` |
| `.env.example` | `backend/.env.example` (copy to `.env` and fill in values) |
| `vite.config.js` | `frontend/vite.config.js` |

---

## Step 1 — SQL Migrations (run once in your DB)

```sql
-- Add mood column to expenses (if not already done)
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS mood VARCHAR(20) DEFAULT NULL;

-- Email settings columns (if not already done)
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS email_reminders_enabled BOOLEAN DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS email_frequency VARCHAR(10) DEFAULT 'monthly';

-- Savings goals (if not already done)
CREATE TABLE IF NOT EXISTS savings_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    name VARCHAR(200) NOT NULL,
    target_amount NUMERIC(12,2) NOT NULL,
    saved_amount NUMERIC(12,2) DEFAULT 0,
    months INTEGER DEFAULT 6,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Step 2 — Backend: Paste production_routes.py

Open `backend/app.py`, find the line:
```python
from email_routes import email_bp
```
Paste the entire contents of `production_routes.py` immediately ABOVE that line.

---

## Step 3 — Local Testing

```bash
cd backend
pip install -r requirements.txt
python app.py
```

```bash
cd frontend
npm install
npm run dev
```

---

## Step 4 — Deploy Backend on Render

1. Go to [render.com](https://render.com) → New → Web Service
2. Connect your GitHub repo
3. Set **Root Directory**: `backend`
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
6. Add Environment Variables:
   ```
   SECRET_KEY=<generate a long random string>
   DATABASE_URL=<your render postgres URL>
   EMAIL_SENDER=your@gmail.com
   EMAIL_PASSWORD=your_app_password
   FRONTEND_URL=https://your-app.vercel.app
   FLASK_DEBUG=false
   ```
7. Add a **PostgreSQL** database service → Render auto-sets `DATABASE_URL`

---

## Step 5 — Deploy Frontend on Vercel

1. Go to [vercel.com](https://vercel.com) → New Project
2. Import your GitHub repo
3. Set **Root Directory**: `frontend`
4. Set **Framework**: Vite
5. Add Environment Variable:
   ```
   VITE_API_URL=https://your-backend.onrender.com
   ```
6. Deploy

---

## Step 6 — Update CORS on Backend

After getting your Vercel URL, update `app.py` CORS origins:
```python
CORS(app,
     supports_credentials=True,
     origins=[
         "http://localhost:5173",
         "https://your-app.vercel.app",    # ← add this
         "https://your-custom-domain.com", # ← if you have one
     ],
     ...
)
```

---

## What Was Fixed

### 1. Editable Budget
- `EditBudgetWidget` component in Dashboard — click "✏️ Edit Budget" next to "Budget vs Actual"
- Calls `POST /api/update-budget` and refreshes summary
- New alias: `PUT /api/budget/update`

### 2. Full Spending Calendar
- `SpendingCalendar` component — shows complete month grid
- Month navigation (prev/next)
- Colored cells by spend intensity (4 shades)
- Hover tooltip showing exact amount
- Calls `GET /api/expenses/calendar?year=&month=`

### 3. AI Chat (real answers)
- `SmartChat` component replaces 3 static buttons with a full chat interface
- Free-text input + quick prompts
- Calls `/api/smart-chat` with `{ message: "..." }`
- Falls back to `/api/chat` if needed
- Context bar shows budget/spent/remaining

### 4. Savings Goals with Calculations
- Shows monthly_saving_needed + daily_saving_needed per goal
- Calls `/api/savings-goals/calculated` (with fallback to `/api/savings-goals`)

### 5. Mood in Expenses
- Already added in previous session (Expenses.jsx)
- 5 mood buttons: 😊 😑 😤 😔 🤩

### 6. Wardrobe Edit
- ✏️ button on each wardrobe card opens `EditModal`
- Calls `PUT /api/wardrobe/<id>`
- Full form: name, price, category, color

### 7. Email
- `api_test_email_direct` tries `EMAIL_SENDER`/`EMAIL_PASSWORD` env vars
- Uses SMTP port 587 + STARTTLS (more compatible than 465)
- Detailed error messages with fix hints

### 8. Deployment
- `requirements.txt` with all deps
- `Procfile` for gunicorn
- `vite.config.js` with API proxy + `VITE_API_URL` env var support
- All API calls use `import.meta.env.VITE_API_URL || "http://localhost:5000"`

---

## Testing Checklist

- [ ] Login works, session persists across pages
- [ ] Budget edit saves and refreshes dashboard
- [ ] Calendar shows colored days for dates with expenses
- [ ] AI chat: "Can I afford ₹2000?" returns a real calculated answer
- [ ] Wardrobe edit modal opens and saves
- [ ] Goals show daily/monthly saving amounts
- [ ] Test email sends (check spam folder)
- [ ] `npm run build` completes without errors