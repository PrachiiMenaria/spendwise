// fenora/frontend/src/pages/Landing.jsx
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const features = [
  { icon: "👗", title: "Wardrobe Intelligence", desc: "Track cost-per-wear. Stop buying clothes you already have hidden in your closet.", color: "#7c6fa0", bg: "#f0eef8" },
  { icon: "💳", title: "Expense Tracking", desc: "Log expenses in seconds. See exactly where every rupee goes with beautiful charts.", color: "#c9a96e", bg: "#fdf8e8" },
  { icon: "🤖", title: "AI Insights Engine", desc: "Get personalised alerts about overspending before it happens. Your money, your way.", color: "#6aaa8a", bg: "#eaf6ef" },
  { icon: "🏦", title: "Goal-Based Saving", desc: "Set a goal, get a plan. Fenora tells you exactly what to cut to reach it.", color: "#e07070", bg: "#fdf0f0" },
];

const stats = [
  { value: "₹12K", label: "Avg monthly savings" },
  { value: "3×", label: "Better wardrobe use" },
  { value: "2 min", label: "Daily tracking time" },
];

// Floating mini-card previews for the hero
function FloatingCard({ style, children }) {
  return (
    <div style={{
      background: "rgba(255,255,255,0.85)",
      backdropFilter: "blur(16px)",
      border: "1px solid rgba(255,255,255,0.7)",
      borderRadius: 16,
      padding: "12px 16px",
      boxShadow: "0 8px 32px rgba(124,111,160,0.15)",
      fontFamily: "'DM Sans', sans-serif",
      ...style,
    }}>
      {children}
    </div>
  );
}

export default function Landing({ isAuthenticated }) {
  const [visible, setVisible] = useState(false);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    setTimeout(() => setVisible(true), 100);
    const t = setInterval(() => setTick(p => p + 1), 3000);
    return () => clearInterval(t);
  }, []);

  const tips = [
    "Skip Swiggy today → save ₹320 🍕",
    "You've worn your black tee 12× — great value! ✨",
    "Budget at 68% — you're on track 🎯",
    "3 unworn items in wardrobe 👗",
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#f8f6ff", fontFamily: "'DM Sans', sans-serif", overflowX: "hidden" }}>
      {/* Blob backgrounds */}
      <div style={{ position: "fixed", top: -140, left: -140, width: 500, height: 500, borderRadius: "50%", background: "rgba(124,111,160,0.1)", filter: "blur(80px)", pointerEvents: "none", zIndex: 0 }} />
      <div style={{ position: "fixed", bottom: -120, right: -120, width: 400, height: 400, borderRadius: "50%", background: "rgba(201,169,110,0.09)", filter: "blur(70px)", pointerEvents: "none", zIndex: 0 }} />
      <div style={{ position: "fixed", top: "40%", right: "10%", width: 250, height: 250, borderRadius: "50%", background: "rgba(106,170,138,0.07)", filter: "blur(50px)", pointerEvents: "none", zIndex: 0 }} />

      {/* Navbar */}
      <nav style={{
        position: "fixed", top: 0, left: 0, right: 0, zIndex: 100,
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "14px 40px",
        background: "rgba(248,246,255,0.85)", backdropFilter: "blur(20px)",
        borderBottom: "1px solid rgba(124,111,160,0.08)",
      }}>
        <div style={{ fontSize: 20, fontWeight: 900, color: "#1a1a2e", letterSpacing: "-0.5px" }}>
          Fenora<span style={{ color: "#7c6fa0" }}>✦</span>
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          {isAuthenticated ? (
            <Link to="/dashboard" style={btnPrimary}>Go to Dashboard →</Link>
          ) : (
            <>
              <Link to="/login" style={{ fontSize: 13, fontWeight: 600, color: "#7c6fa0", textDecoration: "none", padding: "8px 16px" }}>Sign In</Link>
              <Link to="/register" style={btnPrimary}>Get Started Free</Link>
            </>
          )}
        </div>
      </nav>

      {/* ── HERO ── */}
      <main style={{ paddingTop: 110, position: "relative", zIndex: 1 }}>
        <div style={{ maxWidth: 1000, margin: "0 auto", padding: "60px 24px 80px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 40, alignItems: "center", flexWrap: "wrap" }}>

            {/* Left: Text */}
            <div>
              {/* Badge */}
              <div style={{
                display: "inline-flex", alignItems: "center", gap: 8,
                background: "rgba(124,111,160,0.1)", borderRadius: 100,
                padding: "7px 16px", marginBottom: 28, fontSize: 12,
                color: "#7c6fa0", fontWeight: 700,
                opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(10px)",
                transition: "all 0.6s ease",
              }}>
                ✦ AI-powered financial lifestyle assistant
              </div>

              <h1 style={{
                fontSize: "clamp(36px, 6vw, 68px)", fontWeight: 900, color: "#1a1a2e",
                lineHeight: 1.08, letterSpacing: "-2px", margin: "0 0 20px",
                opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)",
                transition: "all 0.7s ease 0.1s",
              }}>
                Soft life.<br />
                Smart money.<br />
                <span style={{ background: "linear-gradient(135deg, #7c6fa0, #a89cc8, #c9a96e)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                  That's Fenora ✨
                </span>
              </h1>

              <p style={{
                fontSize: 16, color: "#6b6888", lineHeight: 1.7, maxWidth: 460,
                margin: "0 0 36px",
                opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)",
                transition: "all 0.7s ease 0.2s",
              }}>
                Connect your wardrobe and wallet. Built for Gen Z to build better habits without spreadsheets, stress, or losing your sense of style.
              </p>

              {!isAuthenticated && (
                <div style={{
                  display: "flex", gap: 12, flexWrap: "wrap",
                  opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(20px)",
                  transition: "all 0.7s ease 0.3s",
                }}>
                  <Link to="/register" style={{ ...btnPrimary, fontSize: 14, padding: "13px 30px", borderRadius: 50, boxShadow: "0 8px 28px rgba(124,111,160,0.4)" }}>
                    Start Your Journey →
                  </Link>
                  <Link to="/login" style={{
                    fontSize: 14, padding: "13px 28px", borderRadius: 50, fontWeight: 700,
                    background: "#fff", color: "#7c6fa0", border: "2px solid #e8e4f5",
                    textDecoration: "none", transition: "all 0.2s",
                  }}>Sign In</Link>
                </div>
              )}

              {/* Stats */}
              <div style={{
                display: "flex", gap: 0, marginTop: 44, maxWidth: 420,
                background: "#fff", borderRadius: 18, overflow: "hidden",
                boxShadow: "0 4px 24px rgba(124,111,160,0.09)", border: "1px solid rgba(124,111,160,0.07)",
                opacity: visible ? 1 : 0, transition: "all 0.7s ease 0.4s",
              }}>
                {stats.map((s, i) => (
                  <div key={i} style={{
                    flex: 1, padding: "18px 14px", textAlign: "center",
                    borderRight: i < stats.length - 1 ? "1px solid #f0eef8" : "none",
                  }}>
                    <div style={{ fontSize: 22, fontWeight: 900, color: "#7c6fa0", letterSpacing: "-1px" }}>{s.value}</div>
                    <div style={{ fontSize: 10, color: "#9898b8", marginTop: 3, fontWeight: 600 }}>{s.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Floating UI preview cards */}
            <div style={{
              position: "relative", width: 240, height: 360, flexShrink: 0,
              display: "none",
              opacity: visible ? 1 : 0, transition: "all 0.9s ease 0.5s",
              ...(typeof window !== "undefined" && window.innerWidth > 768 ? { display: "block" } : {}),
            }} className="hero-cards">
              {/* Budget card */}
              <FloatingCard style={{ position: "absolute", top: 0, left: 0, width: 200, animation: "float1 6s ease-in-out infinite" }}>
                <div style={{ fontSize: 9, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 4 }}>This Month</div>
                <div style={{ fontSize: 20, fontWeight: 900, color: "#7c6fa0" }}>₹6,240</div>
                <div style={{ fontSize: 10, color: "#9898b8", marginBottom: 8 }}>of ₹10,000 budget</div>
                <div style={{ background: "#f0eef8", borderRadius: 100, height: 5, overflow: "hidden" }}>
                  <div style={{ width: "62%", height: "100%", background: "linear-gradient(90deg,#7c6fa0,#a89cc8)", borderRadius: 100 }} />
                </div>
              </FloatingCard>

              {/* AI Insight card */}
              <FloatingCard style={{ position: "absolute", top: 100, right: -20, width: 210, animation: "float2 7s ease-in-out infinite" }}>
                <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                  <span style={{ fontSize: 20 }}>🤖</span>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 800, color: "#7c6fa0", marginBottom: 4 }}>AI TIP</div>
                    <div style={{ fontSize: 11, color: "#3d3a52", lineHeight: 1.5 }}>
                      {tips[tick % tips.length]}
                    </div>
                  </div>
                </div>
              </FloatingCard>

              {/* Wardrobe card */}
              <FloatingCard style={{ position: "absolute", bottom: 60, left: 10, width: 190, animation: "float3 8s ease-in-out infinite" }}>
                <div style={{ fontSize: 9, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 8 }}>Wardrobe IQ</div>
                {[{ name: "Black Tee", wears: 12 }, { name: "White Shirt", wears: 4 }, { name: "Blue Jeans", wears: 8 }].map((item, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <span style={{ fontSize: 12 }}>👕</span>
                    <span style={{ fontSize: 10, flex: 1, color: "#555" }}>{item.name}</span>
                    <span style={{ fontSize: 10, fontWeight: 700, color: "#7c6fa0" }}>{item.wears}×</span>
                  </div>
                ))}
              </FloatingCard>

              {/* Goal card */}
              <FloatingCard style={{ position: "absolute", bottom: -10, right: 0, width: 170, animation: "float1 5s ease-in-out infinite reverse" }}>
                <div style={{ fontSize: 9, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 4 }}>Saving Goal 🎯</div>
                <div style={{ fontSize: 13, fontWeight: 800, color: "#1a1a2e", marginBottom: 4 }}>New Phone</div>
                <div style={{ background: "#f0eef8", borderRadius: 100, height: 4, overflow: "hidden", marginBottom: 4 }}>
                  <div style={{ width: "45%", height: "100%", background: "linear-gradient(90deg,#6aaa8a,#8ac8a8)", borderRadius: 100 }} />
                </div>
                <div style={{ fontSize: 10, color: "#6aaa8a", fontWeight: 600 }}>45% saved ✓</div>
              </FloatingCard>
            </div>
          </div>
        </div>

        {/* Feature Cards */}
        <div style={{ maxWidth: 1000, margin: "0 auto", padding: "0 24px 80px" }}>
          <div style={{ textAlign: "center", marginBottom: 40 }}>
            <h2 style={{ fontSize: 30, fontWeight: 800, color: "#1a1a2e", letterSpacing: "-0.5px", margin: 0 }}>Everything you need</h2>
            <p style={{ color: "#9898b8", marginTop: 8, fontSize: 14 }}>Four powerful tools, one seamless experience</p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 18 }}>
            {features.map((f, i) => (
              <div key={i} style={{
                background: "#fff", borderRadius: 20, padding: "24px 22px",
                boxShadow: "0 4px 24px rgba(124,111,160,0.07)",
                border: "1px solid rgba(124,111,160,0.07)",
                transition: "transform 0.2s, box-shadow 0.2s",
                animation: `fadeUp 0.5s ease both`, animationDelay: `${0.4 + i * 0.1}s`,
              }}
                onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-4px)"; e.currentTarget.style.boxShadow = "0 12px 40px rgba(124,111,160,0.14)"; }}
                onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.boxShadow = "0 4px 24px rgba(124,111,160,0.07)"; }}
              >
                <div style={{ width: 48, height: 48, borderRadius: 14, background: f.bg, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24, marginBottom: 16 }}>
                  {f.icon}
                </div>
                <h3 style={{ fontSize: 15, fontWeight: 800, color: "#1a1a2e", margin: "0 0 8px" }}>{f.title}</h3>
                <p style={{ fontSize: 12, color: "#6b6888", lineHeight: 1.6, margin: 0 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        {!isAuthenticated && (
          <div style={{ padding: "0 24px 80px", textAlign: "center" }}>
            <div style={{
              maxWidth: 580, margin: "0 auto",
              background: "linear-gradient(135deg, #7c6fa0 0%, #a89cc8 100%)",
              borderRadius: 24, padding: "40px 32px", color: "#fff",
              position: "relative", overflow: "hidden",
              boxShadow: "0 16px 48px rgba(124,111,160,0.3)",
            }}>
              <div style={{ position: "absolute", top: -50, right: -50, width: 180, height: 180, borderRadius: "50%", background: "rgba(255,255,255,0.07)" }} />
              <div style={{ position: "absolute", bottom: -30, left: -30, width: 120, height: 120, borderRadius: "50%", background: "rgba(255,255,255,0.05)" }} />
              <div style={{ position: "relative", zIndex: 1 }}>
                <div style={{ fontSize: 36, marginBottom: 12 }}>✨</div>
                <h2 style={{ fontSize: 24, fontWeight: 800, margin: "0 0 12px", letterSpacing: "-0.5px" }}>Ready to take control?</h2>
                <p style={{ opacity: 0.85, marginBottom: 28, fontSize: 14, lineHeight: 1.7 }}>
                  Join thousands of students tracking smarter. Free, fast, and actually works.
                </p>
                <Link to="/register" style={{ ...btnPrimary, background: "#fff", color: "#7c6fa0", display: "inline-block", padding: "13px 32px", fontSize: 14 }}>
                  Create Free Account →
                </Link>
              </div>
            </div>
          </div>
        )}
      </main>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800;900&display=swap');
        @keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes float1 { 0%,100%{ transform: translateY(0px); } 50%{ transform: translateY(-10px); } }
        @keyframes float2 { 0%,100%{ transform: translateY(0px) rotate(1deg); } 50%{ transform: translateY(-8px) rotate(-1deg); } }
        @keyframes float3 { 0%,100%{ transform: translateY(0px) rotate(-1deg); } 50%{ transform: translateY(-12px) rotate(1deg); } }
        .hero-cards { display: none !important; }
        @media(min-width: 820px) { .hero-cards { display: block !important; } }
      `}</style>
    </div>
  );
}

const btnPrimary = {
  background: "linear-gradient(135deg, #7c6fa0, #a89cc8)",
  color: "#fff", textDecoration: "none",
  padding: "10px 22px", borderRadius: 50,
  fontSize: 13, fontWeight: 700,
  boxShadow: "0 4px 16px rgba(124,111,160,0.3)",
  display: "inline-block", transition: "all 0.2s",
};