// fenora/frontend/src/pages/Login.jsx
import { useState } from "react";

const API = "http://localhost:5000";

export default function Login({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "", budget: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showPass, setShowPass] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const endpoint = mode === "login" ? "/api/login" : "/api/register";
    try {
      const res = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name: form.name,
          email: form.email,
          password: form.password,
          monthly_budget: parseFloat(form.budget) || 10000,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Something went wrong");
      const userObj = data.user || { id: data.user_id, name: data.name || form.name };
      onLogin({ user_id: userObj.id, name: userObj.name || form.name, budget: data.budget || parseFloat(form.budget) || 10000 });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  return (
    <div style={{
      minHeight: "100vh", display: "flex",
      fontFamily: "'DM Sans', sans-serif",
      background: "#f8f6ff",
    }}>
      {/* Left Panel */}
      <div style={{
        flex: "1 1 45%", display: "none",
        background: "linear-gradient(135deg, #7c6fa0 0%, #5a5080 100%)",
        padding: "60px 48px", flexDirection: "column", justifyContent: "center",
        position: "relative", overflow: "hidden",
        ...(window.innerWidth > 768 ? { display: "flex" } : {}),
      }}>
        {/* Decorative circles */}
        <div style={{ position: "absolute", top: -80, right: -80, width: 300, height: 300, borderRadius: "50%", background: "rgba(255,255,255,0.06)" }} />
        <div style={{ position: "absolute", bottom: -60, left: -60, width: 200, height: 200, borderRadius: "50%", background: "rgba(255,255,255,0.04)" }} />
        <div style={{ position: "absolute", bottom: 120, right: 40, width: 120, height: 120, borderRadius: "50%", background: "rgba(255,255,255,0.06)" }} />

        <div style={{ position: "relative", zIndex: 1 }}>
          <div style={{ fontSize: 36, fontWeight: 900, color: "#fff", letterSpacing: "-1px", marginBottom: 8 }}>
            fenora<span style={{ color: "#c9a96e" }}>.</span>
          </div>
          <div style={{ width: 40, height: 3, background: "#c9a96e", borderRadius: 2, marginBottom: 40 }} />

          <h2 style={{ fontSize: 38, fontWeight: 900, color: "#fff", lineHeight: 1.2, letterSpacing: "-1px", margin: "0 0 16px" }}>
            Track less.<br /><em style={{ fontStyle: "italic" }}>Live more.</em>
          </h2>
          <p style={{ color: "rgba(255,255,255,0.75)", fontSize: 15, lineHeight: 1.7, maxWidth: 320, marginBottom: 40 }}>
            Your intelligent budget & wardrobe companion for Gen Z students in India.
          </p>

          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            {["📊 Smart Charts", "🤖 AI Insights", "👗 Wardrobe IQ", "📧 Monthly Reports"].map((f) => (
              <div key={f} style={{
                background: "rgba(255,255,255,0.15)", backdropFilter: "blur(8px)",
                padding: "8px 16px", borderRadius: 100, fontSize: 12,
                color: "#fff", fontWeight: 600, border: "1px solid rgba(255,255,255,0.2)",
              }}>{f}</div>
            ))}
          </div>

          {/* Testimonial */}
          <div style={{ marginTop: 48, background: "rgba(255,255,255,0.1)", backdropFilter: "blur(12px)", borderRadius: 16, padding: "20px 22px", border: "1px solid rgba(255,255,255,0.15)" }}>
            <p style={{ color: "rgba(255,255,255,0.9)", fontSize: 13, lineHeight: 1.6, margin: "0 0 12px", fontStyle: "italic" }}>
              "Fenora helped me save ₹3,000 last month just by showing me what I was spending on food delivery!"
            </p>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", fontWeight: 600 }}>— Priya, BITS Pilani</div>
          </div>
        </div>
      </div>

      {/* Right Panel */}
      <div style={{
        flex: "1 1 55%", display: "flex", alignItems: "center", justifyContent: "center",
        padding: "40px 24px", minHeight: "100vh",
      }}>
        <div style={{ width: "100%", maxWidth: 420 }}>
          {/* Logo (mobile) */}
          <div style={{ textAlign: "center", marginBottom: 32, display: "block" }}>
            <div style={{ fontSize: 24, fontWeight: 900, color: "#1a1a2e" }}>
              Fenora<span style={{ color: "#7c6fa0" }}>.</span>
            </div>
          </div>

          <div style={{
            background: "#fff", borderRadius: 24, padding: "36px 36px",
            boxShadow: "0 8px 48px rgba(124,111,160,0.12)",
            border: "1px solid rgba(124,111,160,0.08)",
          }}>
            <h2 style={{ fontSize: 24, fontWeight: 800, color: "#1a1a2e", margin: "0 0 6px", letterSpacing: "-0.5px" }}>
              {mode === "login" ? "Welcome back 👋" : "Create account 🚀"}
            </h2>
            <p style={{ fontSize: 13, color: "#9898b8", marginBottom: 28 }}>
              {mode === "login" ? "Sign in to your Fenora account" : "Start tracking smarter — it's free"}
            </p>

            {error && (
              <div style={{ background: "#fff8f8", border: "1px solid #fad5d5", borderRadius: 12, padding: "12px 16px", display: "flex", gap: 10, alignItems: "center", marginBottom: 20 }}>
                <span>⚠️</span>
                <span style={{ fontSize: 13, color: "#e07070" }}>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {mode === "register" && (
                <div>
                  <label style={labelStyle}>Your Name</label>
                  <input style={inputStyle} name="name" placeholder="e.g. Prachi" value={form.name} onChange={onChange} />
                </div>
              )}
              <div>
                <label style={labelStyle}>Email Address</label>
                <input style={inputStyle} type="email" name="email" placeholder="you@example.com" value={form.email} onChange={onChange} required />
              </div>
              <div>
                <label style={labelStyle}>Password</label>
                <div style={{ position: "relative" }}>
                  <input style={{ ...inputStyle, paddingRight: 44 }} type={showPass ? "text" : "password"} name="password" placeholder="••••••••" value={form.password} onChange={onChange} required />
                  <button type="button" onClick={() => setShowPass(!showPass)} style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: 16, color: "#9898b8" }}>
                    {showPass ? "🙈" : "👁️"}
                  </button>
                </div>
              </div>
              {mode === "register" && (
                <div>
                  <label style={labelStyle}>Monthly Budget (₹)</label>
                  <input style={inputStyle} type="number" name="budget" placeholder="e.g. 10000" value={form.budget} onChange={onChange} />
                  <span style={{ fontSize: 11, color: "#b0aec8", marginTop: 4, display: "block" }}>You can change this anytime</span>
                </div>
              )}
              <button type="submit" disabled={loading} style={{
                background: "linear-gradient(135deg, #7c6fa0, #a89cc8)",
                color: "#fff", border: "none", borderRadius: 14, padding: "14px",
                fontSize: 14, fontWeight: 800, cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.7 : 1, fontFamily: "inherit", marginTop: 4,
                boxShadow: "0 4px 20px rgba(124,111,160,0.35)",
                letterSpacing: "0.3px",
              }}>
                {loading ? "Please wait…" : mode === "login" ? "Sign In →" : "Create Account →"}
              </button>
            </form>

            <div style={{ marginTop: 24, textAlign: "center", fontSize: 13, color: "#9898b8" }}>
              {mode === "login" ? "Don't have an account? " : "Already have an account? "}
              <button onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }} style={{
                color: "#7c6fa0", fontWeight: 700, textDecoration: "underline",
                cursor: "pointer", background: "none", border: "none",
                fontFamily: "inherit", fontSize: 13,
              }}>
                {mode === "login" ? "Sign Up" : "Sign In"}
              </button>
            </div>
          </div>

          <p style={{ textAlign: "center", fontSize: 11, color: "#b0aec8", marginTop: 20 }}>
            🔒 Your data is private and never shared
          </p>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800;900&display=swap');
      `}</style>
    </div>
  );
}

const labelStyle = { display: "block", fontSize: 11, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 8 };
const inputStyle = {
  width: "100%", padding: "12px 16px", borderRadius: 12, border: "1.5px solid #e8e4f5",
  fontSize: 13, color: "#1a1a2e", background: "#faf9ff", outline: "none",
  fontFamily: "inherit", boxSizing: "border-box", transition: "border 0.2s",
};