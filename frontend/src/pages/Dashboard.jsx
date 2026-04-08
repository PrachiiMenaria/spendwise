// fenora/frontend/src/pages/Dashboard.jsx
// ── PHASE 2: Enhanced Dashboard with Budget Suggest + Streak ─────
import { useState, useEffect } from "react";

const API = "http://localhost:5000";
const PIE_COLORS = ["#7c6fa0","#a89cc8","#c9a96e","#6aaa8a","#e07070","#88aacc","#c8a8c0","#8ac8a8"];

function formatINR(n) {
  return "₹" + Number(n || 0).toLocaleString("en-IN");
}

/* ─── Mini Pie Chart ─────────────────────────────────────────── */
function PieChart({ data }) {
  if (!data || Object.keys(data).length === 0)
    return <EmptyState icon="📊" text="No expense data yet" />;

  const total = Object.values(data).reduce((a, b) => a + b, 0);
  const entries = Object.entries(data).slice(0, 8);
  let cumAngle = -90;
  const cx = 70, cy = 70, r = 56, hole = 32;

  const slices = entries.map(([cat, val], i) => {
    const pct = val / total;
    const angle = pct * 360;
    const start = cumAngle;
    cumAngle += angle;
    const end = cumAngle;
    const toRad = (a) => (a * Math.PI) / 180;
    const x1 = cx + r * Math.cos(toRad(start)), y1 = cy + r * Math.sin(toRad(start));
    const x2 = cx + r * Math.cos(toRad(end)),   y2 = cy + r * Math.sin(toRad(end));
    const xi1 = cx + hole * Math.cos(toRad(start)), yi1 = cy + hole * Math.sin(toRad(start));
    const xi2 = cx + hole * Math.cos(toRad(end)),   yi2 = cy + hole * Math.sin(toRad(end));
    const large = angle > 180 ? 1 : 0;
    return {
      cat, val, pct, color: PIE_COLORS[i % PIE_COLORS.length],
      path: `M${xi1},${yi1} L${x1},${y1} A${r},${r} 0 ${large},1 ${x2},${y2} L${xi2},${yi2} A${hole},${hole} 0 ${large},0 ${xi1},${yi1} Z`,
    };
  });

  return (
    <div style={{ display: "flex", gap: 20, alignItems: "center", flexWrap: "wrap" }}>
      <svg width="140" height="140" viewBox="0 0 140 140" style={{ flexShrink: 0 }}>
        <defs><filter id="ps"><feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.12"/></filter></defs>
        {slices.map((s, i) => (
          <path key={i} d={s.path} fill={s.color} stroke="#fff" strokeWidth="2.5" filter="url(#ps)">
            <title>{s.cat}: {formatINR(s.val)} ({(s.pct * 100).toFixed(0)}%)</title>
          </path>
        ))}
        <text x="70" y="66" textAnchor="middle" fontSize="9" fill="#9898b8" fontFamily="DM Sans, sans-serif" fontWeight="600">TOTAL</text>
        <text x="70" y="80" textAnchor="middle" fontSize="11" fill="#1a1a2e" fontWeight="800" fontFamily="DM Sans, sans-serif">{formatINR(total)}</text>
      </svg>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 7 }}>
        {slices.map((s, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: s.color, flexShrink: 0 }} />
            <span style={{ fontSize: 11, color: "#555", flex: 1 }}>{s.cat}</span>
            <span style={{ fontSize: 11, fontWeight: 700, color: "#1a1a2e" }}>{(s.pct * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Line Chart ─────────────────────────────────────────────── */
function LineChart({ data }) {
  const entries = Object.entries(data || {}).slice(-6);
  if (entries.length === 0) return <EmptyState icon="📈" text="Not enough data yet" />;

  const values = entries.map(([, v]) => v);
  const avg = values.reduce((a, b) => a + b, 0) / values.length;
  const last = values[values.length - 1];
  const predicted = Math.round((avg * 0.6 + last * 0.4) * 1.05);
  const allValues = [...values, predicted];
  const max = Math.max(...allValues, 1);
  const W = 300, H = 100, pad = 14;

  const pts = entries.map(([, v], i) => {
    const x = pad + (i / (entries.length)) * (W - pad * 2);
    const y = H - pad - ((v / max) * (H - pad * 2));
    return [x, y];
  });
  const predX = pad + (entries.length / entries.length) * (W - pad * 2);
  const predY = H - pad - ((predicted / max) * (H - pad * 2));
  const polyline = pts.map(([x, y]) => `${x},${y}`).join(" ");
  const area = `M${pts[0][0]},${H - 4} ` + pts.map(([x, y]) => `L${x},${y}`).join(" ") + ` L${pts[pts.length - 1][0]},${H - 4} Z`;

  const monthLabels = entries.map(([k]) => {
    const [y, m] = k.split("-");
    return new Date(parseInt(y), parseInt(m) - 1).toLocaleString("default", { month: "short" });
  });
  const now = new Date();
  const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1).toLocaleString("default", { month: "short" });

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H + 28}`} style={{ width: "100%", overflow: "visible" }}>
        <defs>
          <linearGradient id="lg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#7c6fa0" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#7c6fa0" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={area} fill="url(#lg)" />
        <line x1={pts[pts.length-1][0]} y1={pts[pts.length-1][1]} x2={predX} y2={predY}
          stroke="#c9a96e" strokeWidth="2" strokeDasharray="5,4" strokeLinecap="round" />
        <polyline points={polyline} fill="none" stroke="#7c6fa0" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        {pts.map(([x, y], i) => (
          <g key={i}>
            <circle cx={x} cy={y} r="4.5" fill="#7c6fa0" stroke="#fff" strokeWidth="2" />
            <text x={x} y={H + 20} textAnchor="middle" fontSize="9" fill="#9898b8" fontFamily="DM Sans">{monthLabels[i]}</text>
          </g>
        ))}
        <circle cx={predX} cy={predY} r="5" fill="#c9a96e" stroke="#fff" strokeWidth="2" />
        <text x={predX} y={H + 20} textAnchor="middle" fontSize="9" fill="#c9a96e" fontFamily="DM Sans" fontWeight="700">{nextMonth}*</text>
      </svg>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 4 }}>
        <div style={{ width: 20, height: 0, border: "1px dashed #c9a96e" }} />
        <span style={{ fontSize: 10, color: "#c9a96e", fontWeight: 600 }}>Predicted: {formatINR(predicted)} next month</span>
      </div>
    </div>
  );
}

/* ─── Budget vs Actual Bar ───────────────────────────────────── */
function BudgetBar({ spent, budget }) {
  const pct = budget > 0 ? Math.min((spent / budget) * 100, 100) : 0;
  const overBudget = spent > budget && budget > 0;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <span style={{ fontSize: 12, color: "#9898b8", fontWeight: 600 }}>Spent</span>
        <span style={{ fontSize: 12, color: "#9898b8", fontWeight: 600 }}>Budget</span>
      </div>
      <div style={{ display: "flex", gap: 10, alignItems: "flex-end", height: 80 }}>
        <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 11, fontWeight: 800, color: overBudget ? "#e07070" : "#7c6fa0" }}>{formatINR(spent)}</span>
          <div style={{ width: "100%", background: overBudget ? "linear-gradient(180deg,#e07070,#ff9999)" : "linear-gradient(180deg,#7c6fa0,#a89cc8)", borderRadius: "6px 6px 0 0", height: `${Math.min(pct, 100)}%` }} />
        </div>
        <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 11, fontWeight: 800, color: "#6aaa8a" }}>{formatINR(budget)}</span>
          <div style={{ width: "100%", background: "linear-gradient(180deg,#6aaa8a,#8ac8a8)", borderRadius: "6px 6px 0 0", height: "100%" }} />
        </div>
      </div>
      <div style={{ background: "#f0eef8", borderRadius: 100, height: 8, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: overBudget ? "linear-gradient(90deg,#e07070,#ff9999)" : "linear-gradient(90deg,#7c6fa0,#a89cc8)", borderRadius: 100, transition: "width 1.2s ease" }} />
      </div>
      <div style={{ fontSize: 11, color: overBudget ? "#e07070" : "#9898b8", textAlign: "center", fontWeight: 600 }}>
        {overBudget ? `⚠️ Over budget by ${formatINR(spent - budget)}` : `${pct.toFixed(0)}% used · ${formatINR(Math.max(0, budget - spent))} remaining`}
      </div>
    </div>
  );
}

/* ─── Wardrobe Utilization Bars ──────────────────────────────── */
function WardrobeBar({ data }) {
  if (!data || data.length === 0)
    return <EmptyState icon="👗" text="Add wardrobe items to see utilization" />;
  const max = Math.max(...data.map((d) => d.wear_count || 0), 1);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {data.slice(0, 6).map((item, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 11, color: "#666", minWidth: 110, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.name || item.item_name}</span>
          <div style={{ flex: 1, background: "#f0eef8", borderRadius: 100, height: 7, overflow: "hidden" }}>
            <div style={{ width: `${Math.max(((item.wear_count || 0) / max) * 100, item.wear_count === 0 ? 0 : 4)}%`, height: "100%", background: item.wear_count === 0 ? "#fad5d5" : `hsl(${260 + i * 18}, 40%, 65%)`, borderRadius: 100, transition: "width 0.8s ease" }} />
          </div>
          <span style={{ fontSize: 11, color: item.wear_count === 0 ? "#e07070" : "#7c6fa0", fontWeight: 700, minWidth: 28 }}>{item.wear_count || 0}×</span>
        </div>
      ))}
    </div>
  );
}

/* ─── Budget Suggest Widget ──────────────────────────────────── */
function BudgetSuggest({ data, onAccept }) {
  if (!data) return null;
  return (
    <div style={{ background: "linear-gradient(135deg,#fdf8e8,#fffbf4)", border: "1px solid #f5e4b8", borderRadius: 14, padding: "14px 16px" }}>
      <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
        <span style={{ fontSize: 22, flexShrink: 0 }}>💡</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#1a1a2e", marginBottom: 4 }}>Smart Budget Suggestion</div>
          <p style={{ fontSize: 12, color: "#6b6888", lineHeight: 1.6, margin: "0 0 10px" }}>{data.reason}</p>
          {data.suggested && (
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <span style={{ fontSize: 16, fontWeight: 900, color: "#c9a96e" }}>{formatINR(data.suggested)}<span style={{ fontSize: 11, fontWeight: 600, color: "#9898b8" }}>/month</span></span>
              {onAccept && (
                <button onClick={() => onAccept(data.suggested)} style={{
                  background: "#c9a96e", color: "#fff", border: "none", borderRadius: 100,
                  padding: "5px 14px", fontSize: 11, fontWeight: 700, cursor: "pointer", fontFamily: "inherit",
                }}>
                  Apply this budget
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── Savings Goals Widget ───────────────────────────────────── */
function SavingGoals({ goals, onAdd, onDelete, monthlyRemaining }) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", target: "", months: "2" });
  const [submitting, setSubmitting] = useState(false);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.name || !form.target) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/api/savings-goals`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ name: form.name, target_amount: parseFloat(form.target), months: parseInt(form.months) }),
      });
      if (res.ok) { setForm({ name: "", target: "", months: "2" }); setShowForm(false); onAdd(); }
    } catch (err) { console.error(err); }
    setSubmitting(false);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {goals.length === 0 && !showForm && (
        <div style={{ textAlign: "center", padding: "16px 0", opacity: 0.7 }}>
          <div style={{ fontSize: 32 }}>🎯</div>
          <p style={{ color: "#9898b8", fontSize: 12, marginTop: 6 }}>No savings goals yet.</p>
        </div>
      )}
      {goals.map((g, i) => {
        const monthlyNeed = g.target_amount / g.months;
        const canAchieve = monthlyRemaining >= monthlyNeed;
        const pct = Math.min(((g.saved_amount || 0) / g.target_amount) * 100, 100);
        return (
          <div key={g.id || i} style={{ background: "#faf9ff", borderRadius: 14, padding: "14px 16px", border: `1px solid ${canAchieve ? "rgba(106,170,138,0.2)" : "rgba(224,112,112,0.15)"}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#1a1a2e" }}>{g.name}</div>
                <div style={{ fontSize: 11, color: "#9898b8", marginTop: 2 }}>{formatINR(g.target_amount)} in {g.months} month{g.months > 1 ? "s" : ""}</div>
              </div>
              <button onClick={() => onDelete(g.id)} style={{ background: "none", border: "none", color: "#ccc", cursor: "pointer", fontSize: 14 }}>✕</button>
            </div>
            <div style={{ background: "#ece8f5", borderRadius: 100, height: 5, overflow: "hidden", marginBottom: 5 }}>
              <div style={{ width: `${pct}%`, height: "100%", background: pct >= 100 ? "#6aaa8a" : "linear-gradient(90deg,#7c6fa0,#a89cc8)", borderRadius: 100, transition: "width 1s ease" }} />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 10, color: "#9898b8" }}>{pct.toFixed(0)}% saved</span>
              <span style={{ fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 100, background: canAchieve ? "#eaf6ef" : "#fdf0f0", color: canAchieve ? "#6aaa8a" : "#e07070" }}>
                {canAchieve ? "✓ On track" : "⚠ Tight"}
              </span>
            </div>
          </div>
        );
      })}

      {showForm ? (
        <form onSubmit={handleAdd} style={{ background: "#faf9ff", borderRadius: 14, padding: "14px", border: "1.5px solid #e8e4f5", display: "flex", flexDirection: "column", gap: 10 }}>
          <input style={miniInput} placeholder="Goal name (e.g. New Laptop)" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <input style={miniInput} type="number" placeholder="Target ₹" value={form.target} onChange={e => setForm({ ...form, target: e.target.value })} required />
            <select style={miniInput} value={form.months} onChange={e => setForm({ ...form, months: e.target.value })}>
              {[1,2,3,4,5,6].map(m => <option key={m} value={m}>{m} month{m > 1 ? "s" : ""}</option>)}
            </select>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button type="submit" disabled={submitting} style={{ flex: 1, background: "linear-gradient(135deg,#7c6fa0,#a89cc8)", color: "#fff", border: "none", borderRadius: 10, padding: "9px", fontSize: 12, fontWeight: 700, cursor: "pointer", fontFamily: "inherit" }}>
              {submitting ? "Saving…" : "Set Goal"}
            </button>
            <button type="button" onClick={() => setShowForm(false)} style={{ background: "#f0eef8", border: "none", borderRadius: 10, padding: "9px 14px", color: "#7c6fa0", fontSize: 12, cursor: "pointer", fontFamily: "inherit" }}>Cancel</button>
          </div>
        </form>
      ) : (
        <button onClick={() => setShowForm(true)} style={{
          width: "100%", background: "transparent", border: "1.5px dashed #d0cce8",
          borderRadius: 12, padding: "10px", fontSize: 12, fontWeight: 600, color: "#9898b8",
          cursor: "pointer", fontFamily: "inherit", transition: "all 0.2s",
        }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = "#7c6fa0"; e.currentTarget.style.color = "#7c6fa0"; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = "#d0cce8"; e.currentTarget.style.color = "#9898b8"; }}
        >+ New Savings Goal</button>
      )}
    </div>
  );
}

function EmptyState({ icon, text }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "28px 0", opacity: 0.55 }}>
      <span style={{ fontSize: 32 }}>{icon}</span>
      <p style={{ color: "#9898b8", marginTop: 8, fontSize: 12 }}>{text}</p>
    </div>
  );
}

/* ─── Streak Mini Widget ─────────────────────────────────────── */
function StreakBadge({ streak }) {
  if (!streak) return null;
  const count = streak.streak || 0;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, background: count > 0 ? "#fdf8e8" : "#f8f6ff", borderRadius: 10, padding: "8px 12px", border: `1px solid ${count > 0 ? "#f5e4b8" : "#e8e4f5"}` }}>
      <span style={{ fontSize: 20 }}>{count >= 7 ? "🔥🔥" : count > 0 ? "🔥" : "💤"}</span>
      <div>
        <div style={{ fontSize: 14, fontWeight: 800, color: count > 0 ? "#c9a96e" : "#9898b8" }}>{count} day{count !== 1 ? "s" : ""}</div>
        <div style={{ fontSize: 10, color: "#9898b8" }}>Savings streak</div>
      </div>
    </div>
  );
}

/* ─── Main Dashboard ─────────────────────────────────────────── */
export default function Dashboard({ user }) {
  const [summary, setSummary] = useState(null);
  const [expSummary, setExpSummary] = useState(null);
  const [wardData, setWardData] = useState(null);
  const [aiData, setAiData] = useState(null);
  const [goals, setGoals] = useState([]);
  const [streak, setStreak] = useState(null);
  const [budgetSuggest, setBudgetSuggest] = useState(null);
  const [chatReply, setChatReply] = useState(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [applyingBudget, setApplyingBudget] = useState(false);

  const fetchGoals = async () => {
    try {
      const res = await fetch(`${API}/api/savings-goals`, { credentials: "include" });
      if (res.ok) { const d = await res.json(); setGoals(Array.isArray(d) ? d : []); }
    } catch {}
  };

  const deleteGoal = async (id) => {
    try {
      await fetch(`${API}/api/savings-goals/${id}`, { method: "DELETE", credentials: "include" });
      fetchGoals();
    } catch {}
  };

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      try {
        const [s, e, w, a, str, bs] = await Promise.all([
          fetch(`${API}/api/get-summary`, { credentials: "include" }).then(r => r.json()),
          fetch(`${API}/api/expense-summary`, { credentials: "include" }).then(r => r.json()),
          fetch(`${API}/api/wardrobe-data`, { credentials: "include" }).then(r => r.json()),
          fetch(`${API}/api/ai-analysis`, { credentials: "include" }).then(r => r.json()),
          fetch(`${API}/api/streak`, { credentials: "include" }).then(r => r.json()).catch(() => null),
          fetch(`${API}/api/suggest-budget`, { credentials: "include" }).then(r => r.json()).catch(() => null),
        ]);
        setSummary(s); setExpSummary(e); setWardData(w); setAiData(a);
        setStreak(str); setBudgetSuggest(bs);
      } catch (err) { console.error("Dashboard fetch error:", err); }
      finally { setLoading(false); }
    };
    fetchAll();
    fetchGoals();
  }, []);

  const askChat = async (key) => {
    setChatLoading(true); setChatReply(null);
    try {
      const res = await fetch(`${API}/api/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        credentials: "include", body: JSON.stringify({ question_key: key }),
      });
      setChatReply(await res.json());
    } catch (err) { console.error(err); }
    finally { setChatLoading(false); }
  };

  const handleApplyBudget = async (amount) => {
    setApplyingBudget(true);
    try {
      const res = await fetch(`${API}/api/update-budget`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        credentials: "include", body: JSON.stringify({ monthly_budget: amount }),
      });
      if (res.ok) {
        const s = await fetch(`${API}/api/get-summary`, { credentials: "include" }).then(r => r.json());
        setSummary(s);
        setBudgetSuggest(null); // Hide after applying
      }
    } catch {}
    setApplyingBudget(false);
  };

  if (loading) return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "60vh", gap: 14 }}>
      <div style={{ width: 40, height: 40, borderRadius: "50%", border: "4px solid #e8e4f3", borderTopColor: "#7c6fa0", animation: "spin 0.8s linear infinite" }} />
      <p style={{ color: "#9898b8", fontSize: 13 }}>Loading your dashboard…</p>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  );

  const budget = summary?.budget || 0;
  const spent = summary?.this_month_total || 0;
  const remaining = Math.max(0, budget - spent);
  const pct = budget > 0 ? Math.min((spent / budget) * 100, 100) : 0;
  const allInsights = [...(aiData?.expense_insights || []), ...(aiData?.wardrobe_insights || [])].slice(0, 4);

  const statCards = [
    { label: "Monthly Budget", value: formatINR(budget), sub: `${pct.toFixed(0)}% used`, icon: "💰", accent: "#7c6fa0", bar: true, pct, danger: pct > 85 },
    { label: "Spent This Month", value: formatINR(spent), sub: `${formatINR(remaining)} left`, icon: "📤", accent: pct > 85 ? "#e07070" : "#c9a96e" },
    { label: "Wardrobe Items", value: wardData?.total_items || 0, sub: `Value ${formatINR(wardData?.total_value || 0)}`, icon: "👗", accent: "#a89cc8" },
    { label: "Never Worn", value: summary?.never_worn_count || 0, sub: summary?.never_worn_count > 0 ? "sitting idle" : "All worn ✓", icon: "⚠️", accent: (summary?.never_worn_count || 0) > 0 ? "#e07070" : "#6aaa8a" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Greeting Banner */}
      <div style={{
        background: "linear-gradient(135deg, #7c6fa0 0%, #9b8ec0 50%, #a89cc8 100%)",
        borderRadius: 20, padding: "24px 28px", color: "#fff",
        position: "relative", overflow: "hidden",
        boxShadow: "0 8px 32px rgba(124,111,160,0.25)",
      }}>
        <div style={{ position: "absolute", top: -30, right: -30, width: 160, height: 160, borderRadius: "50%", background: "rgba(255,255,255,0.06)" }} />
        <div style={{ position: "absolute", bottom: -20, right: 80, width: 80, height: 80, borderRadius: "50%", background: "rgba(255,255,255,0.05)" }} />
        <div style={{ position: "relative", zIndex: 1 }}>
          <div style={{ fontSize: 12, opacity: 0.75, fontWeight: 600, letterSpacing: "0.5px", marginBottom: 6 }}>
            {new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" })}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
            <div>
              <h1 style={{ fontSize: 24, fontWeight: 900, margin: "0 0 4px", letterSpacing: "-0.5px" }}>
                Good {new Date().getHours() < 12 ? "morning" : new Date().getHours() < 17 ? "afternoon" : "evening"}, {user?.name?.split(" ")[0] || "there"} ✨
              </h1>
              <p style={{ fontSize: 13, opacity: 0.8, margin: 0 }}>
                {pct > 85 ? "⚠️ Budget running low — slow down spending!" : pct > 60 ? `You've used ${pct.toFixed(0)}% of this month's budget.` : "Your finances look healthy today! Keep it up 🎉"}
              </p>
            </div>
            <StreakBadge streak={streak} />
          </div>
          {pct > 0 && (
            <div style={{ marginTop: 14, background: "rgba(255,255,255,0.15)", borderRadius: 100, height: 6, overflow: "hidden", maxWidth: 300 }}>
              <div style={{ width: `${pct}%`, height: "100%", background: pct > 85 ? "#ff9999" : "rgba(255,255,255,0.9)", borderRadius: 100, transition: "width 1.2s ease" }} />
            </div>
          )}
        </div>
      </div>

      {/* Stat Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(155px, 1fr))", gap: 14 }}>
        {statCards.map((card, i) => (
          <div key={i} style={{
            background: "#fff", borderRadius: 18, padding: "18px 18px 14px",
            boxShadow: "0 2px 16px rgba(124,111,160,0.07)",
            border: "1px solid rgba(124,111,160,0.08)",
            position: "relative", overflow: "hidden",
            animation: `fadeUp 0.4s ease both`, animationDelay: `${i * 0.07}s`,
          }}>
            <div style={{ position: "absolute", top: 12, right: 14, fontSize: 20, opacity: 0.65 }}>{card.icon}</div>
            <div style={{ fontSize: 10, color: "#9898b8", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 6 }}>{card.label}</div>
            <div style={{ fontSize: 19, fontWeight: 800, color: card.accent, letterSpacing: "-0.5px" }}>{card.value}</div>
            <div style={{ fontSize: 11, color: "#b0aec8", marginTop: 4 }}>{card.sub}</div>
            {card.bar && (
              <div style={{ marginTop: 10, background: "#f0eef8", borderRadius: 100, height: 5, overflow: "hidden" }}>
                <div style={{ width: `${card.pct}%`, height: "100%", borderRadius: 100, background: card.danger ? "linear-gradient(90deg,#e07070,#ff9999)" : "linear-gradient(90deg,#7c6fa0,#a89cc8)", transition: "width 1.2s ease" }} />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Budget Suggest Banner */}
      {budgetSuggest && budget > 0 && Math.abs(budgetSuggest.suggested - budget) > 500 && (
        <BudgetSuggest data={budgetSuggest} onAccept={handleApplyBudget} />
      )}

      {/* Charts Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
        <div style={cardStyle}>
          <SectionTitle icon="🥧" label="Expense by Category" />
          <div style={{ marginTop: 16 }}><PieChart data={expSummary?.category_totals} /></div>
        </div>
        <div style={cardStyle}>
          <SectionTitle icon="📈" label="Monthly Trend + Forecast" />
          <div style={{ marginTop: 16 }}><LineChart data={expSummary?.monthly_totals} /></div>
        </div>
      </div>

      {/* Budget vs Actual + Wardrobe */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
        <div style={cardStyle}>
          <SectionTitle icon="🎯" label="Budget vs Actual" />
          <div style={{ marginTop: 16 }}><BudgetBar spent={spent} budget={budget} /></div>
        </div>
        <div style={cardStyle}>
          <SectionTitle icon="👚" label="Wardrobe Utilization" />
          <div style={{ marginTop: 16 }}>
            <WardrobeBar data={Array.isArray(wardData) ? wardData.map(i => ({ name: i.item_name, wear_count: i.wear_count })) : wardData?.utilization_data} />
          </div>
        </div>
      </div>

      {/* Savings Goals */}
      <div style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <SectionTitle icon="🏦" label="Goal-Based Saving" />
          <span style={{ fontSize: 11, color: "#9898b8", fontWeight: 600 }}>{formatINR(remaining)} available/month</span>
        </div>
        <SavingGoals goals={goals} onAdd={fetchGoals} onDelete={deleteGoal} monthlyRemaining={remaining} />
      </div>

      {/* AI Insights */}
      {allInsights.length > 0 && (
        <div>
          <SectionTitle icon="✦" label="AI Insights" />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 12, marginTop: 14 }}>
            {allInsights.map((ins, i) => (
              <div key={i} style={{
                background: ins.type === "danger" ? "#fff8f8" : ins.type === "success" ? "#f4fbf7" : ins.type === "warning" ? "#fffbf0" : "#f8f6ff",
                border: `1px solid ${ins.type === "danger" ? "#fad5d5" : ins.type === "success" ? "#b8e8cc" : ins.type === "warning" ? "#f5e4b8" : "#e0d8f5"}`,
                borderRadius: 14, padding: "14px 16px", display: "flex", gap: 12, alignItems: "flex-start",
                animation: `fadeUp 0.4s ease both`, animationDelay: `${i * 0.07}s`,
                transition: "transform 0.2s",
              }}
                onMouseEnter={e => e.currentTarget.style.transform = "translateY(-2px)"}
                onMouseLeave={e => e.currentTarget.style.transform = "translateY(0)"}
              >
                <span style={{ fontSize: 20, flexShrink: 0 }}>{ins.icon || "💡"}</span>
                <span style={{ fontSize: 12, color: "#3d3a52", lineHeight: 1.55 }}>{ins.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Smart Recommendations */}
      {aiData?.recommendations?.length > 0 && (
        <div>
          <SectionTitle icon="🎯" label="Smart Recommendations" />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 12, marginTop: 14 }}>
            {aiData.recommendations.map((rec, i) => (
              <div key={i} style={{
                background: "#fff", border: "1px solid #ece8f5", borderRadius: 16, padding: "16px 18px",
                boxShadow: "0 2px 12px rgba(124,111,160,0.07)",
                animation: `fadeUp 0.4s ease both`, animationDelay: `${i * 0.08}s`,
                transition: "box-shadow 0.2s, transform 0.2s",
              }}
                onMouseEnter={e => { e.currentTarget.style.boxShadow = "0 8px 24px rgba(124,111,160,0.13)"; e.currentTarget.style.transform = "translateY(-2px)"; }}
                onMouseLeave={e => { e.currentTarget.style.boxShadow = "0 2px 12px rgba(124,111,160,0.07)"; e.currentTarget.style.transform = "translateY(0)"; }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                  <span style={{ fontSize: 22 }}>{rec.icon || "💡"}</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: "#1a1a2e" }}>{rec.title}</div>
                    <span style={{ fontSize: 9, padding: "2px 8px", borderRadius: 100, fontWeight: 700, background: rec.priority === "high" ? "#fdf0f0" : rec.priority === "medium" ? "#fdf6e8" : "#f0f8f3", color: rec.priority === "high" ? "#e07070" : rec.priority === "medium" ? "#c9a96e" : "#6aaa8a", display: "inline-block" }}>{rec.priority?.toUpperCase()}</span>
                  </div>
                </div>
                <p style={{ fontSize: 12, color: "#777", lineHeight: 1.55, margin: 0 }}>{rec.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Chat widget */}
      <div style={{ ...cardStyle, background: "linear-gradient(135deg, #faf9ff 0%, #fff 100%)" }}>
        <SectionTitle icon="🤖" label="Ask Fenora AI" />
        <p style={{ fontSize: 12, color: "#9898b8", marginTop: 4, marginBottom: 14 }}>Get a personalised answer about your finances</p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {[
            { key: "budget", label: "🎯 Is my budget okay?" },
            { key: "reduce", label: "✂️ How to reduce spending?" },
            { key: "avoid", label: "🚫 What to avoid buying?" },
          ].map(({ key, label }) => (
            <button key={key} onClick={() => askChat(key)} style={{
              background: "#fff", border: "1.5px solid #ddd9f0", borderRadius: 100,
              padding: "8px 18px", fontSize: 12, fontWeight: 600, color: "#7c6fa0",
              cursor: "pointer", transition: "all 0.2s", fontFamily: "inherit",
            }}
              onMouseEnter={e => { e.currentTarget.style.background = "#7c6fa0"; e.currentTarget.style.color = "#fff"; e.currentTarget.style.borderColor = "#7c6fa0"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "#fff"; e.currentTarget.style.color = "#7c6fa0"; e.currentTarget.style.borderColor = "#ddd9f0"; }}
            >{label}</button>
          ))}
        </div>
        {chatLoading && (
          <div style={{ marginTop: 14, display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 18, height: 18, borderRadius: "50%", border: "3px solid #e8e4f3", borderTopColor: "#7c6fa0", animation: "spin 0.9s linear infinite" }} />
            <span style={{ fontSize: 12, color: "#9898b8" }}>Thinking…</span>
          </div>
        )}
        {chatReply && (
          <div style={{ marginTop: 14, background: "#fff", border: "1px solid #e0d8f5", borderRadius: 14, padding: "14px 16px", animation: "fadeUp 0.3s ease" }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: "#7c6fa0", letterSpacing: "0.5px", marginBottom: 6 }}>FENORA SAYS</div>
            <p style={{ fontSize: 13, color: "#3d3a52", lineHeight: 1.6, margin: 0 }}>{chatReply.reply}</p>
          </div>
        )}
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}

const cardStyle = { background: "#fff", borderRadius: 18, padding: "20px 22px", boxShadow: "0 2px 16px rgba(124,111,160,0.08)", border: "1px solid rgba(124,111,160,0.08)" };

function SectionTitle({ icon, label }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <span style={{ fontSize: 16 }}>{icon}</span>
      <span style={{ fontSize: 15, fontWeight: 700, color: "#1a1a2e" }}>{label}</span>
    </div>
  );
}

const miniInput = {
  width: "100%", padding: "9px 12px", borderRadius: 10, border: "1.5px solid #e8e4f5",
  fontSize: 12, color: "#1a1a2e", background: "#fff", outline: "none",
  fontFamily: "inherit", boxSizing: "border-box",
};