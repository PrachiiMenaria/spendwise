# ✦ Fenora — Smart Living

<div align="center">

![Fenora](https://via.placeholder.com/1200x400/18182e/ffffff?text=fenora+%E2%80%94+Smart+Living)

**An AI-powered personal finance & wardrobe intelligence platform**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-black?style=for-the-badge&logo=vercel)](https://spendwise-beryl-six.vercel.app)
[![Backend](https://img.shields.io/badge/Backend-Render-purple?style=for-the-badge&logo=render)](https://spendwise-201o.onrender.com)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?style=for-the-badge&logo=github)](https://github.com/PrachiiMenaria/spendwise)

</div>

---

## 📖 About

Fenora is a robust, AI-powered financial and wardrobe tracking application designed to help users merge their budgeting analytics with their lifestyle. Driven by **Google Gemini**, Fenora analyzes your line-item expenses against your clothing wear-counts, acting as a personal stylist and financial advisor simultaneously.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🏠 **Smart Dashboard** | Beautifully animated glassmorphism UI with comprehensive financial overview |
| 👗 **Wardrobe Intelligence** | Log clothing items, track daily wears, calculate Cost-Per-Wear (CPW) |
| 🎯 **Budget Goals** | Set category limits and receive visual warnings when approaching margins |
| 🤖 **AI Co-Pilot** | Floating Gemini-powered chat that analyzes your specific logged metrics |
| 📧 **Email Analytics** | Monthly/weekly AI-generated email snapshots via Brevo |
| 📱 **Mobile Responsive** | Native React state sliders and scalable grids for iOS/Android |
| 🔐 **JWT Security** | Stateless mobile-first authentication via JSON Web Tokens |
| 🔑 **Password Reset** | Secure email-based password reset flow |

---

## 💻 Tech Stack

### Frontend
- **React 19** + Vite
- **Recharts** — Data visualizations
- **Framer Motion** — Animations
- Custom CSS Gradients & Glassmorphism

### Backend
- **Python Flask** REST API
- **PostgreSQL** + psycopg2
- **PyJWT** — JSON Web Token authentication
- **Google Gemini** (`gemini-pro`) — AI insights
- **Brevo** (`sib-api-v3-sdk`) — Email delivery

### Deployment
| Layer | Platform |
|---|---|
| Frontend | Vercel |
| Backend | Render |
| Database | Railway PostgreSQL |
| Email | Brevo (300/day free) |

---

## 🚀 Local Development Setup

### Prerequisites
- Node.js 18+ & npm
- Python 3.9+
- PostgreSQL database

### 1. Clone the Repository
```bash
git clone https://github.com/PrachiiMenaria/spendwise.git
cd spendwise
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env`:
```env
SECRET_KEY=your_super_secret_jwt_key
DATABASE_URL=postgresql://user:password@localhost:5432/fenora
GEMINI_API_KEY=your_google_gemini_key
BREVO_API_KEY=your_brevo_api_key
EMAIL_SENDER=your_verified_email@domain.com
FRONTEND_URL=http://localhost:5173
```

Start the Flask server:
```bash
flask run --port=5000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

Create `frontend/.env`:
```env
VITE_API_URL=http://localhost:5000
```

Start the Vite dev server:
```bash
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 📁 Project Structure

```
spendwise/
├── frontend/                  # React + Vite frontend
│   ├── src/
│   │   ├── pages/             # Dashboard, Expenses, Wardrobe, etc.
│   │   ├── components/        # Sidebar, Charts, Cards
│   │   ├── App.jsx            # Main app + JWT interceptor
│   │   └── main.jsx
│   ├── vercel.json
│   └── vite.config.js
│
├── backend/                   # Flask backend
│   ├── app.py                 # Main Flask app + all API routes
│   ├── email_routes.py        # Email blueprint routes
│   ├── email_service.py       # Brevo email service
│   ├── requirements.txt
│   └── Procfile
```

---

## 📱 Mobile Architecture

Fenora bypasses cross-origin third-party cookie blockers (Safari/Chrome mobile) by using a **global `window.fetch` interceptor** mounted in `App.jsx` that:

- Automatically appends `Authorization: Bearer <token>` to every API request
- Strips legacy `credentials: "include"` from all fetch calls
- Forces logout redirect on any `401` response
- Stores JWT in `localStorage` for persistence across sessions

The sidebar collapses off-canvas on screens under 768px via conditional React state rendering, replaced by a hamburger menu drawer.

---

## 🌐 Environment Variables

### Render (Backend)
| Key | Description |
|---|---|
| `DATABASE_URL` | Railway PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret |
| `GEMINI_API_KEY` | Google Gemini API key |
| `BREVO_API_KEY` | Brevo transactional email key |
| `EMAIL_SENDER` | Verified sender email |
| `FRONTEND_URL` | Vercel frontend URL |

### Vercel (Frontend)
| Key | Description |
|---|---|
| `VITE_API_URL` | Render backend URL |

---

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 👩‍💻 Developer

**Prachi Menaria**
- GitHub: [@PrachiiMenaria](https://github.com/PrachiiMenaria)

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
Made with ❤️ by Prachi Menaria
</div>
