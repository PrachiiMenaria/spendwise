// fenora/frontend/src/pages/Insights.jsx
// ── PHASE 2: Full AI Intelligence Dashboard ──────────────────────
import { useState, useEffect, useRef } from "react";

const API = "http://localhost:5000";

function formatINR(n) {
  return "₹" + Number(n || 0).toLocaleString("en-IN");
}

// ── Spending Heatmap (GitHub-style) ──────────────────────────────
function SpendingHeatmap({ data }) {
  if (!data || data.length === 0)
    return <EmptyState icon="📅" text="Log expenses to see your spending calendar" />;

  const COLORS = {
    0: "#f0eef8",
    1: "#c8e6c9",
    2: "#81c784",
    3: "#e57373",
    4: "#c62828",
  };

  // Group into weeks
  const weeks = [];
  let currentWeek = [];
  const firstDay = new Date(data[0].date).getDay(); // 0=Sun
  for (let i = 0; i < firstDay; i++) currentWeek.push(null);
  data.forEach((d, i) => {
    currentWeek.push(d);
    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  });
  if (currentWeek.length > 0) weeks.push(currentWeek);

  const monthLabels = [];
  let lastMonth = -1;
  weeks.forEach((w, wi) => {
    const d = w.find(Boolean);
    if (d) {
      const m = new Date(d.date).getMonth();
      if (m !== lastMonth) {
        monthLabels.push({ week: wi, label: new Date(d.date).toLocaleString("default", { month: "short" }) });
        lastMonth = m;
      }
    }
  });

  return (
    <div style={{ overflowX: "auto" }}>
      {/* Month labels */}
      <div style={{ display: "flex", gap: 3, marginBottom: 4, paddingLeft: 24 }}>
        {weeks.map((_, wi) => {
          const ml = monthLabels.find((m) => m.week === wi);
          return (
            <div key={wi} style={{ width: 13, fontSize: 8, color: "#9898b8", fontWeight: 600, flexShrink: 0, overflow: "visible", whiteSpace: "nowrap" }}>
              {ml ? ml.label : ""}
            </div>
          );
        })}
      </div>
      <div style={{ display: "flex", gap: 3 }}>
        {/* Day labels */}
        <div style={{ display: "flex", flexDirection: "column", gap: 3, marginRight: 4 }}>
          {["S", "M", "T", "W", "T", "F", "S"].map((d, i) => (
            <div key={i} style={{ height: 13, fontSize: 8, color: "#9898b8", fontWeight: 600, lineHeight: "13px", display: i % 2 === 0 ? "block" : "none" }}>
              {d}
            </div>
          ))}
        </div>
        {/* Grid */}
        {weeks.map((week, wi) => (
          <div key={wi} style={{ display: "flex", flexDirection: "column", gap: 3 }}>
            {Array.from({ length: 7 }, (_, di) => {
              const cell = week[di];
              if (!cell) return <div key={di} style={{ width: 13, height: 13 }} />;
              return (
                <div
                  key={di}
                  title={`${cell.date}: ${formatINR(cell.amount)}`}
                  style={{
                    width: 13, height: 13, borderRadius: 3,
                    background: COLORS[cell.level] || COLORS[0],
                    cursor: "default", flexShrink: 0,
                    transition: "transform 0.1s",
                  }}
                  onMouseEnter={e => e.currentTarget.style.transform = "scale(1.4)"}
                  onMouseLeave={e => e.currentTarget.style.transform = "scale(1)"}
                />
              );
            })}
          </div>
        ))}
      </div>
      {/* Legend */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 10, justifyContent: "flex-end" }}>
        <span style={{ fontSize: 9, color: "#9898b8" }}>Less</span>
        {[0, 1, 2, 3, 4].map((l) => (
          <div key={l} style={{ width: 11, height: 11, borderRadius: 2, background: COLORS[l] }} />
        ))}
        <span style={{ fontSize: 9, color: "#9898b8" }}>More</span>
      </div>
    </div>
  );
}

// ── Spending Personality Card ─────────────────────────────────────
function PersonalityCard({ data }) {
  if (!data || data.personality === "new_user") return (
    <div style={{ textAlign: "center", padding: "24px 0", opacity: 0.7 }}>
      <div style={{ fontSize: 40 }}>🌱</div>
      <p style={{ color: "#9898b8", fontSize: 13, marginTop: 8 }}>Log more expenses to discover your spending personality!</p>
    </div>
  );

  const scores = data.score_breakdown || {};
  const maxScore = Math.max(...Object.values(scores), 1);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {/* Main personality */}
      <div style={{
        background: `linear-gradient(135deg, ${data.color}18, ${data.color}08)`,
        border: `1px solid ${data.color}30`,
        borderRadius: 16, padding: "18px 20px",
        display: "flex", gap: 16, alignItems: "center",
      }}>
        <div style={{ fontSize: 44, flexShrink: 0 }}>{data.icon}</div>
        <div>
          <div style={{ fontSize: 18, fontWeight: 800, color: data.color, letterSpacing: "-0.5px" }}>{data.label}</div>
          <p style={{ fontSize: 12, color: "#6b6888", lineHeight: 1.6, margin: "6px 0 0" }}>{data.description}</p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 10 }}>
            {(data.traits || []).map((t, i) => (
              <span key={i} style={{ fontSize: 10, fontWeight: 600, padding: "3px 10px", borderRadius: 100, background: `${data.color}18`, color: data.color }}>
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>
      {/* Score bars */}
      {Object.entries(scores).map(([label, score]) => {
        const pct = (score / maxScore) * 100;
        const isActive = label === data.label;
        return (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: 11, color: isActive ? "#1a1a2e" : "#9898b8", fontWeight: isActive ? 700 : 500, minWidth: 110 }}>{label}</span>
            <div style={{ flex: 1, background: "#f0eef8", borderRadius: 100, height: 6, overflow: "hidden" }}>
              <div style={{ width: `${pct}%`, height: "100%", background: isActive ? data.color : "#d0cce8", borderRadius: 100, transition: "width 1s ease" }} />
            </div>
            <span style={{ fontSize: 10, color: "#9898b8", minWidth: 24, textAlign: "right" }}>{score}</span>
          </div>
        );
      })}
    </div>
  );
}

// ── Anomaly Alerts ────────────────────────────────────────────────
function AnomalyAlerts({ data }) {
  if (!data || data.length === 0) return (
    <div style={{ textAlign: "center", padding: "20px 0", opacity: 0.7 }}>
      <div style={{ fontSize: 32 }}>✅</div>
      <p style={{ color: "#9898b8", fontSize: 12, marginTop: 8 }}>No unusual activity detected this week.</p>
    </div>
  );

  const colors = {
    danger: { bg: "#fff8f8", border: "#fad5d5", color: "#e07070" },
    warning: { bg: "#fffbf0", border: "#f5e4b8", color: "#c9a96e" },
    info: { bg: "#f8f6ff", border: "#e0d8f5", color: "#7c6fa0" },
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {data.map((a, i) => {
        const c = colors[a.level] || colors.info;
        return (
          <div key={i} style={{ background: c.bg, border: `1px solid ${c.border}`, borderRadius: 12, padding: "12px 14px", display: "flex", gap: 12, alignItems: "flex-start" }}>
            <span style={{ fontSize: 20, flexShrink: 0 }}>{a.icon}</span>
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#1a1a2e", marginBottom: 3 }}>{a.title}</div>
              <div style={{ fontSize: 12, color: "#6b6888", lineHeight: 1.5 }}>{a.message}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Recurring Expenses ────────────────────────────────────────────
function RecurringExpenses({ data }) {
  if (!data || data.length === 0) return (
    <div style={{ textAlign: "center", padding: "20px 0", opacity: 0.7 }}>
      <div style={{ fontSize: 32 }}>🔄</div>
      <p style={{ color: "#9898b8", fontSize: 12, marginTop: 8 }}>No recurring expenses detected yet. Log more data!</p>
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {data.map((r, i) => (
        <div key={i} style={{
          display: "flex", alignItems: "center", gap: 12, padding: "12px 14px",
          background: r.is_due_soon ? "#fffbf0" : "#faf9ff",
          border: `1px solid ${r.is_due_soon ? "#f5e4b8" : "rgba(124,111,160,0.1)"}`,
          borderRadius: 12,
        }}>
          <div style={{ width: 36, height: 36, borderRadius: 10, background: r.is_due_soon ? "#fdf8e8" : "#f0eef8", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, flexShrink: 0 }}>
            {r.is_due_soon ? "⏰" : "🔄"}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#1a1a2e", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.note}</div>
            <div style={{ fontSize: 11, color: "#9898b8", marginTop: 2 }}>
              {r.frequency} · Next: {r.next_expected}
              {r.is_due_soon && <span style={{ color: "#c9a96e", fontWeight: 700 }}> · Due soon!</span>}
            </div>
          </div>
          <div style={{ fontSize: 14, fontWeight: 800, color: "#7c6fa0", whiteSpace: "nowrap" }}>
            {formatINR(r.avg_amount)}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Weekly Report Card ────────────────────────────────────────────
function WeeklyReport({ data }) {
  if (!data || data.error) return <EmptyState icon="📋" text="No weekly data yet." />;

  const changeUp = data.change_pct > 0;
  const pct = data.weekly_budget > 0 ? Math.min((data.this_week_total / data.weekly_budget) * 100, 100) : 0;
  const over = data.this_week_total > data.weekly_budget && data.weekly_budget > 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
        {[
          { label: "This Week", value: formatINR(data.this_week_total), sub: `${data.transactions_count} txns`, color: over ? "#e07070" : "#7c6fa0" },
          { label: "Last Week", value: formatINR(data.last_week_total), sub: "comparison", color: "#9898b8" },
          { label: "Change", value: `${changeUp ? "+" : ""}${data.change_pct?.toFixed(1)}%`, sub: changeUp ? "more spent" : "less spent", color: changeUp ? "#e07070" : "#6aaa8a" },
        ].map((s, i) => (
          <div key={i} style={{ background: "#faf9ff", borderRadius: 12, padding: "12px 14px" }}>
            <div style={{ fontSize: 9, color: "#9898b8", fontWeight: 700, textTransform: "uppercase", marginBottom: 4 }}>{s.label}</div>
            <div style={{ fontSize: 16, fontWeight: 800, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 10, color: "#b0aec8", marginTop: 2 }}>{s.sub}</div>
          </div>
        ))}
      </div>
      {/* Budget bar */}
      {data.weekly_budget > 0 && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#9898b8", marginBottom: 6 }}>
            <span>Weekly budget: {formatINR(data.weekly_budget)}</span>
            <span style={{ color: over ? "#e07070" : "#7c6fa0", fontWeight: 700 }}>{pct.toFixed(0)}%</span>
          </div>
          <div style={{ background: "#f0eef8", borderRadius: 100, height: 8, overflow: "hidden" }}>
            <div style={{ width: `${pct}%`, height: "100%", background: over ? "linear-gradient(90deg,#e07070,#ff9999)" : "linear-gradient(90deg,#7c6fa0,#a89cc8)", borderRadius: 100, transition: "width 1s ease" }} />
          </div>
        </div>
      )}
      {/* Top categories */}
      {data.categories?.length > 0 && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#9898b8", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.5px" }}>By Category</div>
          {data.categories.slice(0, 4).map((c, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 0", borderBottom: "1px solid #f0eef8" }}>
              <span style={{ fontSize: 12, color: "#3d3a52" }}>{c.category}</span>
              <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <span style={{ fontSize: 10, color: "#9898b8" }}>{c.count} txns</span>
                <span style={{ fontSize: 12, fontWeight: 700, color: "#7c6fa0" }}>{formatINR(c.total)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
      {/* Suggestions */}
      {data.suggestions?.map((s, i) => (
        <div key={i} style={{ background: "#f8f6ff", border: "1px solid #e0d8f5", borderRadius: 10, padding: "10px 12px", fontSize: 12, color: "#3d3a52", lineHeight: 1.5 }}>
          💡 {s}
        </div>
      ))}
    </div>
  );
}

// ── Savings Streak Widget ─────────────────────────────────────────
function SavingsStreak({ data }) {
  if (!data) return null;
  const streak = data.streak || 0;
  const best = data.best_streak || 0;

  const flames = Math.min(streak, 7);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, alignItems: "center", textAlign: "center", padding: "10px 0" }}>
      <div style={{ fontSize: 48, lineHeight: 1 }}>
        {streak === 0 ? "💤" : streak >= 7 ? "🔥🔥" : "🔥"}
      </div>
      <div>
        <div style={{ fontSize: 36, fontWeight: 900, color: streak > 0 ? "#c9a96e" : "#9898b8", letterSpacing: "-1px" }}>
          {streak}
          <span style={{ fontSize: 16, fontWeight: 600, color: "#9898b8", marginLeft: 4 }}>days</span>
        </div>
        <div style={{ fontSize: 13, color: "#9898b8", marginTop: 4 }}>Current Streak</div>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        {[...Array(7)].map((_, i) => (
          <div key={i} style={{ width: 28, height: 28, borderRadius: "50%", background: i < flames ? "linear-gradient(135deg,#f5a623,#f76b1c)" : "#f0eef8", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, transition: "all 0.3s", transitionDelay: `${i * 0.05}s` }}>
            {i < flames ? "🔥" : ""}
          </div>
        ))}
      </div>
      <div style={{ fontSize: 12, color: "#9898b8" }}>
        {data.message}
      </div>
      {best > streak && (
        <div style={{ fontSize: 11, color: "#7c6fa0", fontWeight: 600 }}>Best: {best} days 🏆</div>
      )}
      {data.daily_budget > 0 && (
        <div style={{ background: "#faf9ff", borderRadius: 10, padding: "8px 16px", fontSize: 11, color: "#9898b8" }}>
          Daily budget target: {formatINR(data.daily_budget)}
        </div>
      )}
    </div>
  );
}

// ── Category Budget Caps ──────────────────────────────────────────
function CategoryBudgets({ data, onSetCap }) {
  const [editCat, setEditCat] = useState(null);
  const [capInput, setCapInput] = useState("");

  if (!data || data.length === 0)
    return <EmptyState icon="🏷️" text="Log expenses to see category budgets." />;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {data.map((c, i) => {
        const pct = c.cap ? Math.min(c.pct_used, 100) : 0;
        const alertColor = c.alert === "over" ? "#e07070" : c.alert === "warning" ? "#c9a96e" : "#7c6fa0";
        return (
          <div key={i}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: "#1a1a2e" }}>{c.category}</span>
                {c.alert && (
                  <span style={{ fontSize: 9, fontWeight: 800, padding: "2px 7px", borderRadius: 100, background: c.alert === "over" ? "#fdf0f0" : "#fffbf0", color: alertColor }}>
                    {c.alert === "over" ? "OVER" : "⚠"}
                  </span>
                )}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 11, color: alertColor, fontWeight: 700 }}>
                  {formatINR(c.spent)}{c.cap ? ` / ${formatINR(c.cap)}` : ""}
                </span>
                <button onClick={() => { setEditCat(c.category); setCapInput(c.cap || ""); }} style={{ background: "none", border: "none", cursor: "pointer", fontSize: 12, color: "#9898b8" }}>
                  ✏️
                </button>
              </div>
            </div>
            {c.cap ? (
              <div style={{ background: "#f0eef8", borderRadius: 100, height: 5, overflow: "hidden" }}>
                <div style={{ width: `${pct}%`, height: "100%", background: c.alert === "over" ? "linear-gradient(90deg,#e07070,#ff9999)" : c.alert === "warning" ? "linear-gradient(90deg,#c9a96e,#e8c88a)" : "linear-gradient(90deg,#7c6fa0,#a89cc8)", borderRadius: 100, transition: "width 1s ease" }} />
              </div>
            ) : (
              <div style={{ fontSize: 10, color: "#b0aec8" }}>No cap set — click ✏️ to set a limit</div>
            )}
            {editCat === c.category && (
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <input
                  type="number"
                  placeholder={`Cap for ${c.category} (₹)`}
                  value={capInput}
                  onChange={e => setCapInput(e.target.value)}
                  style={{ flex: 1, padding: "7px 12px", borderRadius: 8, border: "1.5px solid #e8e4f5", fontSize: 12, fontFamily: "inherit", outline: "none" }}
                />
                <button onClick={() => { onSetCap(c.category, parseFloat(capInput)); setEditCat(null); }} style={{ background: "linear-gradient(135deg,#7c6fa0,#a89cc8)", color: "#fff", border: "none", borderRadius: 8, padding: "7px 14px", fontSize: 12, cursor: "pointer", fontFamily: "inherit", fontWeight: 700 }}>
                  Set
                </button>
                <button onClick={() => setEditCap(null)} style={{ background: "#f0eef8", border: "none", borderRadius: 8, padding: "7px 10px", color: "#7c6fa0", fontSize: 12, cursor: "pointer" }}>
                  ✕
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Monthly Recap Card ────────────────────────────────────────────
function MonthlyRecap({ data }) {
  if (!data || data.error) return <EmptyState icon="📋" text="No monthly data available." />;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 900, color: "#1a1a2e", letterSpacing: "-0.5px" }}>{data.month_name}</div>
          <div style={{ fontSize: 12, color: "#9898b8", marginTop: 2 }}>{data.transactions_count} transactions</div>
        </div>
        <div style={{ background: `${data.verdict_color}18`, border: `1px solid ${data.verdict_color}30`, borderRadius: 100, padding: "4px 14px" }}>
          <span style={{ fontSize: 12, fontWeight: 800, color: data.verdict_color }}>{data.verdict}</span>
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        {[
          { label: "Total Spent", value: formatINR(data.total_spent), color: "#7c6fa0" },
          { label: "Budget", value: formatINR(data.budget), color: "#6aaa8a" },
          { label: "Saved", value: formatINR(data.savings), color: data.savings > 0 ? "#6aaa8a" : "#e07070" },
          { label: "vs Last Month", value: `${data.change_pct > 0 ? "+" : ""}${data.change_pct?.toFixed(1)}%`, color: data.change_pct > 0 ? "#e07070" : "#6aaa8a" },
        ].map((s, i) => (
          <div key={i} style={{ background: "#faf9ff", borderRadius: 12, padding: "12px 14px" }}>
            <div style={{ fontSize: 9, color: "#9898b8", fontWeight: 700, textTransform: "uppercase", marginBottom: 4 }}>{s.label}</div>
            <div style={{ fontSize: 16, fontWeight: 800, color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>
      {/* Top categories */}
      {data.top_categories?.length > 0 && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#9898b8", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.5px" }}>Top Categories</div>
          {data.top_categories.map((c, i) => {
            const pct = data.total_spent > 0 ? (c.total / data.total_spent) * 100 : 0;
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                <span style={{ fontSize: 11, color: "#3d3a52", minWidth: 90, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.category}</span>
                <div style={{ flex: 1, background: "#f0eef8", borderRadius: 100, height: 5, overflow: "hidden" }}>
                  <div style={{ width: `${pct}%`, height: "100%", background: `hsl(${260 + i * 25}, 40%, 65%)`, borderRadius: 100, transition: "width 1s ease" }} />
                </div>
                <span style={{ fontSize: 11, fontWeight: 700, color: "#7c6fa0", minWidth: 60, textAlign: "right" }}>{formatINR(c.total)}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── AI Insight Cards (existing style) ────────────────────────────
const TYPE_CONFIG = {
  danger: { bg: "#fff8f8", border: "#fad5d5", badge: "🚨 Alert", badgeBg: "#fdf0f0", badgeColor: "#e07070" },
  warning: { bg: "#fffbf0", border: "#f5e4b8", badge: "⚠️ Warning", badgeBg: "#fdf8e8", badgeColor: "#c9a96e" },
  success: { bg: "#f4fbf7", border: "#b8e8cc", badge: "✅ Good", badgeBg: "#eaf6ef", badgeColor: "#6aaa8a" },
  info: { bg: "#f8f6ff", border: "#e0d8f5", badge: "💡 Insight", badgeBg: "#f0eef8", badgeColor: "#7c6fa0" },
};

function InsightCard({ ins, index }) {
  const cfg = TYPE_CONFIG[ins.type] || TYPE_CONFIG.info;
  return (
    <div style={{ background: cfg.bg, border: `1px solid ${cfg.border}`, borderRadius: 16, padding: "16px 18px", display: "flex", gap: 12, alignItems: "flex-start", animation: `fadeUp 0.4s ease both`, animationDelay: `${index * 0.06}s`, transition: "transform 0.2s" }}
      onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px)"; }}
      onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; }}
    >
      <span style={{ fontSize: 24, flexShrink: 0, marginTop: 2 }}>{ins.icon || "💡"}</span>
      <div style={{ flex: 1 }}>
        <span style={{ fontSize: 10, fontWeight: 800, padding: "2px 9px", borderRadius: 100, background: cfg.badgeBg, color: cfg.badgeColor, display: "inline-block", marginBottom: 7 }}>{cfg.badge}</span>
        <p style={{ fontSize: 12, color: "#3d3a52", lineHeight: 1.6, margin: 0 }}>{ins.text || ins.message}</p>
      </div>
    </div>
  );
}

function EmptyState({ icon, text }) {
  return (
    <div style={{ textAlign: "center", padding: "28px 0", opacity: 0.55 }}>
      <span style={{ fontSize: 36 }}>{icon}</span>
      <p style={{ color: "#9898b8", marginTop: 8, fontSize: 12 }}>{text}</p>
    </div>
  );
}

// ── Card wrapper ──────────────────────────────────────────────────
function Card({ title, icon, children, badge, accentColor }) {
  return (
    <div style={{ background: "#fff", borderRadius: 20, padding: "20px 22px", boxShadow: "0 2px 16px rgba(124,111,160,0.08)", border: "1px solid rgba(124,111,160,0.08)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
        <span style={{ fontSize: 18 }}>{icon}</span>
        <span style={{ fontSize: 15, fontWeight: 700, color: "#1a1a2e" }}>{title}</span>
        {badge && <span style={{ marginLeft: "auto", fontSize: 10, fontWeight: 700, padding: "3px 10px", borderRadius: 100, background: "#f0eef8", color: "#7c6fa0" }}>{badge}</span>}
      </div>
      {children}
    </div>
  );
}

// ── Main Insights Page ────────────────────────────────────────────
export default function Insights() {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  // Data states
  const [aiData, setAiData] = useState(null);
  const [heatmap, setHeatmap] = useState([]);
  const [personality, setPersonality] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [recurring, setRecurring] = useState([]);
  const [streak, setStreak] = useState(null);
  const [weeklyReport, setWeeklyReport] = useState(null);
  const [catBudgets, setCatBudgets] = useState([]);
  const [monthlyRecap, setMonthlyRecap] = useState(null);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [ai, hm, pers, anom, rec, str, wk, cb, mr] = await Promise.all([
        fetch(`${API}/api/ai-analysis`, { credentials: "include" }).then(r => r.json()).catch(() => null),
        fetch(`${API}/api/heatmap`, { credentials: "include" }).then(r => r.json()).catch(() => []),
        fetch(`${API}/api/personality`, { credentials: "include" }).then(r => r.json()).catch(() => null),
        fetch(`${API}/api/anomalies`, { credentials: "include" }).then(r => r.json()).catch(() => []),
        fetch(`${API}/api/recurring`, { credentials: "include" }).then(r => r.json()).catch(() => []),
        fetch(`${API}/api/streak`, { credentials: "include" }).then(r => r.json()).catch(() => null),
        fetch(`${API}/api/weekly-report`, { credentials: "include" }).then(r => r.json()).catch(() => null),
        fetch(`${API}/api/category-budgets`, { credentials: "include" }).then(r => r.json()).catch(() => []),
        fetch(`${API}/api/monthly-recap`, { credentials: "include" }).then(r => r.json()).catch(() => null),
      ]);
      setAiData(ai);
      setHeatmap(Array.isArray(hm) ? hm : []);
      setPersonality(pers);
      setAnomalies(Array.isArray(anom) ? anom : []);
      setRecurring(Array.isArray(rec) ? rec : []);
      setStreak(str);
      setWeeklyReport(wk);
      setCatBudgets(Array.isArray(cb) ? cb : []);
      setMonthlyRecap(mr);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const handleSetCap = async (category, cap_amount) => {
    try {
      await fetch(`${API}/api/category-budgets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ category, cap_amount }),
      });
      const cb = await fetch(`${API}/api/category-budgets`, { credentials: "include" }).then(r => r.json());
      setCatBudgets(Array.isArray(cb) ? cb : []);
    } catch (err) { console.error(err); }
  };

  const allInsights = [...(aiData?.expense_insights || []), ...(aiData?.wardrobe_insights || [])];
  const recs = aiData?.recommendations || [];

  const tabs = [
    { id: "overview", label: "Overview", icon: "✦" },
    { id: "analytics", label: "Analytics", icon: "📊" },
    { id: "personality", label: "Personality", icon: "🎭" },
    { id: "recommendations", label: "Actions", icon: "🎯" },
  ];

  if (loading) return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "60vh", gap: 16 }}>
      <div style={{ width: 44, height: 44, borderRadius: "50%", border: "4px solid #e8e4f3", borderTopColor: "#7c6fa0", animation: "spin 0.9s linear infinite" }} />
      <p style={{ color: "#9898b8", fontSize: 14 }}>Generating your insights…</p>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Hero Header */}
      <div style={{ background: "linear-gradient(135deg, #7c6fa0 0%, #a89cc8 100%)", borderRadius: 20, padding: "24px 28px", color: "#fff", position: "relative", overflow: "hidden" }}>
        <div style={{ position: "absolute", top: -20, right: -20, width: 120, height: 120, borderRadius: "50%", background: "rgba(255,255,255,0.08)" }} />
        <div style={{ position: "absolute", bottom: -30, right: 60, width: 80, height: 80, borderRadius: "50%", background: "rgba(255,255,255,0.06)" }} />
        <div style={{ position: "relative", zIndex: 1 }}>
          <h1 style={{ fontSize: 22, fontWeight: 800, margin: "0 0 4px", letterSpacing: "-0.5px" }}>✦ AI Insights Engine</h1>
          <p style={{ fontSize: 12, opacity: 0.8, margin: "0 0 16px" }}>Personalised analysis of your spending & lifestyle</p>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            {[
              { label: "AI Insights", value: allInsights.length },
              { label: "Anomalies", value: anomalies.length },
              { label: "Recurring", value: recurring.length },
              { label: "Streak", value: `${streak?.streak || 0}d 🔥` },
            ].map((s, i) => (
              <div key={i} style={{ background: "rgba(255,255,255,0.15)", borderRadius: 10, padding: "8px 14px", backdropFilter: "blur(8px)" }}>
                <div style={{ fontSize: 16, fontWeight: 800 }}>{s.value}</div>
                <div style={{ fontSize: 10, opacity: 0.8 }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{
            padding: "8px 16px", borderRadius: 100, fontSize: 12, fontWeight: 600,
            border: activeTab === tab.id ? "none" : "1.5px solid #e8e4f5",
            background: activeTab === tab.id ? "linear-gradient(135deg,#7c6fa0,#a89cc8)" : "#fff",
            color: activeTab === tab.id ? "#fff" : "#9898b8",
            cursor: "pointer", transition: "all 0.2s", fontFamily: "inherit",
          }}>{tab.icon} {tab.label}</button>
        ))}
      </div>

      {/* OVERVIEW TAB */}
      {activeTab === "overview" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Anomaly alerts — show at top if any */}
          {anomalies.length > 0 && (
            <Card title="Anomaly Alerts" icon="🚨" badge={`${anomalies.length} detected`}>
              <AnomalyAlerts data={anomalies} />
            </Card>
          )}

          {/* AI Insights grid */}
          {allInsights.length > 0 && (
            <Card title="AI Insights" icon="🧠">
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
                {allInsights.map((ins, i) => <InsightCard key={i} ins={ins} index={i} />)}
              </div>
            </Card>
          )}

          {/* 2-col row */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
            <Card title="Weekly Report" icon="📋">
              <WeeklyReport data={weeklyReport} />
            </Card>
            <Card title="Savings Streak" icon="🔥">
              <SavingsStreak data={streak} />
            </Card>
          </div>

          {/* Monthly Recap */}
          <Card title="Monthly Recap" icon="📅">
            <MonthlyRecap data={monthlyRecap} />
          </Card>
        </div>
      )}

      {/* ANALYTICS TAB */}
      {activeTab === "analytics" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Heatmap */}
          <Card title="Spending Calendar" icon="📅" badge="Last 90 days">
            <SpendingHeatmap data={heatmap} />
          </Card>

          {/* Recurring + Category Budgets */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
            <Card title="Recurring Expenses" icon="🔄">
              <RecurringExpenses data={recurring} />
            </Card>
            <Card title="Category Budget Caps" icon="🏷️">
              <CategoryBudgets data={catBudgets} onSetCap={handleSetCap} />
            </Card>
          </div>
        </div>
      )}

      {/* PERSONALITY TAB */}
      {activeTab === "personality" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <Card title="Your Spending Personality" icon="🎭">
            <PersonalityCard data={personality} />
          </Card>
          {/* Wardrobe insights */}
          {(aiData?.wardrobe_insights || []).length > 0 && (
            <Card title="Wardrobe Intelligence" icon="👗">
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
                {(aiData?.wardrobe_insights || []).map((ins, i) => <InsightCard key={i} ins={ins} index={i} />)}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* RECOMMENDATIONS TAB */}
      {activeTab === "recommendations" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {recs.length === 0 ? (
            <div style={{ textAlign: "center", padding: "56px 0", opacity: 0.6 }}>
              <div style={{ fontSize: 48 }}>🎯</div>
              <p style={{ color: "#9898b8", marginTop: 12 }}>No recommendations yet. Keep logging data!</p>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
              {recs.map((rec, i) => {
                const priorityColor = rec.priority === "high" ? "#e07070" : rec.priority === "medium" ? "#c9a96e" : "#6aaa8a";
                const priorityBg = rec.priority === "high" ? "#fdf0f0" : rec.priority === "medium" ? "#fdf8e8" : "#eaf6ef";
                return (
                  <div key={i} style={{ background: "#fff", borderRadius: 16, padding: "18px 20px", boxShadow: "0 2px 14px rgba(124,111,160,0.08)", border: "1px solid rgba(124,111,160,0.08)", animation: `fadeUp 0.4s ease both`, animationDelay: `${i * 0.08}s`, transition: "transform 0.2s, box-shadow 0.2s" }}
                    onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "0 8px 24px rgba(124,111,160,0.14)"; }}
                    onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.boxShadow = "0 2px 14px rgba(124,111,160,0.08)"; }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                      <span style={{ fontSize: 24 }}>{rec.icon || "🎯"}</span>
                      <div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: "#1a1a2e" }}>{rec.title}</div>
                        <span style={{ fontSize: 10, background: priorityBg, color: priorityColor, padding: "2px 8px", borderRadius: 100, fontWeight: 800 }}>
                          {rec.priority?.toUpperCase()} PRIORITY
                        </span>
                      </div>
                    </div>
                    <p style={{ fontSize: 12, color: "#777", lineHeight: 1.6, margin: 0 }}>{rec.text}</p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}