// fenora/frontend/src/pages/Expenses.jsx
import { useState, useEffect } from "react";

const API = "http://localhost:5000";

function formatINR(n) {
  return "₹" + Number(n || 0).toLocaleString("en-IN");
}

const EXPENSE_CATEGORIES = ["Food", "Transport", "Shopping", "Entertainment", "Education", "Health", "Utilities", "Rent", "Others"];

const CATEGORY_ICONS = {
  Food: "🍱", Transport: "🚗", Shopping: "🛍️", Entertainment: "🎬",
  Education: "📚", Health: "💊", Utilities: "🔌", Rent: "🏠", Others: "💳",
};

const CATEGORY_COLORS = {
  Food: "#fdf0e8", Transport: "#e8f4fd", Shopping: "#fde8f8",
  Entertainment: "#fdf8e8", Education: "#e8f0fd", Health: "#e8fdf0",
  Utilities: "#fde8e8", Rent: "#f0e8fd", Others: "#f0f0f0",
};

export default function Expenses() {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({ amount: "", category: "Food", note: "" });
  const [filterCat, setFilterCat] = useState("All");
  const fetchExpenses = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/expenses`, { credentials: "include" });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      setExpenses(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchExpenses(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.amount || parseFloat(form.amount) <= 0) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/api/expenses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ ...form, amount: parseFloat(form.amount) }),
      });
      if (!res.ok) throw new Error("Failed to add");
      setForm({ amount: "", category: "Food", note: "" });
      setShowForm(false);
      await fetchExpenses();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this expense?")) return;
    try {
      await fetch(`${API}/api/expenses/${id}`, { method: "DELETE", credentials: "include" });
      setExpenses((prev) => prev.filter((e) => e.id !== id));
    } catch (err) {
      setError(err.message);
    }
  };

  const now = new Date();
  const thisMonthExps = expenses.filter((e) => {
    const d = new Date(e.created_at);
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
  });
  const thisMonthTotal = thisMonthExps.reduce((s, e) => s + e.amount, 0);
  const catTotals = {};
  expenses.forEach((e) => { catTotals[e.category] = (catTotals[e.category] || 0) + e.amount; });
  const topCat = Object.entries(catTotals).sort((a, b) => b[1] - a[1])[0];
  const allTimeTotal = expenses.reduce((s, e) => s + e.amount, 0);

  const filterBtns = ["All", "Food", "Transport", "Shopping", "Entertainment", "Others"];
  const filtered = filterCat === "All" ? expenses : expenses.filter((e) => e.category === filterCat);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: "#1a1a2e", margin: 0, letterSpacing: "-0.5px" }}>Expenses 💳</h1>
          <p style={{ color: "#9898b8", marginTop: 4, fontSize: 14 }}>Track every rupee you spend</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} style={{
          background: showForm ? "#f0eef8" : "linear-gradient(135deg,#7c6fa0,#a89cc8)",
          color: showForm ? "#7c6fa0" : "#fff",
          border: "none", borderRadius: 50, padding: "10px 22px",
          fontSize: 13, fontWeight: 700, cursor: "pointer",
          boxShadow: showForm ? "none" : "0 4px 16px rgba(124,111,160,0.3)",
          transition: "all 0.2s", fontFamily: "inherit",
        }}>
          {showForm ? "✕ Cancel" : "+ Add Expense"}
        </button>
      </div>

      {/* Summary Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 14 }}>
        {[
          { label: "This Month", value: formatINR(thisMonthTotal), sub: `${thisMonthExps.length} transactions`, icon: "📅", color: "#7c6fa0" },
          { label: "Top Category", value: topCat?.[0] || "—", sub: topCat ? formatINR(topCat[1]) : "No data yet", icon: "🏆", color: "#c9a96e" },
          { label: "All Time Spent", value: formatINR(allTimeTotal), sub: `${expenses.length} entries`, icon: "📊", color: "#6aaa8a" },
        ].map((c, i) => (
          <div key={i} style={{
            background: "#fff", borderRadius: 16, padding: "18px 18px 14px",
            boxShadow: "0 2px 16px rgba(124,111,160,0.08)",
            border: "1px solid rgba(124,111,160,0.08)", position: "relative", overflow: "hidden",
          }}>
            <div style={{ position: "absolute", top: 12, right: 14, fontSize: 22, opacity: 0.6 }}>{c.icon}</div>
            <div style={{ fontSize: 10, color: "#9898b8", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 6 }}>{c.label}</div>
            <div style={{ fontSize: 20, fontWeight: 800, color: c.color }}>{c.value}</div>
            <div style={{ fontSize: 11, color: "#b0aec8", marginTop: 4 }}>{c.sub}</div>
          </div>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div style={{ background: "#fff8f8", border: "1px solid #fad5d5", borderRadius: 12, padding: "12px 16px", display: "flex", gap: 10, alignItems: "center" }}>
          <span>⚠️</span>
          <span style={{ fontSize: 13, color: "#e07070" }}>{error}</span>
        </div>
      )}

      {/* Add Form */}
      {showForm && (
        <div style={{
          background: "#fff", borderRadius: 18, padding: "24px",
          boxShadow: "0 4px 24px rgba(124,111,160,0.12)",
          border: "1px solid #e8e4f5",
          animation: "fadeUp 0.3s ease both"
        }}>
          <h3 style={{ margin: "0 0 18px", fontSize: 16, fontWeight: 700, color: "#1a1a2e" }}>New Expense</h3>
          <form onSubmit={handleSubmit}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 14 }}>
              <div>
                <label style={labelStyle}>Amount (₹) *</label>
                <input style={inputStyle} type="number" placeholder="0" value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: e.target.value })} required min="1" />
              </div>
              <div>
                <label style={labelStyle}>Category</label>
                <select style={inputStyle} value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                  {EXPENSE_CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                </select>
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>Note (optional)</label>
              <input style={inputStyle} placeholder="e.g. Swiggy dinner" value={form.note}
                onChange={(e) => setForm({ ...form, note: e.target.value })} />
            </div>
            <button type="submit" disabled={submitting} style={{
              width: "100%", background: "linear-gradient(135deg,#7c6fa0,#a89cc8)",
              color: "#fff", border: "none", borderRadius: 12, padding: "12px",
              fontSize: 14, fontWeight: 700, cursor: submitting ? "not-allowed" : "pointer",
              opacity: submitting ? 0.7 : 1, fontFamily: "inherit",
            }}>
              {submitting ? "Saving…" : "Add Expense"}
            </button>
          </form>
        </div>
      )}

      {/* Filter Tabs */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {filterBtns.map((cat) => (
          <button key={cat} onClick={() => setFilterCat(cat)} style={{
            padding: "7px 16px", borderRadius: 100, fontSize: 12, fontWeight: 600,
            border: filterCat === cat ? "none" : "1.5px solid #e8e4f5",
            background: filterCat === cat ? "linear-gradient(135deg,#7c6fa0,#a89cc8)" : "#fff",
            color: filterCat === cat ? "#fff" : "#9898b8",
            cursor: "pointer", transition: "all 0.2s", fontFamily: "inherit",
          }}>{cat}</button>
        ))}
      </div>

      {/* List */}
      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "40px 0" }}>
          <div style={{ width: 36, height: 36, borderRadius: "50%", border: "4px solid #e8e4f3", borderTopColor: "#7c6fa0", animation: "spin 0.9s linear infinite" }} />
        </div>
      ) : filtered.length === 0 ? (
        <div style={{ textAlign: "center", padding: "56px 0", opacity: 0.6 }}>
          <div style={{ fontSize: 48 }}>💰</div>
          <p style={{ color: "#9898b8", marginTop: 12 }}>No expenses logged yet. Add your first one!</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {filtered.map((exp, i) => {
            const d = new Date(exp.created_at);
            const dateStr = d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
            const bg = CATEGORY_COLORS[exp.category] || "#f0f0f0";
            return (
              <div key={exp.id} style={{
                background: "#fff", borderRadius: 14, padding: "14px 16px",
                display: "flex", alignItems: "center", gap: 14,
                boxShadow: "0 1px 8px rgba(124,111,160,0.06)",
                border: "1px solid rgba(124,111,160,0.07)",
                animation: `fadeUp 0.3s ease both`,
                animationDelay: `${i * 0.03}s`,
                transition: "box-shadow 0.2s",
              }}
                onMouseEnter={e => e.currentTarget.style.boxShadow = "0 4px 20px rgba(124,111,160,0.12)"}
                onMouseLeave={e => e.currentTarget.style.boxShadow = "0 1px 8px rgba(124,111,160,0.06)"}
              >
                <div style={{ width: 42, height: 42, borderRadius: 12, background: bg, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, flexShrink: 0 }}>
                  {CATEGORY_ICONS[exp.category] || "💳"}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 700, color: "#1a1a2e", fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", display: "flex", alignItems: "center", gap: 6 }}>
                    {exp.note || exp.category}
                  </div>
                  <div style={{ fontSize: 11, color: "#9898b8", marginTop: 2 }}>{exp.category} · {dateStr}</div>
                </div>
                <div style={{ fontSize: 16, fontWeight: 800, color: "#7c6fa0", whiteSpace: "nowrap" }}>{formatINR(exp.amount)}</div>
                <button onClick={() => handleDelete(exp.id)} style={{
                  background: "#fff8f8", border: "1px solid #fad5d5", borderRadius: 8,
                  padding: "6px 10px", color: "#e07070", fontSize: 12, cursor: "pointer",
                  fontFamily: "inherit", transition: "all 0.15s",
                }}
                  onMouseEnter={e => { e.target.style.background = "#fad5d5"; }}
                  onMouseLeave={e => { e.target.style.background = "#fff8f8"; }}
                >✕</button>
              </div>
            );
          })}
        </div>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}

const labelStyle = { display: "block", fontSize: 11, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 6 };
const inputStyle = {
  width: "100%", padding: "10px 14px", borderRadius: 10, border: "1.5px solid #e8e4f5",
  fontSize: 13, color: "#1a1a2e", background: "#faf9ff", outline: "none",
  fontFamily: "inherit", boxSizing: "border-box", transition: "border 0.2s",
};