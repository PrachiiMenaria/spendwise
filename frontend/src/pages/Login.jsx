// fenora/frontend/src/pages/Login.jsx — UPGRADED
import { useState } from "react";

const API = "http://localhost:5000";

export default function Login({ onLogin, onBack }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "", budget: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showPass, setShowPass] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setError(null);
    const endpoint = mode === "login" ? "/api/login" : "/api/register";
    try {
      const res = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name: form.name, email: form.email,
          password: form.password,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Something went wrong");
      const userObj = data.user || { id: data.user_id, name: data.name || form.name };
      onLogin({ user_id: userObj.id, name: userObj.name || form.name, budget: data.budget || null });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh", display: "flex",
      fontFamily: "'Outfit', sans-serif",
      background: "#f5f3fc",
    }}>
      {/* ── Left panel ── */}
      <div className="login-left" style={{
        flex: "0 0 44%",
        background: "linear-gradient(155deg, #6b5fa0 0%, #5a4f8c 40%, #4a3f78 100%)",
        padding: "56px 52px",
        display: "flex", flexDirection: "column", justifyContent: "center",
        position: "relative", overflow: "hidden",
      }}>
        {/* Decorative circles */}
        <div style={{ position: "absolute", top: -80, right: -80, width: 320, height: 320, borderRadius: "50%", background: "rgba(255,255,255,0.05)" }} />
        <div style={{ position: "absolute", bottom: -70, left: -70, width: 240, height: 240, borderRadius: "50%", background: "rgba(255,255,255,0.04)" }} />
        <div style={{ position: "absolute", top: "50%", right: 40, width: 100, height: 100, borderRadius: "50%", background: "rgba(201,169,110,0.15)" }} />

        <div style={{ position: "relative", zIndex: 1 }}>
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 48 }}>
            <div style={{ width: 36, height: 36, borderRadius: 11, background: "rgba(255,255,255,0.15)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, color: "#fff", border: "1px solid rgba(255,255,255,0.2)" }}>✦</div>
            <span style={{ fontSize: 22, fontWeight: 900, color: "#fff", letterSpacing: "-0.5px" }}>fenora<span style={{ color: "#c9a96e" }}>.</span></span>
          </div>

          <h2 style={{ fontSize: "clamp(28px, 3.5vw, 42px)", fontWeight: 900, color: "#fff", lineHeight: 1.15, letterSpacing: "-1px", margin: "0 0 16px" }}>
            Money in control.<br />
            <span style={{ fontFamily: "'Playfair Display', serif", fontStyle: "italic", color: "#c9a96e" }}>Life on glow.</span>
          </h2>

          <p style={{ color: "rgba(255,255,255,0.72)", fontSize: 14, lineHeight: 1.75, maxWidth: 340, marginBottom: 40 }}>
            Your intelligent budget & wardrobe companion for Gen Z students in India. Track smarter, live freer.
          </p>

          {/* Feature pills */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 48 }}>
            {["📊 Smart Charts", "🤖 AI Insights", "👗 Wardrobe IQ", "📧 Monthly Reports"].map((f) => (
              <div key={f} style={{
                background: "rgba(255,255,255,0.12)", backdropFilter: "blur(8px)",
                padding: "7px 14px", borderRadius: 100, fontSize: 11,
                color: "#fff", fontWeight: 600, border: "1px solid rgba(255,255,255,0.18)",
              }}>{f}</div>
            ))}
          </div>

          {/* Testimonial */}
          <div style={{ background: "rgba(255,255,255,0.08)", backdropFilter: "blur(12px)", borderRadius: 18, padding: "20px 22px", border: "1px solid rgba(255,255,255,0.12)" }}>
            <p style={{ color: "rgba(255,255,255,0.88)", fontSize: 13, lineHeight: 1.65, margin: "0 0 12px", fontStyle: "italic" }}>
              "Fenora helped me save ₹3,000 last month just by showing me what I was spending on Swiggy!"
            </p>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.55)", fontWeight: 600 }}>— Priya, BITS Pilani</div>
          </div>
        </div>
      </div>

      {/* ── Right panel ── */}
      <div style={{
        flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
        padding: "40px 24px",
      }}>
        <div style={{ width: "100%", maxWidth: 420 }}>
          {/* Back button */}
          {onBack && (
            <button onClick={onBack} style={{
              background: "none", border: "none", cursor: "pointer",
              fontSize: 13, color: "#9898b8", fontFamily: "inherit",
              display: "flex", alignItems: "center", gap: 6, marginBottom: 28,
              padding: 0, transition: "color 0.15s",
            }}
              onMouseEnter={e => e.currentTarget.style.color = "#6b5fa0"}
              onMouseLeave={e => e.currentTarget.style.color = "#9898b8"}
            >
              ← Back to home
            </button>
          )}

          {/* Mode toggle */}
          <div style={{ background: "#f0eef8", borderRadius: 14, padding: 4, display: "flex", marginBottom: 28 }}>
            {["login", "register"].map(m => (
              <button key={m} onClick={() => { setMode(m); setError(null); }} style={{
                flex: 1, padding: "9px 16px", borderRadius: 11, fontSize: 13, fontWeight: 700,
                background: mode === m ? "#fff" : "transparent",
                color: mode === m ? "#6b5fa0" : "#9898b8",
                border: "none", cursor: "pointer", fontFamily: "inherit",
                boxShadow: mode === m ? "0 2px 8px rgba(107,95,160,0.12)" : "none",
                transition: "all 0.18s",
              }}>
                {m === "login" ? "Sign In" : "Sign Up"}
              </button>
            ))}
          </div>

          {/* Card */}
          <div style={{
            background: "#fff", borderRadius: 24, padding: "36px 36px",
            boxShadow: "0 8px 48px rgba(107,95,160,0.12)",
            border: "1px solid rgba(107,95,160,0.08)",
          }}>
            <h2 style={{ fontSize: 24, fontWeight: 800, color: "#18182e", margin: "0 0 6px", letterSpacing: "-0.5px" }}>
              {mode === "login" ? "Welcome back 👋" : "Create account 🚀"}
            </h2>
            <p style={{ fontSize: 13, color: "#9898b8", marginBottom: 28 }}>
              {mode === "login" ? "Sign in to your fenora account" : "Start tracking smarter — it's free"}
            </p>

            {error && (
              <div style={{ background: "#fff8f8", border: "1px solid #fad5d5", borderRadius: 12, padding: "12px 16px", display: "flex", gap: 10, alignItems: "center", marginBottom: 20 }}>
                <span>⚠️</span>
                <span style={{ fontSize: 13, color: "#d96b6b" }}>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {mode === "register" && (
                <div>
                  <label style={labelStyle}>Your Name</label>
                  <input style={inputStyle} name="name" placeholder="e.g. Prachi" value={form.name}
                    onChange={e => setForm({ ...form, name: e.target.value })} required />
                </div>
              )}
              <div>
                <label style={labelStyle}>Email Address</label>
                <input style={inputStyle} type="email" name="email" placeholder="you@example.com" value={form.email}
                  onChange={e => setForm({ ...form, email: e.target.value })} required />
              </div>
              <div>
                <label style={labelStyle}>Password</label>
                <div style={{ position: "relative" }}>
                  <input style={{ ...inputStyle, paddingRight: 44 }} type={showPass ? "text" : "password"}
                    placeholder="••••••••" value={form.password}
                    onChange={e => setForm({ ...form, password: e.target.value })} required />
                  <button type="button" onClick={() => setShowPass(!showPass)} style={{
                    position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)",
                    background: "none", border: "none", cursor: "pointer", fontSize: 15, color: "#9898b8",
                  }}>
                    {showPass ? "🙈" : "👁️"}
                  </button>
                </div>
                {mode === "login" && (
                  <div style={{ textAlign: "right", marginTop: 6 }}>
                    <a href="/forgot-password" onClick={(e) => { e.preventDefault(); window.location.href = '/forgot-password'; }} style={{ fontSize: 11, color: "#6b5fa0", textDecoration: "none", fontWeight: 600 }}>Forgot Password?</a>
                  </div>
                )}
              </div>
              <button type="submit" disabled={loading} style={{
                background: loading ? "#b0aec8" : "linear-gradient(135deg, #6b5fa0, #9b8ec8)",
                color: "#fff", border: "none", borderRadius: 14, padding: "14px",
                fontSize: 14, fontWeight: 800, cursor: loading ? "not-allowed" : "pointer",
                fontFamily: "inherit", marginTop: 4,
                boxShadow: loading ? "none" : "0 4px 20px rgba(107,95,160,0.38)",
                transition: "all 0.22s", letterSpacing: "0.2px",
              }}
                onMouseEnter={e => { if (!loading) e.currentTarget.style.transform = "translateY(-1px)"; }}
                onMouseLeave={e => e.currentTarget.style.transform = "translateY(0)"}
              >
                {loading ? (
                  <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
                    <span style={{ width: 16, height: 16, borderRadius: "50%", border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "#fff", animation: "spin 0.8s linear infinite", display: "inline-block" }} />
                    Please wait…
                  </span>
                ) : (
                  mode === "login" ? "Sign In →" : "Create Account →"
                )}
              </button>
            </form>
          </div>

          <p style={{ textAlign: "center", fontSize: 11, color: "#b0aec8", marginTop: 20 }}>
            🔒 Your data is private and never shared
          </p>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Playfair+Display:ital,wght@1,700&display=swap');
        @keyframes spin { to { transform: rotate(360deg); } }
        @media (max-width: 768px) { .login-left { display: none !important; } }
      `}</style>
    </div>
  );
}

const labelStyle = {
  display: "block", fontSize: 11, fontWeight: 700, color: "#9898b8",
  textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 8,
};
const inputStyle = {
  width: "100%", padding: "12px 16px", borderRadius: 12,
  border: "1.5px solid #ebe8f5", fontSize: 13, color: "#18182e",
  background: "#faf9ff", outline: "none", fontFamily: "inherit",
  boxSizing: "border-box", transition: "border 0.18s, box-shadow 0.18s",
};