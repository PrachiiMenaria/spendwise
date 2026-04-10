// fenora/frontend/src/pages/Insights.jsx — FIXED
// All APIs wired to real backend data, proper loading/error states, no fake defaults
import { useState, useEffect, useRef } from "react";

const API = "http://localhost:5000";

function formatINR(n) {
  return "₹" + Number(n || 0).toLocaleString("en-IN");
}

// ── Mini Donut Chart ─────────────────────────────────────────────
function DonutChart({ data }) {
  if (!data || Object.keys(data).length === 0) return (
    <div style={{ textAlign: "center", padding: "20px 0", color: "#b0aec8", fontSize: 12 }}>No expense data yet — log some spending!</div>
  );
  const COLORS = ["#6d4fc2","#f0803c","#3db88a","#e05c7d","#4a9ede","#c9a96e","#8ac8a8","#c8a8c0"];
  const total = Object.values(data).reduce((a, b) => a + b, 0);
  if (total === 0) return null;
  const entries = Object.entries(data).slice(0, 8);
  let cumAngle = -90;
  const cx = 60, cy = 60, r = 48, hole = 26;
  const slices = entries.map(([cat, val], i) => {
    const pct = val / total;
    const angle = pct * 360;
    const start = cumAngle; cumAngle += angle; const end = cumAngle;
    const toRad = a => (a * Math.PI) / 180;
    const x1 = cx + r * Math.cos(toRad(start)), y1 = cy + r * Math.sin(toRad(start));
    const x2 = cx + r * Math.cos(toRad(end)), y2 = cy + r * Math.sin(toRad(end));
    const xi1 = cx + hole * Math.cos(toRad(start)), yi1 = cy + hole * Math.sin(toRad(start));
    const xi2 = cx + hole * Math.cos(toRad(end)), yi2 = cy + hole * Math.sin(toRad(end));
    return { cat, val, pct, color: COLORS[i % COLORS.length], path: `M${xi1},${yi1} L${x1},${y1} A${r},${r} 0 ${angle > 180 ? 1 : 0},1 ${x2},${y2} L${xi2},${yi2} A${hole},${hole} 0 ${angle > 180 ? 1 : 0},0 ${xi1},${yi1} Z` };
  });
  return (
    <div style={{ display: "flex", gap: 20, alignItems: "center" }}>
      <svg width="120" height="120" viewBox="0 0 120 120" style={{ flexShrink: 0 }}>
        {slices.map((s, i) => <path key={i} d={s.path} fill={s.color} stroke="#fff" strokeWidth="2"><title>{s.cat}: {formatINR(s.val)}</title></path>)}
        <text x="60" y="56" textAnchor="middle" fontSize="8" fill="#888">TOTAL</text>
        <text x="60" y="70" textAnchor="middle" fontSize="10" fill="#1a1a2e" fontWeight="800">{formatINR(total)}</text>
      </svg>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 5 }}>
        {slices.map((s, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 7 }}>
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: s.color, flexShrink: 0 }} />
            <span style={{ fontSize: 10.5, color: "#555", flex: 1 }}>{s.cat}</span>
            <span style={{ fontSize: 10.5, fontWeight: 700 }}>{(s.pct * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Mood Chart ───────────────────────────────────────────────────
function MoodChart({ data, counts }) {
  const MOODS = [
    { key: "happy", emoji: "😊", label: "Happy", color: "#3db88a" },
    { key: "sad", emoji: "😔", label: "Sad", color: "#4a9ede" },
    { key: "stressed", emoji: "😤", label: "Stressed", color: "#e05c7d" },
    { key: "neutral", emoji: "😑", label: "Neutral", color: "#c9a96e" },
    { key: "excited", emoji: "🤩", label: "Excited", color: "#6d4fc2" },
    { key: "bored", emoji: "😒", label: "Bored", color: "#a89cc8" },
  ];
  if (!data || Object.keys(data).length === 0) return (
    <div style={{ textAlign: "center", padding: "20px", color: "#b0aec8", fontSize: 12 }}>
      Select a mood when adding expenses to see patterns here 😊
    </div>
  );
  const maxVal = Math.max(...MOODS.map(m => data[m.key] || 0), 1);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {MOODS.filter(m => data[m.key] > 0).map(m => (
        <div key={m.key} style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 18, flexShrink: 0 }}>{m.emoji}</span>
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
              <span style={{ fontSize: 11, fontWeight: 600, color: "#3d3a52" }}>{m.label}</span>
              <span style={{ fontSize: 11, fontWeight: 700, color: m.color }}>{formatINR(data[m.key])}</span>
            </div>
            <div style={{ height: 6, background: "#f0edf8", borderRadius: 100, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${(data[m.key] / maxVal) * 100}%`, background: m.color, borderRadius: 100, transition: "width 0.8s ease" }} />
            </div>
            {counts && counts[m.key] && (
              <div style={{ fontSize: 9, color: "#b0aec8", marginTop: 2 }}>{counts[m.key]} transactions · avg {formatINR(Math.round(data[m.key] / counts[m.key]))}/transaction</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Spending Heatmap ──────────────────────────────────────────────
function SpendingHeatmap({ data }) {
  if (!data || data.length === 0) return (
    <div style={{ textAlign: "center", padding: "20px", color: "#b0aec8", fontSize: 12 }}>Log expenses to see your spending calendar 📅</div>
  );
  const COLORS = { 0: "#f0edf8", 1: "#c3b8e8", 2: "#9c89d4", 3: "#7355c2", 4: "#4d2a9e" };
  const weeks = [];
  let currentWeek = [];
  const firstDay = new Date(data[0].date).getDay();
  for (let i = 0; i < firstDay; i++) currentWeek.push(null);
  data.forEach(d => {
    currentWeek.push(d);
    if (currentWeek.length === 7) { weeks.push(currentWeek); currentWeek = []; }
  });
  if (currentWeek.length > 0) weeks.push(currentWeek);
  return (
    <div style={{ overflowX: "auto" }}>
      <div style={{ display: "flex", gap: 3 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 3, marginRight: 4 }}>
          {["S","M","T","W","T","F","S"].map((d, i) => (
            <div key={i} style={{ height: 12, fontSize: 7.5, color: "#b0aec8", fontWeight: 600, lineHeight: "12px", visibility: i % 2 === 0 ? "visible" : "hidden" }}>{d}</div>
          ))}
        </div>
        {weeks.map((week, wi) => (
          <div key={wi} style={{ display: "flex", flexDirection: "column", gap: 3 }}>
            {Array.from({ length: 7 }, (_, di) => {
              const cell = week[di];
              if (!cell) return <div key={di} style={{ width: 12, height: 12 }} />;
              return (
                <div key={di} title={`${cell.date}: ${formatINR(cell.amount)}`} style={{ width: 12, height: 12, borderRadius: 2, background: COLORS[cell.level] || COLORS[0], cursor: "default", transition: "transform 0.1s" }}
                  onMouseEnter={e => e.currentTarget.style.transform = "scale(1.4)"}
                  onMouseLeave={e => e.currentTarget.style.transform = "scale(1)"}
                />
              );
            })}
          </div>
        ))}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 5, marginTop: 8, justifyContent: "flex-end" }}>
        <span style={{ fontSize: 8, color: "#b0aec8" }}>Less</span>
        {[0,1,2,3,4].map(l => <div key={l} style={{ width: 10, height: 10, borderRadius: 2, background: COLORS[l] }} />)}
        <span style={{ fontSize: 8, color: "#b0aec8" }}>More</span>
      </div>
    </div>
  );
}

// ── Loading Spinner ───────────────────────────────────────────────
function Spinner() {
  return (
    <div style={{ display: "flex", justifyContent: "center", padding: "24px 0" }}>
      <div style={{ width: 28, height: 28, borderRadius: "50%", border: "3px solid #e8e4f3", borderTopColor: "#7c6fa0", animation: "spin 0.8s linear infinite" }} />
    </div>
  );
}

// ── Inline chat within Insights ───────────────────────────────────
function InsightsChat() {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Ask me anything about your budget, spending, or wardrobe. Try: 'Can I afford ₹5000?' or 'How to reduce my food spending?'" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async (text) => {
    if (!text.trim() || loading) return;
    setMessages(prev => [...prev, { role: "user", text }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ message: text, question_key: text }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "assistant", text: data.reply || "Something went wrong." }]);
    } catch {
      setMessages(prev => [...prev, { role: "assistant", text: "Couldn't reach the server. Check if the backend is running." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ maxHeight: 240, overflowY: "auto", display: "flex", flexDirection: "column", gap: 10, padding: "4px 0" }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: msg.role === "user" ? "flex-end" : "flex-start" }}>
            <div style={{
              maxWidth: "88%", padding: "10px 14px",
              borderRadius: msg.role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
              background: msg.role === "user" ? "linear-gradient(135deg,#6b5fa0,#9b8ec8)" : "#f8f6ff",
              color: msg.role === "user" ? "#fff" : "#3d3a52",
              fontSize: 12.5, lineHeight: 1.6,
              border: msg.role === "assistant" ? "1px solid #e8e4f5" : "none",
            }}>{msg.text}</div>
          </div>
        ))}
        {loading && (
          <div style={{ display: "flex", gap: 5, padding: "8px 12px", background: "#f8f6ff", borderRadius: "16px 16px 16px 4px", width: "fit-content" }}>
            {[0,1,2].map(i => <div key={i} style={{ width: 6, height: 6, borderRadius: "50%", background: "#9b8ec8", animation: "bounce 1.2s ease-in-out infinite", animationDelay: `${i*0.2}s` }} />)}
          </div>
        )}
        <div ref={endRef} />
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter") send(input); }}
          placeholder="Ask me anything…"
          style={{ flex: 1, padding: "10px 14px", borderRadius: 12, border: "1.5px solid #e8e4f5", fontSize: 13, fontFamily: "inherit", color: "#18182e", outline: "none", background: "#faf9ff" }}
          onFocus={e => e.target.style.borderColor = "#7c6fa0"}
          onBlur={e => e.target.style.borderColor = "#e8e4f5"}
        />
        <button onClick={() => send(input)} disabled={!input.trim() || loading} style={{
          background: input.trim() ? "linear-gradient(135deg,#7c6fa0,#a89cc8)" : "#f0eef8",
          color: input.trim() ? "#fff" : "#b0aec8",
          border: "none", borderRadius: 12, padding: "10px 18px",
          fontSize: 13, fontWeight: 700, cursor: input.trim() ? "pointer" : "default",
          fontFamily: "inherit",
        }}>Ask →</button>
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {["Can I afford ₹2000?", "Reduce food spending", "Budget status?", "What to avoid?"].map(s => (
          <button key={s} onClick={() => send(s)} style={{
            padding: "5px 12px", borderRadius: 100, fontSize: 11, fontWeight: 600,
            background: "#f5f3fc", border: "1px solid rgba(107,95,160,0.15)",
            color: "#7c6fa0", cursor: "pointer", fontFamily: "inherit",
          }}>{s}</button>
        ))}
      </div>
    </div>
  );
}

// ── Section Card ──────────────────────────────────────────────────
function SCard({ title, icon, children, loading: isLoading }) {
  return (
    <div style={{ background: "#fff", borderRadius: 18, padding: "20px 22px", boxShadow: "0 2px 16px rgba(124,111,160,0.08)", border: "1px solid rgba(124,111,160,0.08)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
        <span style={{ fontSize: 18 }}>{icon}</span>
        <span style={{ fontSize: 15, fontWeight: 700, color: "#1a1a2e" }}>{title}</span>
      </div>
      {isLoading ? <Spinner /> : children}
    </div>
  );
}

// ── Main Insights Page ────────────────────────────────────────────
export default function Insights() {
  const [data, setData] = useState({
    summary: null,
    expSummary: null,
    aiData: null,
    wardData: null,
    heatmap: [],
    streak: null,
    personality: null,
    weeklyReport: null,
    moodData: null,
  });
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);

      // Fetch all APIs in parallel, handle failures individually
      const safe = async (key, url) => {
        try {
          const res = await fetch(url, { credentials: "include" });
          if (!res.ok) throw new Error(`${res.status}`);
          return [key, await res.json()];
        } catch (e) {
          setErrors(prev => ({ ...prev, [key]: e.message }));
          return [key, null];
        }
      };

      const results = await Promise.all([
        safe("summary", `${API}/api/get-summary`),
        safe("expSummary", `${API}/api/expense-summary`),
        safe("aiData", `${API}/api/ai-analysis`),
        safe("wardData", `${API}/api/wardrobe-data`),
        safe("heatmap", `${API}/api/heatmap?days=90`),
        safe("streak", `${API}/api/streak`),
        safe("personality", `${API}/api/personality`),
        safe("weeklyReport", `${API}/api/weekly-report`),
        safe("moodData", `${API}/api/mood-analytics`),
      ]);

      const newData = {};
      for (const [key, val] of results) {
        newData[key] = val;
      }
      setData(newData);
      setLoading(false);
    };

    fetchAll();
  }, []);

  const { summary, expSummary, aiData, wardData, heatmap, streak, personality, weeklyReport, moodData } = data;
  const budget = summary?.budget || 0;
  const spent = summary?.this_month_total || 0;
  const pct = budget > 0 ? Math.min((spent / budget) * 100, 100) : 0;

  if (loading) return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "60vh", gap: 14 }}>
      <div style={{ width: 40, height: 40, borderRadius: "50%", border: "4px solid #e8e4f3", borderTopColor: "#7c6fa0", animation: "spin 0.8s linear infinite" }} />
      <p style={{ color: "#9898b8", fontSize: 13 }}>Loading your insights…</p>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: "#1a1a2e", margin: 0, letterSpacing: "-0.5px" }}>AI Insights 🤖</h1>
        <p style={{ color: "#9898b8", marginTop: 4, fontSize: 13 }}>Data-driven analysis of your spending, wardrobe & behavior</p>
      </div>

      {/* Personality Card */}
      {personality && personality.label && (
        <div style={{
          background: `linear-gradient(135deg, ${personality.color || "#7c6fa0"}22, ${personality.color || "#7c6fa0"}08)`,
          border: `1px solid ${personality.color || "#7c6fa0"}30`,
          borderRadius: 18, padding: "20px 22px",
        }}>
          <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ fontSize: 42 }}>{personality.icon || "💡"}</div>
            <div>
              <div style={{ fontSize: 11, color: "#9898b8", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 4 }}>Your Spending Personality</div>
              <div style={{ fontSize: 18, fontWeight: 800, color: "#1a1a2e", marginBottom: 4 }}>{personality.label}</div>
              <div style={{ fontSize: 12, color: "#6b6888", maxWidth: 400 }}>{personality.description}</div>
            </div>
          </div>
        </div>
      )}

      {/* Budget overview */}
      {budget > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: 12 }}>
          {[
            { label: "Budget", value: formatINR(budget), color: "#7c6fa0", icon: "💰" },
            { label: "Spent", value: formatINR(spent), color: pct > 85 ? "#e07070" : "#c9a96e", icon: "📤" },
            { label: "Remaining", value: formatINR(Math.max(0, budget - spent)), color: "#6aaa8a", icon: "💚" },
            { label: "Used", value: `${pct.toFixed(0)}%`, color: pct > 85 ? "#e07070" : "#7c6fa0", icon: "📊" },
          ].map((s, i) => (
            <div key={i} style={{ background: "#fff", borderRadius: 16, padding: "14px 16px", boxShadow: "0 2px 12px rgba(124,111,160,0.07)", border: "1px solid rgba(124,111,160,0.08)", position: "relative", overflow: "hidden" }}>
              <div style={{ position: "absolute", top: 10, right: 12, fontSize: 18, opacity: 0.5 }}>{s.icon}</div>
              <div style={{ fontSize: 10, color: "#9898b8", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 4 }}>{s.label}</div>
              <div style={{ fontSize: 18, fontWeight: 800, color: s.color }}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Weekly Report — FIXED with real data */}
      {weeklyReport && (
        <SCard title="This Week" icon="📅">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 14 }}>
            <div style={{ background: "#f8f6ff", borderRadius: 12, padding: "12px", textAlign: "center" }}>
              <div style={{ fontSize: 10, color: "#9898b8", fontWeight: 700, textTransform: "uppercase", marginBottom: 4 }}>This Week</div>
              <div style={{ fontSize: 18, fontWeight: 900, color: "#7c6fa0" }}>{formatINR(weeklyReport.this_week_total || 0)}</div>
            </div>
            <div style={{ background: "#f8f6ff", borderRadius: 12, padding: "12px", textAlign: "center" }}>
              <div style={{ fontSize: 10, color: "#9898b8", fontWeight: 700, textTransform: "uppercase", marginBottom: 4 }}>Last Week</div>
              <div style={{ fontSize: 18, fontWeight: 900, color: "#9898b8" }}>{formatINR(weeklyReport.last_week_total || 0)}</div>
            </div>
            <div style={{ background: "#f8f6ff", borderRadius: 12, padding: "12px", textAlign: "center" }}>
              <div style={{ fontSize: 10, color: "#9898b8", fontWeight: 700, textTransform: "uppercase", marginBottom: 4 }}>Change</div>
              <div style={{ fontSize: 18, fontWeight: 900, color: (weeklyReport.change_pct || 0) > 0 ? "#e07070" : "#6aaa8a" }}>
                {(weeklyReport.change_pct || 0) > 0 ? "+" : ""}{weeklyReport.change_pct || 0}%
              </div>
            </div>
          </div>
          {weeklyReport.status && (
            <div style={{ background: "#faf9ff", borderRadius: 10, padding: "10px 14px", fontSize: 12, color: "#6b6888", border: "1px solid #e8e4f5" }}>
              {weeklyReport.status}
            </div>
          )}
          {weeklyReport.top_categories && weeklyReport.top_categories.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 8 }}>Top This Week</div>
              {weeklyReport.top_categories.map((c, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", fontSize: 12 }}>
                  <span style={{ color: "#3d3a52" }}>{c.category}</span>
                  <span style={{ fontWeight: 700, color: "#7c6fa0" }}>{formatINR(c.total)}</span>
                </div>
              ))}
            </div>
          )}
          {weeklyReport.this_week_total === 0 && weeklyReport.last_week_total === 0 && (
            <div style={{ color: "#b0aec8", fontSize: 12, textAlign: "center", padding: "8px 0" }}>No expenses logged this week yet.</div>
          )}
        </SCard>
      )}

      {/* Charts Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
        <SCard title="Spending by Category" icon="🥧">
          <DonutChart data={expSummary?.category_totals} />
        </SCard>

        {/* Streak */}
        <SCard title="Savings Streak" icon="🔥">
          {streak ? (
            <div style={{ textAlign: "center", padding: "8px 0" }}>
              <div style={{ fontSize: 52 }}>{(streak.streak || 0) >= 7 ? "🔥🔥" : (streak.streak || 0) > 0 ? "🔥" : "💤"}</div>
              <div style={{ fontSize: 32, fontWeight: 900, color: (streak.streak || 0) > 0 ? "#c9a96e" : "#9898b8", margin: "8px 0 4px" }}>{streak.streak || 0} days</div>
              <div style={{ fontSize: 12, color: "#9898b8" }}>Best: {streak.best_streak || 0} days</div>
              {streak.message && <div style={{ fontSize: 12, color: "#6b6888", marginTop: 10, background: "#faf9ff", borderRadius: 10, padding: "8px 12px", border: "1px solid #e8e4f5" }}>{streak.message}</div>}
              {streak.daily_budget > 0 && <div style={{ fontSize: 11, color: "#b0aec8", marginTop: 8 }}>Daily budget: {formatINR(streak.daily_budget)}</div>}
            </div>
          ) : <div style={{ color: "#b0aec8", fontSize: 12, textAlign: "center", padding: "20px 0" }}>Set a budget to track your streak!</div>}
        </SCard>
      </div>

      {/* Spending Heatmap */}
      <SCard title="90-Day Spending Calendar" icon="📆">
        <SpendingHeatmap data={heatmap} />
      </SCard>

      {/* Mood Analytics — FIXED: new endpoint */}
      <SCard title="Mood-Based Spending" icon="😊">
        {moodData ? (
          <>
            <MoodChart data={moodData.mood_totals} counts={moodData.mood_counts} />
            {moodData.insights && moodData.insights.length > 0 && (
              <div style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 8 }}>
                {moodData.insights.map((ins, i) => (
                  <div key={i} style={{ background: "#fdf8e8", border: "1px solid #f5e4b8", borderRadius: 10, padding: "10px 14px", fontSize: 12, color: "#6b6888" }}>{ins}</div>
                ))}
              </div>
            )}
            {Object.keys(moodData.mood_totals || {}).length === 0 && (
              <div style={{ color: "#b0aec8", fontSize: 12, textAlign: "center", padding: "12px 0" }}>
                Select a mood when adding expenses to unlock mood spending patterns!
              </div>
            )}
          </>
        ) : <div style={{ color: "#b0aec8", fontSize: 12, textAlign: "center", padding: "12px 0" }}>Tag your expenses with moods to see patterns here.</div>}
      </SCard>

      {/* AI Insights */}
      {aiData && (
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
            <span style={{ fontSize: 16 }}>✦</span>
            <span style={{ fontSize: 15, fontWeight: 700, color: "#1a1a2e" }}>AI Insights</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 12 }}>
            {[...(aiData.expense_insights || []), ...(aiData.wardrobe_insights || [])].map((ins, i) => (
              <div key={i} style={{
                background: ins.type === "danger" ? "#fff8f8" : ins.type === "success" ? "#f4fbf7" : ins.type === "warning" ? "#fffbf0" : "#f8f6ff",
                border: `1px solid ${ins.type === "danger" ? "#fad5d5" : ins.type === "success" ? "#b8e8cc" : ins.type === "warning" ? "#f5e4b8" : "#e0d8f5"}`,
                borderRadius: 14, padding: "14px 16px", display: "flex", gap: 12, alignItems: "flex-start",
                animation: `fadeUp 0.4s ease both`, animationDelay: `${i * 0.07}s`,
              }}>
                <span style={{ fontSize: 20, flexShrink: 0 }}>{ins.icon || "💡"}</span>
                <span style={{ fontSize: 12, color: "#3d3a52", lineHeight: 1.55 }}>{ins.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {aiData?.recommendations?.length > 0 && (
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
            <span style={{ fontSize: 16 }}>🎯</span>
            <span style={{ fontSize: 15, fontWeight: 700, color: "#1a1a2e" }}>Smart Recommendations</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 12 }}>
            {aiData.recommendations.map((rec, i) => (
              <div key={i} style={{ background: "#fff", border: "1px solid #ece8f5", borderRadius: 16, padding: "16px 18px", boxShadow: "0 2px 12px rgba(124,111,160,0.07)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                  <span style={{ fontSize: 22 }}>{rec.icon}</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: "#1a1a2e" }}>{rec.title}</div>
                    <span style={{ fontSize: 9, padding: "2px 8px", borderRadius: 100, fontWeight: 700, background: rec.priority === "high" ? "#fdf0f0" : "#fdf6e8", color: rec.priority === "high" ? "#e07070" : "#c9a96e", display: "inline-block" }}>{rec.priority?.toUpperCase()}</span>
                  </div>
                </div>
                <p style={{ fontSize: 12, color: "#777", lineHeight: 1.55, margin: 0 }}>{rec.text}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Chat */}
      <SCard title="Ask Fenora AI" icon="🤖">
        <p style={{ fontSize: 12, color: "#9898b8", marginBottom: 16 }}>
          Ask anything — affordability, budget status, spending advice. All answers are based on your real data.
        </p>
        <InsightsChat />
      </SCard>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes bounce { 0%,80%,100%{ transform:scale(0.75); opacity:0.4; } 40%{ transform:scale(1.2); opacity:1; } }
      `}</style>
    </div>
  );
}