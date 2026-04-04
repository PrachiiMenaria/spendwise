"""
app_chatbot_integration.py
──────────────────────────────────────────────────────────────────
HOW TO ADD THE CHATBOT TO YOUR EXISTING app.py
Just copy the 3 marked blocks into your app.py — nothing else changes.
──────────────────────────────────────────────────────────────────
"""

# ════════════════════════════════════════════════════════
# BLOCK 1 — Add this import near the top of app.py
#            (after your existing imports)
# ════════════════════════════════════════════════════════
from chatbot import chatbot_bp

# ════════════════════════════════════════════════════════
# BLOCK 2 — Register the blueprint (after app = Flask(__name__))
#            One line only:
# ════════════════════════════════════════════════════════
# app.register_blueprint(chatbot_bp)

# ════════════════════════════════════════════════════════
# BLOCK 3 — Add to your .env.example and Render/Railway
#            environment variables:
#
#   GEMINI_API_KEY=your_gemini_key_here
#
# Get a free key at: https://aistudio.google.com/app/apikey
# ════════════════════════════════════════════════════════


# ── That's it. Your new routes will be: ──
#
#   POST /chat          ← main chat endpoint (called by JS)
#   GET  /chat/status   ← health check (shows ai or fallback mode)


# ── Full working example of a minimal app.py with chatbot: ────────

import os
from flask import Flask, session, redirect, url_for
from chatbot import chatbot_bp

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

# Register chatbot
app.register_blueprint(chatbot_bp)

# ... rest of your routes (login, dashboard, wardrobe, etc.) ...

if __name__ == "__main__":
    app.run(debug=True)