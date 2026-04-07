"""
chatbot.py — WardrobeIQ AI Chatbot
────────────────────────────────────
Drop this file into your project root.
Import and register the blueprint in app.py.

Requirements:
  pip install google-generativeai

Environment variable needed:
  GEMINI_API_KEY=your_key_here
  Get key free at: https://aistudio.google.com/app/apikey
"""

import os
import json
import logging
from flask import Blueprint, request, jsonify, session
import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

# ── Blueprint ──────────────────────────────────────────────────────
chatbot_bp = Blueprint("chatbot", __name__)

# ── Gemini setup ───────────────────────────────────────────────────
_gemini_model = None

def get_gemini():
    """Lazy-load Gemini model. Returns None if key not set."""
    global _gemini_model
    if _gemini_model is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set — chatbot will use fallback mode.")
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            logger.info("Gemini model loaded.")
        except Exception as e:
            logger.error(f"Gemini load failed: {e}")
    return _gemini_model


# ── DB helper (reuse your existing get_db or paste your own) ───────
def get_db():
    return psycopg2.connect(
        host     = os.getenv("DB_HOST",     "localhost"),
        database = os.getenv("DB_NAME",     "wardrobe_db"),
        user     = os.getenv("DB_USER",     "postgres"),
        password = os.getenv("DB_PASSWORD", "wardrobe123"),
        port     = os.getenv("DB_PORT",     "5432"),
    )


# ── Fetch user context for the system prompt ───────────────────────
def get_user_context(user_id: int) -> dict:
    """
    Pull the data WardrobeIQ AI needs from the database.
    Returns a dict with all placeholder values.
    """
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Budget from latest survey
    cur.execute(
        "SELECT monthly_budget FROM survey_responses "
        "WHERE user_id=%s ORDER BY created_at DESC LIMIT 1", (user_id,)
    )
    sv = cur.fetchone()
    budget = float(sv["monthly_budget"]) if sv else 0.0

    # Total spending from wardrobe items
    cur.execute(
        "SELECT COALESCE(SUM(purchase_price),0) AS t FROM wardrobe_items WHERE user_id=%s",
        (user_id,)
    )
    spending = float(cur.fetchone()["t"])

    # WUI
    cur.execute(
        "SELECT COALESCE(SUM(wear_count),0) AS tw, COUNT(*) AS tc "
        "FROM wardrobe_items WHERE user_id=%s", (user_id,)
    )
    r  = cur.fetchone()
    tw, tc = float(r["tw"]), max(float(r["tc"]), 1)
    wui = round(tw / tc, 2)

    # High CPW categories (avg CPW > 200)
    cur.execute("""
        SELECT category,
               ROUND(AVG(CASE WHEN wear_count>0 THEN purchase_price/wear_count
                         ELSE purchase_price END)::numeric,0) AS avg_cpw
        FROM wardrobe_items WHERE user_id=%s
        GROUP BY category HAVING
               AVG(CASE WHEN wear_count>0 THEN purchase_price/wear_count
                        ELSE purchase_price END) > 200
        ORDER BY avg_cpw DESC LIMIT 3
    """, (user_id,))
    high_cpw_rows = cur.fetchall()
    high_cpw = ", ".join(
        f"{r['category']} (₹{r['avg_cpw']:.0f}/wear)" for r in high_cpw_rows
    ) or "none flagged"

    # Latest ML prediction
    cur.execute(
        "SELECT predicted_spending, risk_category, budget_ratio "
        "FROM ml_predictions WHERE user_id=%s ORDER BY predicted_at DESC LIMIT 1",
        (user_id,)
    )
    pred_row = cur.fetchone()
    prediction = f"₹{pred_row['predicted_spending']:,.0f}" if pred_row else "not run yet"
    risk       = pred_row["risk_category"] if pred_row else "unknown"

    # Purchase pattern (gap-based)
    cur.execute(
        "SELECT created_at::date AS d FROM wardrobe_items "
        "WHERE user_id=%s ORDER BY created_at ASC", (user_id,)
    )
    dates = [row["d"] for row in cur.fetchall()]
    if len(dates) >= 2:
        gaps    = [(dates[i+1]-dates[i]).days for i in range(len(dates)-1)]
        avg_gap = sum(gaps) / len(gaps)
        if avg_gap < 10:
            pattern = "frequent"
        elif avg_gap <= 30:
            pattern = "moderate"
        else:
            pattern = "occasional"
    else:
        pattern = "not enough data"

    cur.close(); conn.close()

    return dict(
        budget     = f"₹{budget:,.0f}" if budget > 0 else "not set",
        spending   = f"₹{spending:,.0f}",
        wui        = wui,
        high_cpw   = high_cpw,
        pattern    = pattern,
        prediction = prediction,
        risk       = risk,
    )


# ── Build the system prompt ────────────────────────────────────────
SYSTEM_PROMPT_TEMPLATE = """
You are WardrobeIQ AI — a smart, human-like wardrobe and spending advisor.

Your personality:
- Talk like a helpful, intelligent human (not robotic)
- Be conversational, natural, and slightly friendly
- Keep responses concise but insightful — 2 to 4 short paragraphs max
- Do NOT sound like a generic AI assistant
- Avoid repeating numbers blindly — interpret what they mean
- Never say "based on the data provided" or "as an AI"
- Sound like a smart friend who understands both money and fashion

Your role:
You help users understand their wardrobe, spending habits, and behavior.
You analyze Cost Per Wear (CPW), Wardrobe Utilization Index (WUI),
spending vs budget, purchase patterns, and ML-based predictions.
You do NOT just show data — you EXPLAIN what it means in plain English.

USER'S CURRENT DATA:
- Monthly Budget: {budget}
- Total Wardrobe Spending: {spending}
- Wardrobe Utilization Index (WUI): {wui}  (scale: low<2, moderate 2-5, excellent>5)
- High CPW Categories: {high_cpw}
- Purchase Pattern: {pattern}  (frequent = every <10 days, occasional = >30 days)
- Last ML Prediction: {prediction}
- Current Risk Level: {risk}

HOW TO RESPOND:
1. Understand the user's intent — even if vague or emotional
2. Translate numbers into meaning (do NOT recite them robotically)
3. Give one or two specific, actionable suggestions
4. Keep tone: insightful, slightly conversational, never preachy

INTERPRETATION GUIDE:
- WUI < 2.0  → wardrobe underused; buying more items won't help
- WUI > 5.0  → great utilization; efficient wardrobe
- High CPW   → items bought but rarely worn; spending not translating to use
- Risk = High Risk → predicted to exceed budget; needs immediate action
- Frequent pattern → impulse buying risk; clustering purchases
- Occasional pattern → infrequent but can spike; needs planning

EXAMPLES OF GOOD RESPONSES:
Q: "Am I overspending?"
A: "You're close to your limit — the bigger issue is your wardrobe isn't getting much use. 
    Buying more right now won't solve the feeling of having 'nothing to wear.'"

Q: "Why is my CPW high?"
A: "Some of your most expensive categories are barely being worn. 
    That's your money sitting in your closet instead of working for you."

Q: "Should I buy a new jacket?"
A: "Honestly? Check your wardrobe first. Your utilization score suggests you probably 
    have items you haven't fully explored yet. Wear what you own for 2-3 weeks, 
    then revisit the decision."

Now respond to the user's message naturally. Keep it under 150 words.
""".strip()


def build_system_prompt(ctx: dict) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(**ctx)


# ── Fallback responses when Gemini is not available ───────────────
FALLBACK_RESPONSES = [
    "Your WUI suggests your wardrobe isn't being used as much as it could be. "
    "Before thinking about new purchases, try wearing your least-used items for a week.",

    "Looking at your patterns, the issue isn't how much you spend — it's how little "
    "you use what you already own. That's where the real value is hiding.",

    "Your spending is {ratio}% of your budget. {advice}",

    "I'd suggest running a quick Spending Analysis first — it gives a much clearer "
    "picture of what's happening with your wardrobe finances.",
]

def fallback_response(ctx: dict, user_msg: str) -> str:
    """Simple rule-based fallback when Gemini API is unavailable."""
    msg = user_msg.lower()

    if any(w in msg for w in ["overspend", "budget", "spend too much", "money"]):
        if ctx.get("risk") == "High Risk":
            return ("Your predicted spending is flagged as High Risk — you're likely heading "
                    "over budget. The quickest fix is to pause purchases this week and check "
                    "which items in your wardrobe you haven't worn yet.")
        return ("Your spending looks manageable, but your wardrobe utilization could be better. "
                "Getting more wear out of what you own is the fastest way to improve your "
                "cost-per-wear across the board.")

    if any(w in msg for w in ["cpw", "cost per wear", "expensive", "waste"]):
        cpw = ctx.get("high_cpw", "none flagged")
        if cpw != "none flagged":
            return (f"Your highest CPW is in: {cpw}. "
                    "These items are costing you the most per use — either start wearing "
                    "them more regularly or reconsider adding to those categories.")
        return ("Your cost-per-wear looks reasonable right now. "
                "Keep logging your wears to keep the data accurate.")

    if any(w in msg for w in ["wui", "utilization", "not wearing", "closet", "wardrobe"]):
        wui = ctx.get("wui", 0)
        if float(wui) < 2.0:
            return (f"Your WUI of {wui} tells me your wardrobe is underused — most items are "
                    "sitting unworn. Before buying anything new, challenge yourself to wear "
                    "something different every day for a week.")
        return (f"Your WUI of {wui} is decent. You're making reasonable use of your clothes. "
                "Focus on the categories with high CPW to squeeze more value out of your wardrobe.")

    if any(w in msg for w in ["buy", "purchase", "shop", "should i"]):
        return ("Before buying anything new, check your wardrobe utilization. "
                "If your WUI is below 3, you likely have unworn items that could fill "
                "the gap — buying more would just add to the clutter.")

    return ("Good question! Run a Spending Analysis from the dashboard for a full picture. "
            "Once you have a prediction and risk level, I can give you much more specific advice.")


# ── Main chat route ────────────────────────────────────────────────
@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    """
    POST /chat
    Body: { "message": "user message" }
    Session must have user_id set (user must be logged in).
    Returns: { "reply": "...", "mode": "ai" | "fallback" }
    """
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data     = request.get_json(silent=True) or {}
    user_msg = (data.get("message") or "").strip()

    if not user_msg:
        return jsonify({"error": "Empty message"}), 400
    if len(user_msg) > 500:
        return jsonify({"error": "Message too long (max 500 chars)"}), 400

    user_id = session["user_id"]

    # ── Fetch user context ─────────────────────────────────────────
    try:
        ctx = get_user_context(user_id)
    except Exception as e:
        logger.error(f"Context fetch failed: {e}")
        ctx = {
            "budget": "not set", "spending": "unknown", "wui": "0",
            "high_cpw": "unknown", "pattern": "unknown",
            "prediction": "not run yet", "risk": "unknown"
        }

    # ── Try Gemini ─────────────────────────────────────────────────
    gemini = get_gemini()
    if gemini:
        try:
            system_prompt = build_system_prompt(ctx)
            full_prompt   = f"{system_prompt}\n\nUser: {user_msg}\n\nWardrobeIQ AI:"
            response      = gemini.generate_content(full_prompt)
            reply         = response.text.strip()

            # Safety: strip any "based on the data" phrases
            for phrase in ["Based on the data provided,", "As an AI,", "Based on your data,"]:
                reply = reply.replace(phrase, "").strip()

            return jsonify({"reply": reply, "mode": "ai"})

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            # Fall through to fallback

    # ── Fallback ───────────────────────────────────────────────────
    reply = fallback_response(ctx, user_msg)
    return jsonify({"reply": reply, "mode": "fallback"})


# ── Health check for chatbot ───────────────────────────────────────
@chatbot_bp.route("/chat/status", methods=["GET"])
def chat_status():
    gemini_ready = get_gemini() is not None
    return jsonify({
        "gemini_configured": gemini_ready,
        "mode": "ai" if gemini_ready else "fallback",
        "message": "AI chatbot ready." if gemini_ready else
                   "Running in fallback mode. Set GEMINI_API_KEY to enable full AI."
    })


# ── Page route (renders chat.html template) ────────────────────────
@chatbot_bp.route("/chat-page")
def chat_page():
    """Renders the chat interface page."""
    from flask import render_template, redirect, url_for
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("chat.html")