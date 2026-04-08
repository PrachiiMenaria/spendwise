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

export default function App() {
  const [page, setPage] = useState("landing");
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem("sw_user");
      return saved ? JSON.parse(saved) : null;
    } catch { return null; }
  });

  const handleLogin = (userData) => {
    localStorage.setItem("sw_user", JSON.stringify(userData));
    setUser(userData);
    setPage("dashboard");
  };

  const handleLogout = () => {
    localStorage.removeItem("sw_user");
    setUser(null);
    setPage("landing");
  };

  // Show landing page for unauthenticated users
  if (!user && page === "landing") {
    return <Landing onGetStarted={() => setPage("login")} />;
  }

  if (!user) return <Login onLogin={handleLogin} onBack={() => setPage("landing")} />;

  return (
    <div className="app-shell">
      <Sidebar page={page} setPage={setPage} user={user} onLogout={handleLogout} />
      <main className="app-main">
        <div className="page-content">
          {page === "dashboard" && <Dashboard user={user} />}
          {page === "wardrobe" && <Wardrobe />}
          {page === "expenses" && <Expenses />}
          {page === "insights" && <Insights />}
        </div>
      </main>
      <FloatingChat />
    </div>
  );
}

/* ── Sidebar ─────────────────────────────────────────────────── */
function Sidebar({ page, setPage, user, onLogout }) {
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    { key: "dashboard", icon: SquaresIcon, label: "Dashboard" },
    { key: "wardrobe",  icon: WardrobeIcon, label: "Wardrobe" },
    { key: "expenses",  icon: ExpenseIcon,  label: "Expenses" },
    { key: "insights",  icon: InsightIcon,  label: "AI Insights" },
  ];

  const w = collapsed ? 68 : 236;

  return (
    <aside style={{
      position: "fixed", inset: "0 auto 0 0",
      width: w, background: "#ffffff",
      borderRight: "1px solid rgba(107,95,160,0.07)",
      padding: "24px 12px 20px",
      zIndex: 40, display: "flex", flexDirection: "column",
      boxShadow: "2px 0 32px rgba(107,95,160,0.07)",
      transition: "width 0.25s cubic-bezier(0.4,0,0.2,1)",
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
              onClick={() => setPage(item.key)}
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