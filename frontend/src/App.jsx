// wardrobe-analysis-project/frontend/src/App.jsx
import { useState, useEffect } from "react";
import Dashboard from "./pages/Dashboard";
import Wardrobe from "./pages/Wardrobe";
import Expenses from "./pages/Expenses";
import Login from "./pages/Login";
import "./App.css";

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("sw_user");
    return saved ? JSON.parse(saved) : null;
  });

  const handleLogin = (userData) => {
    localStorage.setItem("sw_user", JSON.stringify(userData));
    setUser(userData);
    setPage("dashboard");
  };

  const handleLogout = () => {
    localStorage.removeItem("sw_user");
    setUser(null);
    setPage("dashboard");
  };

  if (!user) return <Login onLogin={handleLogin} />;

  return (
    <div className="app-shell">
      <Sidebar page={page} setPage={setPage} user={user} onLogout={handleLogout} />
      <main className="app-main">
        {page === "dashboard" && <Dashboard user={user} />}
        {page === "wardrobe" && <Wardrobe />}
        {page === "expenses" && <Expenses />}
      </main>
    </div>
  );
}

function Sidebar({ page, setPage, user, onLogout }) {
  const navItems = [
    { key: "dashboard", icon: "⊞", label: "Dashboard" },
    { key: "wardrobe", icon: "👗", label: "Wardrobe" },
    { key: "expenses", icon: "💳", label: "Expenses" },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">✦</div>
        <span className="brand-name">fenora</span>
      </div>

      <div className="sidebar-user">
        <div className="user-avatar">{user.name?.[0]?.toUpperCase() || "U"}</div>
        <div className="user-info">
          <div className="user-name">{user.name || "User"}</div>
          <div className="user-role">Smart Spender</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.key}
            className={`nav-item ${page === item.key ? "active" : ""}`}
            onClick={() => setPage(item.key)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <button className="sidebar-logout" onClick={onLogout}>
        <span>⇤</span> Sign Out
      </button>
    </aside>
  );
}