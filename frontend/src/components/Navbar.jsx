// fenora/frontend/src/components/Navbar.jsx
import React from "react";
import { useNavigate } from "react-router-dom";

export default function Navbar({ setIsAuthenticated, user, onLogout }) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await fetch("/api/logout", { method: "POST", credentials: "include" });
    } catch (e) {
      console.error(e);
    } finally {
      if (onLogout) onLogout();
      else if (setIsAuthenticated) setIsAuthenticated(false);
      navigate("/login");
    }
  };

  return (
    <header style={{
      position: "fixed", top: 0, left: 240, right: 0, height: 64, zIndex: 30,
      background: "rgba(248,246,255,0.9)", backdropFilter: "blur(20px)",
      borderBottom: "1px solid rgba(124,111,160,0.08)",
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "0 28px",
      boxShadow: "0 2px 12px rgba(124,111,160,0.06)",
    }}
      className="sw-navbar"
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{ fontSize: 11, color: "#c0bcd8", fontWeight: 700, letterSpacing: "1px", textTransform: "uppercase" }}>
          fenora Dashboard
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <div style={{ fontSize: 13, color: "#6b6888" }}>
          Hello, <strong style={{ color: "#1a1a2e" }}>{user?.name?.split(" ")[0] || "there"}</strong> 👋
        </div>
        <div style={{
          width: 34, height: 34, borderRadius: "50%",
          background: "linear-gradient(135deg, #7c6fa0, #a89cc8)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 13, fontWeight: 800, color: "#fff", cursor: "pointer",
          flexShrink: 0,
        }}>
          {(user?.name || "U").charAt(0).toUpperCase()}
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .sw-navbar { left: 0 !important; }
        }
      `}</style>
    </header>
  );
}