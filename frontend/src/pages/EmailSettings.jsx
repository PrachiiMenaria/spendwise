// fenora/frontend/src/pages/EmailSettings.jsx
// ─────────────────────────────────────────────────────────
// Smart Email Reminder Settings + Test Email Button
// Add to your router: <Route path="/email-settings" element={<EmailSettings />} />
// Add to your sidebar/nav as: "📧 Email Reminders"
// ─────────────────────────────────────────────────────────

import { useState, useEffect } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000";

// ── Tiny helpers ──────────────────────────────────────────
const useFetch = (url) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    fetch(url, { credentials: "include" })
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [url]);
  return { data, loading };
};

// ── Sub-components ────────────────────────────────────────

function StatusBadge({ type, children }) {
  const styles = {
    success: { bg: "#f0faf5", color: "#27ae60", border: "#c3e6cb" },
    error:   { bg: "#fdf0f0", color: "#e74c3c", border: "#f5c6cb" },
    info:    { bg: "#f3f0fa", color: "#7c6fa0", border: "#d4c5f9" },
    warning: { bg: "#fef9f0", color: "#c67c17", border: "#fde68a" },
  };
  const s = styles[type] || styles.info;
  return (
    <div style={{
      background: s.bg, color: s.color,
      border: `1px solid ${s.border}`,
      borderRadius: 10, padding: "12px 16px",
      fontSize: 13, fontWeight: 500, lineHeight: 1.5,
      display: "flex", gap: 10, alignItems: "flex-start",
    }}>
      <span style={{ fontSize: 16, flexShrink: 0 }}>
        {type === "success" ? "✅" : type === "error" ? "⚠️" : type === "warning" ? "⚠️" : "💡"}
      </span>
      <span>{children}</span>
    </div>
  );
}

function Card({ title, subtitle, icon, children, accent }) {
  return (
    <div style={{
      background: "#fff",
      borderRadius: 18,
      padding: "22px 24px",
      boxShadow: "0 2px 20px rgba(124,111,160,0.08)",
      border: "1px solid rgba(124,111,160,0.09)",
      borderTop: `3px solid ${accent || "#7c6fa0"}`,
    }}>
      {(title || icon) && (
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
          {icon && (
            <div style={{
              width: 38, height: 38, borderRadius: 11,
              background: `${accent || "#7c6fa0"}18`,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 18, flexShrink: 0,
            }}>{icon}</div>
          )}
          <div>
            {title && <div style={{ fontWeight: 800, fontSize: 15, color: "#1a1a2e" }}>{title}</div>}
            {subtitle && <div style={{ fontSize: 12, color: "#9898b8", marginTop: 1 }}>{subtitle}</div>}
          </div>
        </div>
      )}
      {children}
    </div>
  );
}

function Toggle({ checked, onChange, disabled }) {
  return (
    <div
      onClick={() => !disabled && onChange(!checked)}
      style={{
        width: 50, height: 27, borderRadius: 100,
        background: checked ? "linear-gradient(135deg,#7c6fa0,#a89cc8)" : "#e0dde8",
        position: "relative", cursor: disabled ? "not-allowed" : "pointer",
        transition: "background 0.25s", flexShrink: 0,
        boxShadow: checked ? "0 2px 12px rgba(124,111,160,0.35)" : "none",
        opacity: disabled ? 0.5 : 1,
      }}
    >
      <div style={{
        position: "absolute", top: 3, left: checked ? 26 : 3,
        width: 21, height: 21, borderRadius: "50%", background: "#fff",
        transition: "left 0.25s cubic-bezier(0.34,1.56,0.64,1)",
        boxShadow: "0 1px 5px rgba(0,0,0,0.2)",
      }} />
    </div>
  );
}

function FreqPill({ label, value, selected, onClick }) {
  return (
    <button onClick={onClick} style={{
      padding: "9px 22px", borderRadius: 100, fontSize: 13, fontWeight: 700,
      border: selected ? "none" : "1.5px solid #e8e4f5",
      background: selected ? "linear-gradient(135deg,#7c6fa0,#a89cc8)" : "#faf9ff",
      color: selected ? "#fff" : "#9898b8",
      cursor: "pointer", fontFamily: "inherit",
      transition: "all 0.2s",
      boxShadow: selected ? "0 4px 16px rgba(124,111,160,0.28)" : "none",
    }}>{label}</button>
  );
}

function InsightChip({ icon, text, type }) {
  const colors = {
    success: ["#f0faf5", "#27ae60"],
    warning: ["#fef9f0", "#c67c17"],
    danger:  ["#fdf0f0", "#e74c3c"],
    info:    ["#f3f0fa", "#7c6fa0"],
  };
  const [bg, color] = colors[type] || colors.info;
  return (
    <div style={{
      background: bg, borderRadius: 8, padding: "9px 12px",
      display: "flex", gap: 8, alignItems: "flex-start", marginBottom: 8,
    }}>
      <span style={{ fontSize: 15, flexShrink: 0 }}>{icon}</span>
      <span style={{ fontSize: 12, color, lineHeight: 1.5 }}>{text}</span>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────

export default function EmailSettings() {
  const { data: settings, loading: settingsLoading } = useFetch(`${API}/api/email-settings`);
  const { data: preview, loading: previewLoading } = useFetch(`${API}/api/email-preview`);
  const { data: emailDebug } = useFetch(`${API}/api/email-debug`);

  const [enabled, setEnabled] = useState(true);
  const [frequency, setFrequency] = useState("monthly");
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null); // {type, msg}

  const [testState, setTestState] = useState("idle"); // idle | loading | success | error
  const [testResult, setTestResult] = useState(null);

  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    if (settings) {
      setEnabled(settings.email_reminders_enabled ?? true);
      setFrequency(settings.email_frequency ?? "monthly");
    }
  }, [settings]);

  const saveSettings = async () => {
    setSaving(true);
    setSaveStatus(null);
    try {
      const res = await fetch(`${API}/api/email-settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email_reminders_enabled: enabled, email_frequency: frequency }),
      });
      const data = await res.json();
      setSaveStatus({
        type: data.success ? "success" : "error",
        msg: data.success ? "Settings saved! ✨" : data.error || "Failed to save.",
      });
    } catch {
      setSaveStatus({ type: "error", msg: "Network error. Please try again." });
    } finally {
      setSaving(false);
      setTimeout(() => setSaveStatus(null), 4000);
    }
  };

  const sendTestEmail = async () => {
    setTestState("loading");
    setTestResult(null);
    try {
      const res = await fetch(`${API}/api/test-email-v2`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ weekly: frequency === "weekly" }),
      });
      const data = await res.json();
      setTestResult(data);
      setTestState(data.success ? "success" : "error");
    } catch (err) {
      setTestResult({ success: false, message: "Network error. Is the backend running?" });
      setTestState("error");
    }
  };

  const resetTest = () => { setTestState("idle"); setTestResult(null); };

  const insights = preview?.insights;
  const allInsights = [
    ...(insights?.expense_insights || []),
    ...(insights?.wardrobe_insights || []),
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 22, maxWidth: 680 }}>

      {/* ── Page header ── */}
      <div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: "#1a1a2e", margin: 0, letterSpacing: "-0.5px" }}>
          Email Reminders 📧
        </h1>
        <p style={{ color: "#9898b8", marginTop: 5, fontSize: 13 }}>
          Get smart financial & wardrobe insights delivered to your inbox.
        </p>
      </div>

      {/* ── Toggle + Frequency ── */}
      <Card title="Reminder Settings" subtitle="Choose how often fenora emails you" icon="⚙️" accent="#7c6fa0">
        {settingsLoading ? (
          <div style={{ height: 60, display: "flex", alignItems: "center", gap: 10, color: "#9898b8", fontSize: 13 }}>
            <div style={{ width: 18, height: 18, borderRadius: "50%", border: "3px solid #e8e4f3", borderTopColor: "#7c6fa0", animation: "spin 0.8s linear infinite" }} />
            Loading settings…
          </div>
        ) : (
          <>
            {/* Enable toggle */}
            <div style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              padding: "14px 16px", background: "#faf9ff", borderRadius: 12,
              border: "1.5px solid #ede9f8", marginBottom: 16,
            }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14, color: "#1a1a2e" }}>Email Reminders</div>
                <div style={{ fontSize: 12, color: "#9898b8", marginTop: 2 }}>
                  {enabled ? "Active — you'll receive periodic summaries" : "Paused — no emails will be sent"}
                </div>
              </div>
              <Toggle checked={enabled} onChange={setEnabled} />
            </div>

            {/* Frequency selector */}
            <div style={{ opacity: enabled ? 1 : 0.4, transition: "opacity 0.2s", pointerEvents: enabled ? "auto" : "none" }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 10 }}>
                Frequency
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <FreqPill label="📅 Monthly" value="monthly" selected={frequency === "monthly"} onClick={() => setFrequency("monthly")} />
                <FreqPill label="🗓️ Weekly" value="weekly" selected={frequency === "weekly"} onClick={() => setFrequency("weekly")} />
              </div>
              <div style={{ fontSize: 11, color: "#b0aec8", marginTop: 10 }}>
                {frequency === "monthly"
                  ? "Sent on the 1st of each month — a full recap of your spending & wardrobe."
                  : "Sent every Sunday — a quick weekly check-in to keep you on track."}
              </div>
            </div>

            {/* Save button */}
            <div style={{ marginTop: 18, display: "flex", alignItems: "center", gap: 12 }}>
              <button onClick={saveSettings} disabled={saving} style={{
                background: saving ? "#c0bcd8" : "linear-gradient(135deg,#7c6fa0,#a89cc8)",
                color: "#fff", border: "none", borderRadius: 12, padding: "11px 26px",
                fontSize: 13, fontWeight: 700, cursor: saving ? "not-allowed" : "pointer",
                fontFamily: "inherit", transition: "all 0.2s",
                boxShadow: saving ? "none" : "0 4px 16px rgba(124,111,160,0.3)",
              }}>
                {saving ? "Saving…" : "Save Settings"}
              </button>
              {saveStatus && (
                <span style={{
                  fontSize: 13, fontWeight: 600,
                  color: saveStatus.type === "success" ? "#27ae60" : "#e74c3c",
                  animation: "fadeUp 0.3s ease both",
                }}>{saveStatus.msg}</span>
              )}
            </div>
          </>
        )}
      </Card>

      {/* ── Test Email Button ── */}
      <Card title="Test Your Email" subtitle="Send a preview email right now" icon="🚀" accent="#c9a96e">
        <p style={{ fontSize: 13, color: "#666", lineHeight: 1.7, marginBottom: 20, marginTop: 0 }}>
          Click below to instantly send a personalised email with your current spending insights.
          Great for checking setup or just seeing what the email looks like!
        </p>

        {testState === "idle" && (
          <button onClick={sendTestEmail} style={{
            background: "linear-gradient(135deg,#c9a96e,#e8c88a)",
            color: "#fff", border: "none", borderRadius: 12, padding: "13px 28px",
            fontSize: 14, fontWeight: 800, cursor: "pointer", fontFamily: "inherit",
            boxShadow: "0 4px 20px rgba(201,169,110,0.38)",
            transition: "all 0.2s", display: "flex", alignItems: "center", gap: 8,
          }}
            onMouseEnter={e => e.currentTarget.style.transform = "translateY(-1px)"}
            onMouseLeave={e => e.currentTarget.style.transform = "translateY(0)"}
          >
            <span>📧</span> Send Test Email
          </button>
        )}

        {testState === "loading" && (
          <div style={{
            background: "#f3f0fa", borderRadius: 14, padding: "20px 22px",
            display: "flex", alignItems: "center", gap: 14,
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: "50%",
              border: "3px solid #e8e4f3", borderTopColor: "#7c6fa0",
              animation: "spin 0.8s linear infinite", flexShrink: 0,
            }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: 14, color: "#1a1a2e" }}>Generating your insights…</div>
              <div style={{ fontSize: 12, color: "#9898b8", marginTop: 2 }}>Analysing expenses, wardrobe & recommendations</div>
            </div>
          </div>
        )}

        {testState === "success" && testResult && (
          <div style={{ animation: "fadeUp 0.4s ease both" }}>
            <div style={{
              background: "linear-gradient(135deg,#f0faf5,#e8f7f0)", borderRadius: 14, padding: "20px 22px",
              border: "1.5px solid #a8dfc0", marginBottom: 16,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                <span style={{ fontSize: 22 }}>🎉</span>
                <div>
                  <div style={{ fontWeight: 800, fontSize: 15, color: "#1a1a2e" }}>Email sent!</div>
                  <div style={{ fontSize: 12, color: "#5a9a72" }}>Check your inbox at <strong>{testResult.to}</strong></div>
                </div>
              </div>
              <div style={{ fontSize: 12, color: "#666", background: "#fff", borderRadius: 8, padding: "8px 12px", marginTop: 8 }}>
                Subject: <em>{testResult.subject}</em>
              </div>
            </div>

            {/* Insights summary */}
            {testResult.insights_summary && (
              <div style={{
                background: "#fff", borderRadius: 14, padding: "16px 18px",
                border: "1px solid #ede9f8", marginBottom: 14,
              }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 12 }}>
                  Generated For Your Email
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
                  {[
                    { label: "Spent This Month", value: `₹${Number(testResult.insights_summary.this_month_total || 0).toLocaleString("en-IN")}`, icon: "💳" },
                    { label: "Budget Used", value: `${testResult.insights_summary.budget_pct || 0}%`, icon: "📊" },
                    { label: "Insights", value: `${(testResult.insights_summary.expense_insights_count || 0) + (testResult.insights_summary.wardrobe_insights_count || 0)}`, icon: "🧠" },
                  ].map((stat, i) => (
                    <div key={i} style={{ textAlign: "center", padding: "10px 8px", background: "#faf9ff", borderRadius: 10 }}>
                      <div style={{ fontSize: 18 }}>{stat.icon}</div>
                      <div style={{ fontWeight: 800, fontSize: 15, color: "#7c6fa0", margin: "4px 0" }}>{stat.value}</div>
                      <div style={{ fontSize: 10, color: "#9898b8" }}>{stat.label}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <button onClick={resetTest} style={{
                background: "#f3f0fa", border: "none", borderRadius: 10, padding: "10px 20px",
                fontSize: 12, fontWeight: 700, color: "#7c6fa0", cursor: "pointer", fontFamily: "inherit",
              }}>
                Send Another
              </button>
              <button onClick={() => setShowPreview(!showPreview)} style={{
                background: "#fff", border: "1.5px solid #ede9f8", borderRadius: 10, padding: "10px 20px",
                fontSize: 12, fontWeight: 700, color: "#9898b8", cursor: "pointer", fontFamily: "inherit",
              }}>
                {showPreview ? "Hide Preview" : "👁️ Preview Email"}
              </button>
            </div>
          </div>
        )}

        {testState === "error" && testResult && (
          <div style={{ animation: "fadeUp 0.3s ease both" }}>
            <StatusBadge type="error">
              <div>
                <strong>Failed to send email</strong><br />
                {testResult.message}
                {testResult.hint && (
                  <div style={{ marginTop: 8, padding: "10px 12px", background: "rgba(231,76,60,0.07)", borderRadius: 8, fontSize: 11, lineHeight: 1.7, whiteSpace: "pre-line" }}>
                    {testResult.hint}
                  </div>
                )}
                {testResult.debug && !testResult.debug.sender_set && (
                  <div style={{ marginTop: 6, fontSize: 11 }}>
                    Add to your <code>.env</code>: <code>EMAIL_SENDER</code> and <code>EMAIL_PASSWORD</code>
                  </div>
                )}
              </div>
            </StatusBadge>
            <button onClick={resetTest} style={{
              marginTop: 12, background: "#f3f0fa", border: "none", borderRadius: 10, padding: "10px 20px",
              fontSize: 12, fontWeight: 700, color: "#7c6fa0", cursor: "pointer", fontFamily: "inherit",
            }}>
              ↩ Try Again
            </button>
          </div>
        )}
      </Card>

      {/* ── Insight Preview ── */}
      {!previewLoading && insights && allInsights.length > 0 && (
        <Card title="Your Current Insights" subtitle="This is what will be in your next email" icon="🧠" accent="#a89cc8">
          {allInsights.slice(0, 5).map((ins, i) => (
            <InsightChip key={i} icon={ins.icon} text={ins.text} type={ins.type} />
          ))}
          {insights.recommendations?.length > 0 && (
            <>
              <div style={{ fontSize: 11, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", letterSpacing: "0.5px", margin: "14px 0 10px" }}>
                Action Plan
              </div>
              {insights.recommendations.slice(0, 2).map((rec, i) => (
                <div key={i} style={{
                  display: "flex", gap: 10, alignItems: "flex-start", padding: "10px 12px",
                  background: "#faf9ff", borderRadius: 10, marginBottom: 8,
                }}>
                  <span style={{ fontSize: 18 }}>{rec.icon}</span>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 13, color: "#1a1a2e" }}>{rec.title}</div>
                    <div style={{ fontSize: 12, color: "#666", marginTop: 2 }}>{rec.text}</div>
                  </div>
                </div>
              ))}
            </>
          )}
        </Card>
      )}

      {/* ── How it works ── */}
      <Card title="How It Works" icon="📬" accent="#6aaa8a">
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[
            { step: "1", title: "fenora analyses your data", desc: "Expenses, budget usage, wardrobe wear counts — all combined into smart insights." },
            { step: "2", title: "Email is generated & sent", desc: `Monthly on the 1st${frequency === "weekly" ? " + every Sunday" : ""} — straight to your inbox.` },
            { step: "3", title: "You take action", desc: "Follow the recommendations to save more, spend smarter, and wear more of your wardrobe." },
          ].map((item) => (
            <div key={item.step} style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
              <div style={{
                width: 28, height: 28, borderRadius: 8, flexShrink: 0,
                background: "linear-gradient(135deg,#7c6fa0,#a89cc8)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 12, fontWeight: 800, color: "#fff",
              }}>{item.step}</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 13, color: "#1a1a2e" }}>{item.title}</div>
                <div style={{ fontSize: 12, color: "#9898b8", marginTop: 2, lineHeight: 1.5 }}>{item.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* ── Email Config Debug Panel ── */}
      {emailDebug && (
        <Card title="Email Configuration" subtitle="Check your SMTP setup" icon="🔧" accent={emailDebug.ready ? "#27ae60" : "#e74c3c"}>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div style={{ background: emailDebug.sender_configured ? "#f0faf5" : "#fdf0f0", border: `1px solid ${emailDebug.sender_configured ? "#c3e6cb" : "#f5c6cb"}`, borderRadius: 10, padding: "10px 14px" }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", marginBottom: 4 }}>Email Sender</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: emailDebug.sender_configured ? "#27ae60" : "#e74c3c" }}>
                  {emailDebug.sender_configured ? `✅ ${emailDebug.sender_preview || "Set"}` : "❌ Not set"}
                </div>
                <div style={{ fontSize: 10, color: "#9898b8", marginTop: 2 }}>EMAIL_SENDER in .env</div>
              </div>
              <div style={{ background: emailDebug.password_configured ? "#f0faf5" : "#fdf0f0", border: `1px solid ${emailDebug.password_configured ? "#c3e6cb" : "#f5c6cb"}`, borderRadius: 10, padding: "10px 14px" }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", marginBottom: 4 }}>App Password</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: emailDebug.password_configured ? "#27ae60" : "#e74c3c" }}>
                  {emailDebug.password_configured ? "✅ Set" : "❌ Not set"}
                </div>
                <div style={{ fontSize: 10, color: "#9898b8", marginTop: 2 }}>EMAIL_PASSWORD in .env</div>
              </div>
            </div>
            <div style={{ background: "#f8f6ff", borderRadius: 10, padding: "10px 14px", display: "flex", gap: 8, alignItems: "center" }}>
              <span style={{ fontSize: 14 }}>{emailDebug.ready ? "✅" : "⚠️"}</span>
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: "#1a1a2e" }}>SMTP: {emailDebug.smtp_host}:{emailDebug.smtp_port} ({emailDebug.method})</div>
                <div style={{ fontSize: 11, color: "#9898b8", marginTop: 2 }}>{emailDebug.hint}</div>
              </div>
            </div>
            {!emailDebug.ready && (
              <div style={{ background: "#fef9f0", border: "1px solid #fde68a", borderRadius: 10, padding: "12px 14px" }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: "#92400e", marginBottom: 6 }}>Setup Steps:</div>
                <ol style={{ margin: 0, paddingLeft: 18, display: "flex", flexDirection: "column", gap: 4 }}>
                  {["Go to myaccount.google.com → Security", "Enable 2-Step Verification (required)", "Security → App passwords → Create new", "Copy the 16-char password", "Add to .env: EMAIL_SENDER=you@gmail.com", "Add to .env: EMAIL_PASSWORD=xxxx xxxx xxxx xxxx"].map((s, i) => (
                    <li key={i} style={{ fontSize: 11, color: "#78350f" }}>{s}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* ── Email HTML Preview Modal ── */}
      {showPreview && (
        <div style={{ position: "fixed", inset: 0, zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,0.5)", backdropFilter: "blur(4px)" }}>
          <div style={{
            background: "#fff", borderRadius: 18, overflow: "hidden",
            width: "min(620px, 95vw)", maxHeight: "85vh",
            display: "flex", flexDirection: "column",
            boxShadow: "0 20px 80px rgba(0,0,0,0.3)",
          }}>
            <div style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              padding: "16px 20px", borderBottom: "1px solid #ede9f8",
              background: "#faf9ff",
            }}>
              <div>
                <div style={{ fontWeight: 800, fontSize: 14, color: "#1a1a2e" }}>Email Preview</div>
                <div style={{ fontSize: 11, color: "#9898b8" }}>
                  {preview?.subject || "Loading preview…"}
                </div>
              </div>
              <button onClick={() => setShowPreview(false)} style={{
                background: "#f0eef8", border: "none", borderRadius: 8, padding: "6px 12px",
                cursor: "pointer", fontSize: 13, color: "#7c6fa0", fontFamily: "inherit", fontWeight: 700,
              }}>✕ Close</button>
            </div>
            <div style={{ overflow: "auto", flex: 1 }}>
              {previewLoading ? (
                <div style={{ padding: 32, textAlign: "center", color: "#9898b8" }}>Loading preview…</div>
              ) : preview?.html ? (
                <iframe
                  srcDoc={preview.html}
                  style={{ width: "100%", height: 550, border: "none" }}
                  title="Email Preview"
                />
              ) : (
                <div style={{ padding: 32, textAlign: "center", color: "#9898b8" }}>No preview available. Add more data to generate insights.</div>
              )}
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}