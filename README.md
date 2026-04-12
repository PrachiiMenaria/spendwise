# ✦ Fenora (Spendwise)

![Fenora Banner](https://via.placeholder.com/1200x400/18182e/ffffff?text=fenora+%E2%80%94+Smart+Living)

Fenora is a robust, AI-powered financial and wardrobe tracking application designed to help users merge their budgeting analytics with their lifestyle. Driven by Google Gemini, Fenora analyzes your line-item expenses against your clothing wear-counts, acting as a personal stylist and financial advisor simultaneously.

## ✨ Features

- **Smart Dashboard:** A beautifully animated, glassmorphism-inspired UI detailing your comprehensive financial standing.
- **Wardrobe Intelligence:** Log clothing items, track your daily "wears", and automatically calculate your true Cost-Per-Wear (CPW) over time to visualize ROI.
- **Goal Checkpoints:** Set rigid limits for categories and receive visual UI warnings when bridging margins.
- **AI Co-Pilot:** A floating chat interface powered by Google Gemini that analyzes *your specific logged metrics* to answer conversational questions about your habits.
- **Automated Email Analytics:** Opt-in to monthly/weekly AI-generated layout emails delivering recommendations via Brevo transactionals.
- **True Mobile Responsiveness:** Built natively with React state sliders and scalable grids ensuring a 1:1 application feel on iOS/Android devices.
- **Stateless JWT Security:** Mobile-first secure authentication via JSON Web Tokens for lightning-fast cross-origin validations.

## 💻 Tech Stack

**Frontend:**
- React 19 (Vite)
- Recharts (Data Visualizations)
- Framer Motion
- Custom CSS Gradients & Glassmorphism architecture

**Backend:**
- Python Flask REST API
- PostgreSQL / psycopg2
- JSON Web Tokens (PyJWT) Auth
- Google Generative AI (`gemini-pro`)
- Brevo (`sib-api-v3-sdk`) Email Delivery

**Deployment Architecture:**
- Vercel (Frontend)
- Render (Backend App)
- Supabase / Neon (Database)

## 🚀 Local Development Setup

### Prerequisites
- Node.js & npm
- Python 3.9+
- PostgreSQL Database

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/spendwise.git
cd spendwise
```

### 2. Backend Configuration
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:
```env
# Server & DB Config
SECRET_KEY=your_super_secret_jwt_key
DATABASE_URL=postgresql://user:password@localhost:5432/fenora

# APIs
GEMINI_API_KEY=your_google_gemini_key
BREVO_API_KEY=your_brevo_api_key

# Email Sandbox (For automated test routes)
EMAIL_SENDER=your_verified_email@domain.com
```

Start the Flask server:
```bash
flask run --port=5000
```

### 3. Frontend Configuration
```bash
cd frontend
npm install
```

Create a `.env` file in the `frontend/` directory:
```env
VITE_API_URL=http://localhost:5000
```

Start the Vite development server:
```bash
npm run dev
```

## 📱 Mobile Architecture
Fenora bypasses rigid cross-origin third-party Safari/Chrome session blockers by utilizing a local-storage `Bearer` interceptor hook mounted directly to the `window.fetch` layer inside `App.jsx`. Additionally, the CSS layout collapses dynamically under `768px` via conditional state rendering, pulling the Sidebar component entirely off-canvas.

## 🤝 Contributing
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
