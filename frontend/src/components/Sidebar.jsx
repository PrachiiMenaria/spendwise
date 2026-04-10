import React from "react";
import { NavLink, useNavigate } from "react-router-dom";

const navItems = [
  { to: "/dashboard", icon: "⊞", label: "Dashboard" },
  { to: "/expenses", icon: "💳", label: "Expenses" },
  { to: "/wardrobe", icon: "👗", label: "Wardrobe" },
  { to: "/insights", icon: "🤖", label: "AI Insights" },
];

export default function Sidebar({ setIsAuthenticated, user, onLogout }) {
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

  const userName = user?.name || "Student";
  const initials = userName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className="sw-sidebar"
        style={{
          display: "flex",
          flexDirection: "column",
          position: "fixed",
          inset: "0 auto 0 0",
          width: 240,
          background: "#ffffff",
          borderRight: "1px solid #eeebf8",
          padding: "28px 16px 24px",
          zIndex: 40,
          boxShadow: "2px 0 24px rgba(124,111,160,0.07)",
        }}
      >
        {/* Logo */}
        <div style={{ padding: "0 10px", marginBottom: 32 }}>
          <div
            style={{
              fontSize: 20,
              fontWeight: 800,
              color: "#1a1a2e",
              letterSpacing: "-0.5px",
              lineHeight: 1,
            }}
          >
            SpendWise
            <span style={{ color: "#7c6fa0" }}>.</span>
          </div>
          <div
            style={{
              fontSize: 10,
              color: "#b5b2cc",
              fontWeight: 600,
              letterSpacing: "1px",
              marginTop: 4,
              textTransform: "uppercase",
            }}
          >
            Budget &amp; Wardrobe
          </div>
        </div>

        {/* Nav */}
        <nav
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            gap: 2,
          }}
        >
          {/* Landing Page Button */}
          <NavLink
            to="/"
            end
            style={({ isActive }) => ({
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "10px 13px",
              borderRadius: 12,
              fontSize: 13,
              fontWeight: isActive ? 600 : 400,
              color: isActive ? "#7c6fa0" : "#706d8a",
              background: isActive
                ? "linear-gradient(135deg, rgba(124,111,160,0.10), rgba(168,156,200,0.06))"
                : "transparent",
              textDecoration: "none",
              transition: "all 0.18s ease",
              border: isActive
                ? "1px solid rgba(124,111,160,0.14)"
                : "1px solid transparent",
              marginBottom: 12,
            })}
            onMouseEnter={(e) => {
              const isActive = e.currentTarget.getAttribute("aria-current") === "page";
              if (!isActive) {
                e.currentTarget.style.background = "#faf8ff";
                e.currentTarget.style.color = "#7c6fa0";
              }
            }}
            onMouseLeave={(e) => {
              const isActive = e.currentTarget.getAttribute("aria-current") === "page";
              if (!isActive) {
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.color = "#706d8a";
              }
            }}
          >
            <span style={{ fontSize: 17, width: 22, textAlign: "center", flexShrink: 0 }}>🏠</span>
            <span>Landing Page</span>
          </NavLink>

          <div
            style={{
              fontSize: 10,
              color: "#c4c0d8",
              fontWeight: 700,
              letterSpacing: "1px",
              textTransform: "uppercase",
              padding: "0 12px",
              marginBottom: 8,
            }}
          >
            Menu
          </div>

          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              style={({ isActive }) => ({
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "10px 13px",
                borderRadius: 12,
                fontSize: 13,
                fontWeight: isActive ? 600 : 400,
                color: isActive ? "#7c6fa0" : "#706d8a",
                background: isActive
                  ? "linear-gradient(135deg, rgba(124,111,160,0.10), rgba(168,156,200,0.06))"
                  : "transparent",
                textDecoration: "none",
                transition: "all 0.18s ease",
                border: isActive
                  ? "1px solid rgba(124,111,160,0.14)"
                  : "1px solid transparent",
              })}
              onMouseEnter={(e) => {
                const isActive = e.currentTarget.getAttribute("aria-current") === "page";
                if (!isActive) {
                  e.currentTarget.style.background = "#faf8ff";
                  e.currentTarget.style.color = "#7c6fa0";
                }
              }}
              onMouseLeave={(e) => {
                const isActive = e.currentTarget.getAttribute("aria-current") === "page";
                if (!isActive) {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "#706d8a";
                }
              }}
            >
              <span
                style={{
                  fontSize: 17,
                  width: 22,
                  textAlign: "center",
                  flexShrink: 0,
                }}
              >
                {item.icon}
              </span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User Card */}
        <div
          style={{
            borderTop: "1px solid #eeebf8",
            paddingTop: 16,
            marginTop: 8,
          }}
        >
          {/* User Info */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "8px 10px",
              borderRadius: 12,
              marginBottom: 8,
            }}
          >
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: "50%",
                flexShrink: 0,
                background: "linear-gradient(135deg, #7c6fa0, #a89cc8)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 13,
                fontWeight: 700,
                color: "#fff",
                letterSpacing: "0.5px",
              }}
            >
              {initials}
            </div>
            <div style={{ minWidth: 0 }}>
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: "#1a1a2e",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {userName}
              </div>
              <div
                style={{
                  fontSize: 11,
                  color: "#9e9bba",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {user?.email || "student@spendwise.app"}
              </div>
            </div>
          </div>

          {/* Sign Out */}
          <button
            onClick={handleLogout}
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              gap: 9,
              padding: "9px 13px",
              borderRadius: 12,
              background: "transparent",
              border: "1px solid #fad5d5",
              color: "#d96b6b",
              fontSize: 12,
              fontWeight: 600,
              cursor: "pointer",
              fontFamily: "inherit",
              transition: "all 0.18s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "#fff5f5";
              e.currentTarget.style.borderColor = "#f5b8b8";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.borderColor = "#fad5d5";
            }}
          >
            <span style={{ fontSize: 15 }}>🚪</span>
            Sign Out
          </button>
        </div>
      </aside>

      {/* Mobile Bottom Nav */}
      <nav
        className="sw-bottom-nav"
        style={{
          display: "none",
          position: "fixed",
          bottom: 0,
          left: 0,
          right: 0,
          zIndex: 50,
          background: "rgba(255,255,255,0.96)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          borderTop: "1px solid #eeebf8",
          boxShadow: "0 -4px 20px rgba(124,111,160,0.08)",
          padding: "8px 0 14px",
          justifyContent: "space-around",
        }}
      >
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            style={({ isActive }) => ({
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 3,
              textDecoration: "none",
              padding: "4px 14px",
              color: isActive ? "#7c6fa0" : "#b5b2cc",
              transition: "all 0.18s ease",
            })}
          >
            <span style={{ fontSize: 22 }}>{item.icon}</span>
            <span
              style={{ fontSize: 9, fontWeight: 700, letterSpacing: "0.3px" }}
            >
              {item.label}
            </span>
          </NavLink>
        ))}
      </nav>

      <style>{`
        @media (max-width: 768px) {
          .sw-sidebar { display: none !important; }
          .sw-bottom-nav { display: flex !important; }
        }
      `}</style>
    </>
  );
}