import { useState, useEffect } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function ResetPassword() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const [showPass, setShowPass] = useState(false);

  useEffect(() => {
    if (!token) {
      setError("Invalid or missing reset token.");
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      setLoading(false);
      return;
    }
    
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      setLoading(false);
      return;
    }
    
    try {
      const res = await fetch(`${API}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Something went wrong");
      setMessage("Your password was updated successfully. You can now login.");
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
          <div style={{
            background: "#fff", borderRadius: 24, padding: "36px 36px",
            boxShadow: "0 8px 48px rgba(107,95,160,0.12)",
            border: "1px solid rgba(107,95,160,0.08)",
          }}>
            <h2 style={{ fontSize: 24, fontWeight: 800, color: "#18182e", margin: "0 0 6px", letterSpacing: "-0.5px" }}>
              New Password 🔑
            </h2>
            <p style={{ fontSize: 13, color: "#9898b8", marginBottom: 28 }}>
              Please enter your new password below.
            </p>

            {error && (
              <div style={{ background: "#fff8f8", border: "1px solid #fad5d5", borderRadius: 12, padding: "12px 16px", display: "flex", gap: 10, alignItems: "center", marginBottom: 20 }}>
                <span>⚠️</span>
                <span style={{ fontSize: 13, color: "#d96b6b" }}>{error}</span>
              </div>
            )}
            
            {message && (
              <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 12, padding: "12px 16px", display: "flex", gap: 10, alignItems: "center", marginBottom: 20, flexDirection: "column", textAlign: "center" }}>
                <span style={{ fontSize: 32 }}>✅</span>
                <span style={{ fontSize: 14, color: "#166534", lineHeight: 1.5, fontWeight: 600 }}>{message}</span>
                <button onClick={() => window.location.href = '/'} style={{
                  background: "#166534", color: "#fff", border: "none", borderRadius: 8, padding: "8px 16px",
                  fontSize: 13, fontWeight: 700, cursor: "pointer", fontFamily: "inherit", marginTop: 8
                }}>
                  Back to Login
                </button>
              </div>
            )}

            {!message && (
              <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <div>
                  <label style={labelStyle}>New Password</label>
                  <div style={{ position: "relative" }}>
                    <input style={{ ...inputStyle, paddingRight: 44 }} type={showPass ? "text" : "password"}
                      placeholder="••••••••" value={password} disabled={!token}
                      onChange={e => setPassword(e.target.value)} required />
                    <button type="button" onClick={() => setShowPass(!showPass)} style={{
                      position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)",
                      background: "none", border: "none", cursor: "pointer", fontSize: 15, color: "#9898b8",
                    }}>
                      {showPass ? "🙈" : "👁️"}
                    </button>
                  </div>
                </div>
                
                <div>
                  <label style={labelStyle}>Confirm Password</label>
                  <input style={inputStyle} type={showPass ? "text" : "password"} placeholder="••••••••" value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)} required disabled={!token} />
                </div>
                
                <button type="submit" disabled={loading || !token || !password || !confirmPassword} style={{
                  background: loading ? "#b0aec8" : "linear-gradient(135deg, #6b5fa0, #9b8ec8)",
                  color: "#fff", border: "none", borderRadius: 14, padding: "14px",
                  fontSize: 14, fontWeight: 800, cursor: loading || !token ? "not-allowed" : "pointer",
                  fontFamily: "inherit", marginTop: 4,
                  boxShadow: loading ? "none" : "0 4px 20px rgba(107,95,160,0.38)",
                  transition: "all 0.22s", letterSpacing: "0.2px",
                }}
                  onMouseEnter={e => { if (!loading && token) e.currentTarget.style.transform = "translateY(-1px)"; }}
                  onMouseLeave={e => e.currentTarget.style.transform = "translateY(0)"}
                >
                  {loading ? (
                    <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
                      <span style={{ width: 16, height: 16, borderRadius: "50%", border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "#fff", animation: "spin 0.8s linear infinite", display: "inline-block" }} />
                      Saving...
                    </span>
                  ) : "Update Password →"}
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
