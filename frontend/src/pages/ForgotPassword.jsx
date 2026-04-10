import { useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function ForgotPassword({ onBack }) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    
    try {
      const res = await fetch(`${API}/api/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Something went wrong");
      setMessage(data.message);
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
      <div style={{
        flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
        padding: "40px 24px",
      }}>
        <div style={{ width: "100%", maxWidth: 420 }}>
          <button onClick={() => window.location.href = '/'} style={{
            background: "none", border: "none", cursor: "pointer",
            fontSize: 13, color: "#9898b8", fontFamily: "inherit",
            display: "flex", alignItems: "center", gap: 6, marginBottom: 28,
            padding: 0, transition: "color 0.15s",
          }}
            onMouseEnter={e => e.currentTarget.style.color = "#6b5fa0"}
            onMouseLeave={e => e.currentTarget.style.color = "#9898b8"}
          >
            ← Back to login
          </button>

          <div style={{
            background: "#fff", borderRadius: 24, padding: "36px 36px",
            boxShadow: "0 8px 48px rgba(107,95,160,0.12)",
            border: "1px solid rgba(107,95,160,0.08)",
          }}>
            <h2 style={{ fontSize: 24, fontWeight: 800, color: "#18182e", margin: "0 0 6px", letterSpacing: "-0.5px" }}>
              Reset Password 🔐
            </h2>
            <p style={{ fontSize: 13, color: "#9898b8", marginBottom: 28 }}>
              Enter your email and we'll send you a link to reset your password.
            </p>

            {error && (
              <div style={{ background: "#fff8f8", border: "1px solid #fad5d5", borderRadius: 12, padding: "12px 16px", display: "flex", gap: 10, alignItems: "center", marginBottom: 20 }}>
                <span>⚠️</span>
                <span style={{ fontSize: 13, color: "#d96b6b" }}>{error}</span>
              </div>
            )}
            
            {message && (
              <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 12, padding: "12px 16px", display: "flex", gap: 10, alignItems: "center", marginBottom: 20 }}>
                <span>✅</span>
                <span style={{ fontSize: 13, color: "#166534", lineHeight: 1.5 }}>{message}</span>
              </div>
            )}

            {!message && (
              <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <div>
                  <label style={{
                    display: "block", fontSize: 11, fontWeight: 700, color: "#9898b8",
                    textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 8,
                  }}>Email Address</label>
                  <input style={{
                    width: "100%", padding: "12px 16px", borderRadius: 12,
                    border: "1.5px solid #ebe8f5", fontSize: 13, color: "#18182e",
                    background: "#faf9ff", outline: "none", fontFamily: "inherit",
                    boxSizing: "border-box", transition: "border 0.18s, box-shadow 0.18s",
                  }} type="email" placeholder="you@example.com" value={email}
                    onChange={e => setEmail(e.target.value)} required />
                </div>
                
                <button type="submit" disabled={loading || !email} style={{
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
                      Sending...
                    </span>
                  ) : "Send Reset Link →"}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&display=swap');
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
