// fenora/frontend/src/App.jsx — UPGRADED
import { useState, useEffect } from "react";
import Dashboard from "./pages/Dashboard";
import Wardrobe from "./pages/Wardrobe";
import Expenses from "./pages/Expenses";
import Insights from "./pages/Insights";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import FloatingChat from "./components/floatingchat";
import "./App.css";
import EmailSettings from "./pages/EmailSettings";

import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";

const originalFetch = window.fetch;
window.fetch = async function () {
  let [resource, config] = arguments;
  if (!config) config = {};
  
  const token = localStorage.getItem("sw_token");
  if (token) {
    config.headers = {
      ...config.headers,
      "Authorization": `Bearer ${token}`
    };
  }
  
  // Strip out old credentials header to avoid cross-origin cookie baggage
  if (config.credentials) delete config.credentials;
  
  const response = await originalFetch(resource, config);
  
  // Automatically force logout if token expires or unauthorized
  if (response.status === 401 && !resource.includes("/api/login") && !resource.includes("/api/register")) {
    localStorage.removeItem("sw_token");
    localStorage.removeItem("sw_user");
    window.location.href = "/";
  }
  
  return response;
};

export default function App() {
  const [page, setPage] = useState(() => {
    const path = window.location.pathname;
    if (path.includes("/reset-password")) return "reset-password";
    if (path.includes("/forgot-password")) return "forgot-password";
    return "landing";
  });
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem("sw_user");
      return saved ? JSON.parse(saved) : null;
    } catch { return null; }
  });

  // Keep-alive ping for Render backend
  useEffect(() => {
    const keepAlive = setInterval(() => {
      fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/`)
        .catch(() => {});
    }, 10 * 60 * 1000); // every 10 minutes
    return () => clearInterval(keepAlive);
  }, []);

  const handleLogin = (userData) => {
    localStorage.setItem("sw_user", JSON.stringify(userData));
    if (userData.token) {
      localStorage.setItem("sw_token", userData.token);
    }
    setUser(userData);
    setPage("dashboard");
  };

  const handleLogout = () => {
    localStorage.removeItem("sw_user");
    localStorage.removeItem("sw_token");
    setUser(null);
    setPage("landing");
  };

  // Show landing page for unauthenticated users
  if (!user && page === "landing") {
    return <Landing onGetStarted={() => setPage("login")} />;
  }
  
  if (page === "forgot-password") return <ForgotPassword onBack={() => setPage("login")} />;
  if (page === "reset-password") return <ResetPassword />;

  if (!user) return <Login onLogin={handleLogin} onBack={() => setPage("landing")} />;

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="app-shell">
      {/* Mobile Header (hidden on desktop via CSS) */}
      <div className="mobile-header">
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 8, background: "linear-gradient(135deg, #6b5fa0, #9b8ec8)", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 13 }}>✦</div>
          <span style={{ fontSize: 16, fontWeight: 800, color: "#18182e", letterSpacing: "-0.4px" }}>fenora</span>
        </div>
        <button onClick={() => setMobileMenuOpen(true)} style={{ background: "none", border: "none", fontSize: 24, color: "#6b5fa0", cursor: "pointer", display: "flex", alignItems: "center" }}>☰</button>
      </div>

      <Sidebar page={page} setPage={setPage} user={user} onLogout={handleLogout} mobileMenuOpen={mobileMenuOpen} setMobileMenuOpen={setMobileMenuOpen} />
      
      {/* Tap backdrop to close on mobile */}
      {mobileMenuOpen && <div className="mobile-backdrop" onClick={() => setMobileMenuOpen(false)} />}

      <main className="app-main">
        <div className="page-content">
          {page === "dashboard" && <Dashboard user={user} />}
          {page === "wardrobe" && <Wardrobe />}
          {page === "expenses" && <Expenses />}
          {page === "insights" && <Insights />}
          {page === "email-settings" && <EmailSettings />}
        </div>
        
        {/* Footer */}
        <footer style={{
          textAlign: 'center',
          padding: '20px',
          marginTop: '40px',
          fontSize: '14px',
          color: '#888',
          borderTop: '1px solid rgba(255,255,255,0.1)'
        }}>
          Made with ❤️ by <strong style={{color: '#a78bfa'}}>Prachi Menaria</strong>
        </footer>
      </main>
      <FloatingChat />
    </div>
  );
}

/* ── Sidebar ─────────────────────────────────────────────────── */
function Sidebar({ page, setPage, user, onLogout, mobileMenuOpen, setMobileMenuOpen }) {
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    { key: "dashboard", icon: SquaresIcon, label: "Dashboard" },
    { key: "wardrobe",  icon: WardrobeIcon, label: "Wardrobe" },
    { key: "expenses",  icon: ExpenseIcon,  label: "Expenses" },
    { key: "insights",  icon: InsightIcon,  label: "AI Insights" },
    { key: "email-settings", icon: EmailIcon, label: "Email Settings" },
  ];

  const w = collapsed && !mobileMenuOpen ? 68 : 236; // Always full width when open on mobile

  return (
    <aside className={`fenora-sidebar ${mobileMenuOpen ? 'mobile-open' : ''}`} style={{
      position: "fixed", inset: "0 auto 0 0",
      width: w, background: "#ffffff",
      borderRight: "1px solid rgba(107,95,160,0.07)",
      padding: "24px 12px 20px",
      zIndex: 50, display: "flex", flexDirection: "column",
      boxShadow: "2px 0 32px rgba(107,95,160,0.07)",
      transition: "all 0.25s cubic-bezier(0.4,0,0.2,1)",
      overflow: "hidden",
    }}>
      {/* Logo */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "0 8px", marginBottom: 28 }}>
        <div style={{
          width: 34, height: 34, borderRadius: 10, flexShrink: 0,
          background: "linear-gradient(135deg, #6b5fa0, #9b8ec8)",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 4px 12px rgba(107,95,160,0.35)",
        }}>
          <span style={{ fontSize: 17, color: "#fff", lineHeight: 1 }}>✦</span>
        </div>
        {!collapsed && (
          <div>
            <div style={{ fontSize: 17, fontWeight: 800, color: "#18182e", letterSpacing: "-0.4px", lineHeight: 1 }}>
              fenora
            </div>
            <div style={{ fontSize: 9, color: "#b0aec8", fontWeight: 600, letterSpacing: "1.2px", textTransform: "uppercase", marginTop: 2 }}>
              Smart Living
            </div>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          style={{
            marginLeft: "auto", background: "none", border: "none",
            cursor: "pointer", padding: 4, color: "#b0aec8",
            fontSize: 16, transition: "color 0.15s", lineHeight: 1,
            flexShrink: 0,
          }}
          title={collapsed ? "Expand" : "Collapse"}
        >
          {collapsed ? "›" : "‹"}
        </button>
      </div>

      {/* User chip */}
      {!collapsed && (
        <div style={{
          display: "flex", alignItems: "center", gap: 10,
          padding: "10px 12px", background: "linear-gradient(135deg, rgba(107,95,160,0.06), rgba(155,142,200,0.04))",
          borderRadius: 14, marginBottom: 22,
          border: "1px solid rgba(107,95,160,0.08)",
        }}>
          <div style={{
            width: 34, height: 34, borderRadius: "50%", flexShrink: 0,
            background: "linear-gradient(135deg, #6b5fa0, #9b8ec8)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 13, fontWeight: 800, color: "#fff",
          }}>
            {(user.name || "U").charAt(0).toUpperCase()}
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#18182e", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {user.name || "User"}
            </div>
            <div style={{ fontSize: 10, color: "#9898b8", fontWeight: 500 }}>Smart Spender ✨</div>
          </div>
        </div>
      )}

      {/* Label */}
      {!collapsed && (
        <div style={{ fontSize: 9, color: "#c4c0d8", fontWeight: 700, letterSpacing: "1.2px", textTransform: "uppercase", padding: "0 12px", marginBottom: 8 }}>
          Navigation
        </div>
      )}

      {/* Nav items */}
      <nav style={{ flex: 1, display: "flex", flexDirection: "column", gap: 3 }}>
        {navItems.map((item) => {
          const isActive = page === item.key;
          const Icon = item.icon;
          return (
            <button
              key={item.key}
              onClick={() => { setPage(item.key); if (setMobileMenuOpen) setMobileMenuOpen(false); }}
              title={collapsed ? item.label : undefined}
              style={{
                display: "flex", alignItems: "center",
                gap: collapsed ? 0 : 11,
                justifyContent: collapsed ? "center" : "flex-start",
                padding: collapsed ? "11px 0" : "10px 13px",
                borderRadius: 13,
                fontSize: 13, fontWeight: isActive ? 700 : 500,
                color: isActive ? "#6b5fa0" : "#706d8a",
                background: isActive
                  ? "linear-gradient(135deg, rgba(107,95,160,0.10), rgba(155,142,200,0.06))"
                  : "transparent",
                border: isActive ? "1px solid rgba(107,95,160,0.13)" : "1px solid transparent",
                cursor: "pointer", transition: "all 0.18s ease",
                fontFamily: "inherit", textAlign: "left", width: "100%",
              }}
              onMouseEnter={e => {
                if (!isActive) {
                  e.currentTarget.style.background = "rgba(107,95,160,0.05)";
                  e.currentTarget.style.color = "#6b5fa0";
                }
              }}
              onMouseLeave={e => {
                if (!isActive) {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "#706d8a";
                }
              }}
            >
              <Icon size={18} active={isActive} />
              {!collapsed && <span>{item.label}</span>}
              {!collapsed && isActive && (
                <div style={{ marginLeft: "auto", width: 6, height: 6, borderRadius: "50%", background: "#6b5fa0" }} />
              )}
            </button>
          );
        })}
      </nav>

      {/* Sign out */}
      <button
        onClick={onLogout}
        style={{
          display: "flex", alignItems: "center",
          gap: collapsed ? 0 : 9,
          justifyContent: collapsed ? "center" : "flex-start",
          padding: collapsed ? "10px 0" : "9px 13px",
          borderRadius: 13, background: "transparent",
          border: "1px solid rgba(217,107,107,0.2)",
          color: "#d96b6b", fontSize: 12, fontWeight: 600,
          cursor: "pointer", fontFamily: "inherit",
          transition: "all 0.18s ease", width: "100%",
          marginTop: 8,
        }}
        title={collapsed ? "Sign Out" : undefined}
        onMouseEnter={e => { e.currentTarget.style.background = "#fff5f5"; e.currentTarget.style.borderColor = "#f5b8b8"; }}
        onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.borderColor = "rgba(217,107,107,0.2)"; }}
      >
        <span style={{ fontSize: 15 }}>🚪</span>
        {!collapsed && "Sign Out"}
      </button>

      {/* Mobile bottom nav */}
      <style>{`
        @media (max-width: 768px) {
          .app-main { margin-left: 0 !important; }
        }
      `}</style>
    </aside>
  );
}

/* ── Icon Components ─────────────────────────────────────────── */
function SquaresIcon({ size = 18, active }) {
  return (
    <svg width={size} height={size} viewBox="0 0 18 18" fill="none">
      <rect x="1" y="1" width="7" height="7" rx="2" fill={active ? "#6b5fa0" : "#9898b8"} />
      <rect x="10" y="1" width="7" height="7" rx="2" fill={active ? "#9b8ec8" : "#b8b4d0"} opacity={active ? 1 : 0.7} />
      <rect x="1" y="10" width="7" height="7" rx="2" fill={active ? "#9b8ec8" : "#b8b4d0"} opacity={active ? 1 : 0.7} />
      <rect x="10" y="10" width="7" height="7" rx="2" fill={active ? "#6b5fa0" : "#9898b8"} />
    </svg>
  );
}
function WardrobeIcon({ size = 18, active }) {
  return (
    <svg width={size} height={size} viewBox="0 0 18 18" fill="none">
      <path d="M9 2 L2 6 L4 6 L4 16 L14 16 L14 6 L16 6 Z" fill={active ? "#6b5fa0" : "#9898b8"} />
      <circle cx="9" cy="11" r="1.5" fill={active ? "#c9a96e" : "#b8b4d0"} />
    </svg>
  );
}
function ExpenseIcon({ size = 18, active }) {
  return (
    <svg width={size} height={size} viewBox="0 0 18 18" fill="none">
      <rect x="1" y="3" width="16" height="12" rx="3" fill={active ? "#6b5fa0" : "#9898b8"} />
      <rect x="1" y="7" width="16" height="2.5" fill={active ? "#9b8ec8" : "#b8b4d0"} />
      <rect x="4" y="11" width="4" height="1.5" rx="0.75" fill={active ? "#c9a96e" : "#d0cce8"} />
    </svg>
  );
}
function InsightIcon({ size = 18, active }) {
  return (
    <svg width={size} height={size} viewBox="0 0 18 18" fill="none">
      <circle cx="9" cy="9" r="7.5" fill={active ? "#6b5fa0" : "#9898b8"} />
      <path d="M6 12 L8 7 L9 9 L11 5 L13 10" stroke={active ? "#fff" : "#e8e4f5"} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function EmailIcon({ size = 18, active }) {
  return (
    <svg width={size} height={size} viewBox="0 0 18 18" fill="none">
      <rect x="2" y="4" width="14" height="10" rx="2" fill={active ? "#6b5fa0" : "#9898b8"} />
      <path d="M2.5 5.5 L9 9 L15.5 5.5" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}