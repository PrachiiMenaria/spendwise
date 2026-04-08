// fenora/frontend/src/pages/Landing.jsx — CINEMATIC UPGRADE
import { useState, useEffect, useRef } from "react";

const features = [
  {
    icon: "👗", title: "Wardrobe Intelligence",
    desc: "Track cost-per-wear. Stop buying clothes you already have hidden in your closet.",
    color: "#6b5fa0", bg: "linear-gradient(135deg, #f0eef8, #e8e4f8)",
    stat: "3× better", statLabel: "wardrobe use",
  },
  {
    icon: "💳", title: "Expense Tracking",
    desc: "Log expenses in seconds. See exactly where every rupee goes with beautiful charts.",
    color: "#c9a96e", bg: "linear-gradient(135deg, #fdf8e8, #fdf4d8)",
    stat: "2 min", statLabel: "daily habit",
  },
  {
    icon: "🤖", title: "AI Insights Engine",
    desc: "Get personalised alerts about overspending before it happens. Your money, your way.",
    color: "#5aaa82", bg: "linear-gradient(135deg, #eaf6ef, #ddf0e8)",
    stat: "₹12K", statLabel: "avg monthly savings",
  },
  {
    icon: "🏦", title: "Goal-Based Saving",
    desc: "Set a goal, get a plan. Fenora tells you exactly what to cut to reach it.",
    color: "#d96b6b", bg: "linear-gradient(135deg, #fdf0f0, #fde8e8)",
    stat: "92%", statLabel: "goal completion",
  },
];

const testimonials = [
  { name: "Priya S.", college: "BITS Pilani", text: "Saved ₹3,000 last month just by tracking my Swiggy orders. Wild.", avatar: "P" },
  { name: "Rahul M.", college: "IIT Bombay", text: "Finally know my cost-per-wear. My black tee is basically free at this point 😂", avatar: "R" },
  { name: "Ananya K.", college: "Delhi University", text: "The AI insights are scary accurate. It predicted I'd overspend before I did.", avatar: "A" },
];

function useScrollReveal() {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect(); } },
      { threshold: 0.12 }
    );
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);
  return [ref, visible];
}

function RevealSection({ children, delay = 0, style = {} }) {
  const [ref, visible] = useScrollReveal();
  return (
    <div ref={ref} style={{
      opacity: visible ? 1 : 0,
      transform: visible ? "translateY(0)" : "translateY(28px)",
      transition: `opacity 0.7s ease ${delay}s, transform 0.7s ease ${delay}s`,
      ...style,
    }}>
      {children}
    </div>
  );
}

export default function Landing({ onGetStarted }) {
  const [heroVisible, setHeroVisible] = useState(false);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const t1 = setTimeout(() => setHeroVisible(true), 80);
    const t2 = setInterval(() => setTick(p => p + 1), 3200);
    return () => { clearTimeout(t1); clearInterval(t2); };
  }, []);

  const tips = [
    "Skip Swiggy today → save ₹320 🍕",
    "Your black tee: 12 wears → ₹4/wear ✨",
    "Budget at 68% — you're on track 🎯",
    "3 unworn items worth ₹4,800 👗",
  ];

  return (
    <div style={{ minHeight: "100vh", background: "#f5f3fc", fontFamily: "'Outfit', sans-serif", overflowX: "hidden" }}>

      {/* ── Ambient blobs ─────────────────────────────────────────── */}
      <div style={{ position: "fixed", top: -200, left: -200, width: 600, height: 600, borderRadius: "50%", background: "radial-gradient(circle, rgba(107,95,160,0.12) 0%, transparent 70%)", pointerEvents: "none", zIndex: 0 }} />
      <div style={{ position: "fixed", bottom: -150, right: -150, width: 500, height: 500, borderRadius: "50%", background: "radial-gradient(circle, rgba(201,169,110,0.10) 0%, transparent 70%)", pointerEvents: "none", zIndex: 0 }} />
      <div style={{ position: "fixed", top: "35%", right: "5%", width: 300, height: 300, borderRadius: "50%", background: "radial-gradient(circle, rgba(90,170,130,0.07) 0%, transparent 70%)", pointerEvents: "none", zIndex: 0 }} />

      {/* ── Navbar ────────────────────────────────────────────────── */}
      <nav style={{
        position: "fixed", top: 0, left: 0, right: 0, zIndex: 100,
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "0 48px", height: 64,
        background: "rgba(245,243,252,0.88)", backdropFilter: "blur(24px)",
        borderBottom: "1px solid rgba(107,95,160,0.07)",
        boxShadow: "0 2px 20px rgba(107,95,160,0.05)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 30, height: 30, borderRadius: 9,
            background: "linear-gradient(135deg, #6b5fa0, #9b8ec8)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 14, color: "#fff", boxShadow: "0 3px 10px rgba(107,95,160,0.35)",
          }}>✦</div>
          <span style={{ fontSize: 18, fontWeight: 800, color: "#18182e", letterSpacing: "-0.4px" }}>
            fenora<span style={{ color: "#6b5fa0" }}>.</span>
          </span>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button onClick={onGetStarted} style={{
            fontSize: 13, fontWeight: 600, color: "#6b5fa0",
            background: "none", border: "none", cursor: "pointer",
            padding: "8px 16px", fontFamily: "inherit", transition: "color 0.15s",
          }}>Sign In</button>
          <button onClick={onGetStarted} style={{
            background: "linear-gradient(135deg, #6b5fa0, #9b8ec8)",
            color: "#fff", border: "none", borderRadius: 50,
            padding: "10px 22px", fontSize: 13, fontWeight: 700,
            cursor: "pointer", fontFamily: "inherit",
            boxShadow: "0 4px 16px rgba(107,95,160,0.35)",
            transition: "all 0.2s",
          }}
            onMouseEnter={e => e.currentTarget.style.transform = "translateY(-1px)"}
            onMouseLeave={e => e.currentTarget.style.transform = "translateY(0)"}
          >Get Started Free</button>
        </div>
      </nav>

      {/* ── Hero Section ──────────────────────────────────────────── */}
      <section style={{ paddingTop: 120, paddingBottom: 80, position: "relative", zIndex: 1 }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "0 32px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 48, alignItems: "center" }}>

            {/* Left: Copy */}
            <div>
              {/* Badge */}
              <div style={{
                display: "inline-flex", alignItems: "center", gap: 8,
                background: "rgba(107,95,160,0.08)", borderRadius: 100,
                padding: "7px 16px", marginBottom: 28,
                border: "1px solid rgba(107,95,160,0.15)",
                opacity: heroVisible ? 1 : 0,
                transform: heroVisible ? "translateY(0)" : "translateY(12px)",
                transition: "all 0.6s ease",
              }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#5aaa82", display: "inline-block", boxShadow: "0 0 8px rgba(90,170,130,0.6)" }} />
                <span style={{ fontSize: 11, fontWeight: 700, color: "#6b5fa0", letterSpacing: "0.3px" }}>
                  AI-Powered Financial Lifestyle Assistant
                </span>
              </div>

              {/* Headline */}
              <h1 style={{
                margin: "0 0 22px",
                lineHeight: 1.05, letterSpacing: "-2px",
                opacity: heroVisible ? 1 : 0,
                transform: heroVisible ? "translateY(0)" : "translateY(22px)",
                transition: "all 0.7s ease 0.1s",
              }}>
                <span style={{ fontSize: "clamp(40px, 6vw, 68px)", fontWeight: 900, color: "#18182e", display: "block" }}>
                  Money in control.
                </span>
                <span style={{ fontSize: "clamp(40px, 6vw, 68px)", fontWeight: 900, color: "#18182e", display: "block" }}>
                  Life on{" "}
                  <span style={{
                    fontFamily: "'Playfair Display', serif",
                    fontStyle: "italic",
                    background: "linear-gradient(135deg, #6b5fa0, #9b8ec8, #c9a96e)",
                    backgroundSize: "200% 200%",
                    WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
                    animation: "gradientShift 4s ease infinite",
                  }}>glow</span>
                  {" "}✨
                </span>
              </h1>

              {/* Tagline */}
              <p style={{
                fontSize: 16, color: "#5a5880", lineHeight: 1.75,
                maxWidth: 480, margin: "0 0 36px",
                opacity: heroVisible ? 1 : 0,
                transform: heroVisible ? "translateY(0)" : "translateY(18px)",
                transition: "all 0.7s ease 0.2s",
              }}>
                Connect your wardrobe and wallet. Built for Gen Z to track every rupee and every outfit — without the stress of spreadsheets.
              </p>

              {/* CTAs */}
              <div style={{
                display: "flex", gap: 12, flexWrap: "wrap",
                opacity: heroVisible ? 1 : 0,
                transform: heroVisible ? "translateY(0)" : "translateY(16px)",
                transition: "all 0.7s ease 0.3s",
              }}>
                <button onClick={onGetStarted} style={{
                  background: "linear-gradient(135deg, #6b5fa0, #9b8ec8)",
                  color: "#fff", border: "none", borderRadius: 50,
                  padding: "14px 32px", fontSize: 14, fontWeight: 800,
                  cursor: "pointer", fontFamily: "inherit",
                  boxShadow: "0 8px 28px rgba(107,95,160,0.42)",
                  transition: "all 0.22s", letterSpacing: "0.2px",
                }}
                  onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "0 14px 40px rgba(107,95,160,0.5)"; }}
                  onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.boxShadow = "0 8px 28px rgba(107,95,160,0.42)"; }}
                >
                  Start Your Journey →
                </button>
                <button onClick={onGetStarted} style={{
                  background: "#fff", color: "#6b5fa0",
                  border: "2px solid rgba(107,95,160,0.18)", borderRadius: 50,
                  padding: "13px 28px", fontSize: 14, fontWeight: 700,
                  cursor: "pointer", fontFamily: "inherit",
                  boxShadow: "0 4px 16px rgba(107,95,160,0.08)",
                  transition: "all 0.22s",
                }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = "rgba(107,95,160,0.35)"; e.currentTarget.style.background = "#faf9ff"; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = "rgba(107,95,160,0.18)"; e.currentTarget.style.background = "#fff"; }}
                >
                  Sign In
                </button>
              </div>

              {/* Stat strip */}
              <div style={{
                display: "flex", gap: 0, marginTop: 44, maxWidth: 400,
                background: "#fff", borderRadius: 16, overflow: "hidden",
                boxShadow: "0 4px 24px rgba(107,95,160,0.09)",
                border: "1px solid rgba(107,95,160,0.07)",
                opacity: heroVisible ? 1 : 0,
                transition: "all 0.7s ease 0.45s",
              }}>
                {[
                  { v: "₹12K", l: "Avg savings/mo" },
                  { v: "3×", l: "Better wardrobe" },
                  { v: "2 min", l: "Daily tracking" },
                ].map((s, i) => (
                  <div key={i} style={{
                    flex: 1, padding: "16px 12px", textAlign: "center",
                    borderRight: i < 2 ? "1px solid #f0eef8" : "none",
                  }}>
                    <div style={{ fontSize: 20, fontWeight: 900, color: "#6b5fa0", letterSpacing: "-0.5px" }}>{s.v}</div>
                    <div style={{ fontSize: 10, color: "#9898b8", marginTop: 3, fontWeight: 600 }}>{s.l}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Floating UI cards */}
            <div className="hero-cards" style={{ position: "relative", width: 260, height: 400, flexShrink: 0, opacity: heroVisible ? 1 : 0, transition: "all 1s ease 0.55s" }}>
              {/* Budget card */}
              <FloatingMiniCard style={{ top: 0, left: 0, width: 210, animation: "float1 6s ease-in-out infinite" }}>
                <div style={{ fontSize: 9, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: 5 }}>This Month</div>
                <div style={{ fontSize: 22, fontWeight: 900, color: "#6b5fa0", letterSpacing: "-0.5px" }}>₹6,240</div>
                <div style={{ fontSize: 10, color: "#9898b8", marginBottom: 10 }}>of ₹10,000 budget</div>
                <div style={{ background: "#f0eef8", borderRadius: 100, height: 6, overflow: "hidden" }}>
                  <div style={{ width: "62%", height: "100%", background: "linear-gradient(90deg, #6b5fa0, #9b8ec8)", borderRadius: 100 }} />
                </div>
                <div style={{ fontSize: 10, color: "#9898b8", marginTop: 5 }}>62% used · ₹3,760 left</div>
              </FloatingMiniCard>

              {/* AI tip card */}
              <FloatingMiniCard style={{ top: 110, right: -20, width: 220, animation: "float2 7s ease-in-out infinite" }}>
                <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                  <div style={{ width: 34, height: 34, borderRadius: 10, background: "linear-gradient(135deg, #6b5fa0, #9b8ec8)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, flexShrink: 0 }}>🤖</div>
                  <div>
                    <div style={{ fontSize: 9, fontWeight: 800, color: "#6b5fa0", marginBottom: 4, letterSpacing: "0.5px" }}>AI INSIGHT</div>
                    <div style={{ fontSize: 11, color: "#3d3a52", lineHeight: 1.55, fontWeight: 500 }}>
                      {tips[tick % tips.length]}
                    </div>
                  </div>
                </div>
              </FloatingMiniCard>

              {/* Wardrobe card */}
              <FloatingMiniCard style={{ bottom: 80, left: 0, width: 200, animation: "float3 8s ease-in-out infinite" }}>
                <div style={{ fontSize: 9, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: 10 }}>Wardrobe IQ</div>
                {[{ name: "Black Tee", wears: 12, cpw: "₹4" }, { name: "White Shirt", wears: 4, cpw: "₹250" }, { name: "Blue Jeans", wears: 8, cpw: "₹75" }].map((item, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 7 }}>
                    <span style={{ fontSize: 13 }}>👕</span>
                    <span style={{ fontSize: 10, flex: 1, color: "#555", fontWeight: 500 }}>{item.name}</span>
                    <span style={{ fontSize: 10, fontWeight: 700, color: "#6b5fa0" }}>{item.wears}×</span>
                    <span style={{ fontSize: 9, color: "#9898b8" }}>{item.cpw}/wear</span>
                  </div>
                ))}
              </FloatingMiniCard>

              {/* Goal card */}
              <FloatingMiniCard style={{ bottom: -10, right: 0, width: 170, animation: "float1 5s ease-in-out infinite reverse" }}>
                <div style={{ fontSize: 9, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: 5 }}>Saving Goal 🎯</div>
                <div style={{ fontSize: 13, fontWeight: 800, color: "#18182e", marginBottom: 6 }}>New MacBook</div>
                <div style={{ background: "#f0eef8", borderRadius: 100, height: 5, overflow: "hidden", marginBottom: 5 }}>
                  <div style={{ width: "45%", height: "100%", background: "linear-gradient(90deg, #5aaa82, #7acca4)", borderRadius: 100 }} />
                </div>
                <div style={{ fontSize: 10, color: "#5aaa82", fontWeight: 700 }}>45% saved ✓</div>
              </FloatingMiniCard>
            </div>
          </div>
        </div>
      </section>

      {/* ── Storytelling Sections ─────────────────────────────────── */}
      <section style={{ background: "#fff", padding: "80px 0", position: "relative", zIndex: 1 }}>
        <div style={{ maxWidth: 1000, margin: "0 auto", padding: "0 32px" }}>
          {[
            {
              icon: "💸", title: "Track your money", eyebrow: "Expense tracking",
              body: "Know exactly where every rupee goes. Beautiful charts, category breakdowns, and monthly trends make your finances feel less scary and more empowering.",
              visual: <ExpenseVisual />,
              color: "#6b5fa0", flip: false,
            },
            {
              icon: "👗", title: "Understand your wardrobe", eyebrow: "Wardrobe IQ",
              body: "Stop buying clothes you already own. Track every item's cost-per-wear and discover your most (and least) efficient pieces before your next shopping trip.",
              visual: <WardrobeVisual />,
              color: "#c9a96e", flip: true,
            },
            {
              icon: "🤖", title: "Make smarter decisions", eyebrow: "AI insights",
              body: "Your personal AI tracks patterns and flags overspending before it happens. Get weekly reports, anomaly alerts, and predictive forecasts — all automatically.",
              visual: <InsightVisual />,
              color: "#5aaa82", flip: false,
            },
          ].map((sec, i) => (
            <RevealSection key={i} delay={0.1} style={{ marginBottom: i < 2 ? 80 : 0 }}>
              <div style={{ display: "grid", gridTemplateColumns: sec.flip ? "1fr 1fr" : "1fr 1fr", gap: 60, alignItems: "center" }}>
                {sec.flip ? (
                  <>
                    <div style={{ order: 2 }}>
                      <StoryContent {...sec} />
                    </div>
                    <div style={{ order: 1 }}>
                      {sec.visual}
                    </div>
                  </>
                ) : (
                  <>
                    <div>
                      <StoryContent {...sec} />
                    </div>
                    <div>
                      {sec.visual}
                    </div>
                  </>
                )}
              </div>
            </RevealSection>
          ))}
        </div>
      </section>

      {/* ── Features Grid ─────────────────────────────────────────── */}
      <section style={{ padding: "80px 0", position: "relative", zIndex: 1 }}>
        <div style={{ maxWidth: 1000, margin: "0 auto", padding: "0 32px" }}>
          <RevealSection>
            <div style={{ textAlign: "center", marginBottom: 56 }}>
              <div style={{ fontSize: 11, fontWeight: 800, color: "#6b5fa0", letterSpacing: "2px", textTransform: "uppercase", marginBottom: 14 }}>
                EVERYTHING YOU NEED
              </div>
              <h2 style={{ fontSize: "clamp(28px, 4vw, 42px)", fontWeight: 900, color: "#18182e", letterSpacing: "-1px", margin: 0 }}>
                Four tools. One glow-up.
              </h2>
              <p style={{ color: "#9898b8", marginTop: 12, fontSize: 15, maxWidth: 500, margin: "12px auto 0" }}>
                Everything a smart Gen Z student needs to build better money habits.
              </p>
            </div>
          </RevealSection>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 20 }}>
            {features.map((f, i) => (
              <RevealSection key={i} delay={i * 0.1}>
                <div style={{
                  background: "#fff", borderRadius: 20, padding: "28px 24px",
                  boxShadow: "0 4px 24px rgba(107,95,160,0.07)",
                  border: "1px solid rgba(107,95,160,0.07)",
                  transition: "transform 0.22s, box-shadow 0.22s",
                  cursor: "default",
                }}
                  onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-5px)"; e.currentTarget.style.boxShadow = "0 16px 48px rgba(107,95,160,0.16)"; }}
                  onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.boxShadow = "0 4px 24px rgba(107,95,160,0.07)"; }}
                >
                  <div style={{ width: 52, height: 52, borderRadius: 16, background: f.bg, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 26, marginBottom: 18, boxShadow: "0 4px 12px rgba(107,95,160,0.1)" }}>
                    {f.icon}
                  </div>
                  <div style={{ fontSize: 10, fontWeight: 800, color: f.color, letterSpacing: "1px", textTransform: "uppercase", marginBottom: 8 }}>
                    {f.stat} {f.statLabel}
                  </div>
                  <h3 style={{ fontSize: 16, fontWeight: 800, color: "#18182e", margin: "0 0 10px", letterSpacing: "-0.3px" }}>{f.title}</h3>
                  <p style={{ fontSize: 12.5, color: "#706d8a", lineHeight: 1.65, margin: 0 }}>{f.desc}</p>
                </div>
              </RevealSection>
            ))}
          </div>
        </div>
      </section>

      {/* ── Testimonials ──────────────────────────────────────────── */}
      <section style={{ background: "#fff", padding: "80px 0", position: "relative", zIndex: 1 }}>
        <div style={{ maxWidth: 1000, margin: "0 auto", padding: "0 32px" }}>
          <RevealSection>
            <div style={{ textAlign: "center", marginBottom: 48 }}>
              <h2 style={{ fontSize: "clamp(26px, 3.5vw, 38px)", fontWeight: 900, color: "#18182e", letterSpacing: "-0.8px", margin: 0 }}>
                Students love it.
              </h2>
            </div>
          </RevealSection>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 18 }}>
            {testimonials.map((t, i) => (
              <RevealSection key={i} delay={i * 0.12}>
                <div style={{
                  background: "linear-gradient(135deg, #faf9ff, #f5f3fc)",
                  borderRadius: 20, padding: "24px 26px",
                  border: "1px solid rgba(107,95,160,0.09)",
                  boxShadow: "0 4px 20px rgba(107,95,160,0.07)",
                }}>
                  <div style={{ fontSize: 22, marginBottom: 14, color: "#c9a96e" }}>❝</div>
                  <p style={{ fontSize: 14, color: "#3d3a52", lineHeight: 1.7, margin: "0 0 20px", fontWeight: 500 }}>
                    {t.text}
                  </p>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{
                      width: 36, height: 36, borderRadius: "50%",
                      background: "linear-gradient(135deg, #6b5fa0, #9b8ec8)",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 14, fontWeight: 800, color: "#fff",
                    }}>{t.avatar}</div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: "#18182e" }}>{t.name}</div>
                      <div style={{ fontSize: 11, color: "#9898b8" }}>{t.college}</div>
                    </div>
                  </div>
                </div>
              </RevealSection>
            ))}
          </div>
        </div>
      </section>

      {/* ── Final CTA ─────────────────────────────────────────────── */}
      <section style={{ padding: "80px 32px", textAlign: "center", position: "relative", zIndex: 1 }}>
        <RevealSection>
          <div style={{
            maxWidth: 640, margin: "0 auto",
            background: "linear-gradient(135deg, #6b5fa0 0%, #8b7dc0 50%, #9b8ec8 100%)",
            backgroundSize: "200% 200%",
            animation: "gradientShift 5s ease infinite",
            borderRadius: 28, padding: "52px 40px",
            position: "relative", overflow: "hidden",
            boxShadow: "0 24px 80px rgba(107,95,160,0.40)",
          }}>
            <div style={{ position: "absolute", top: -60, right: -60, width: 220, height: 220, borderRadius: "50%", background: "rgba(255,255,255,0.06)" }} />
            <div style={{ position: "absolute", bottom: -40, left: -40, width: 160, height: 160, borderRadius: "50%", background: "rgba(255,255,255,0.04)" }} />
            <div style={{ position: "relative", zIndex: 1 }}>
              <div style={{ fontSize: 44, marginBottom: 16 }}>✨</div>
              <h2 style={{ fontSize: "clamp(24px, 4vw, 36px)", fontWeight: 900, color: "#fff", margin: "0 0 14px", letterSpacing: "-0.8px" }}>
                Ready to glow up your finances?
              </h2>
              <p style={{ color: "rgba(255,255,255,0.8)", fontSize: 15, lineHeight: 1.7, margin: "0 0 32px", maxWidth: 440, marginLeft: "auto", marginRight: "auto" }}>
                Join thousands of students who track smarter. Free, fast, and actually works.
              </p>
              <button onClick={onGetStarted} style={{
                background: "#fff", color: "#6b5fa0",
                border: "none", borderRadius: 50,
                padding: "15px 38px", fontSize: 15, fontWeight: 800,
                cursor: "pointer", fontFamily: "inherit",
                boxShadow: "0 8px 32px rgba(0,0,0,0.2)",
                transition: "all 0.22s", letterSpacing: "0.2px",
              }}
                onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px) scale(1.02)"; e.currentTarget.style.boxShadow = "0 14px 44px rgba(0,0,0,0.25)"; }}
                onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0) scale(1)"; e.currentTarget.style.boxShadow = "0 8px 32px rgba(0,0,0,0.2)"; }}
              >
                Create Free Account →
              </button>
              <p style={{ marginTop: 20, fontSize: 12, color: "rgba(255,255,255,0.55)" }}>🔒 Private, secure, and ad-free forever.</p>
            </div>
          </div>
        </RevealSection>
      </section>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Playfair+Display:ital,wght@1,700&display=swap');
        @keyframes float1 { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
        @keyframes float2 { 0%,100%{transform:translateY(0) rotate(1deg)} 50%{transform:translateY(-8px) rotate(-1deg)} }
        @keyframes float3 { 0%,100%{transform:translateY(0) rotate(-1deg)} 50%{transform:translateY(-12px) rotate(1deg)} }
        @keyframes gradientShift { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }
        .hero-cards { display: none !important; }
        @media(min-width: 860px) { .hero-cards { display: block !important; } }
      `}</style>
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────────────────── */
function FloatingMiniCard({ style, children }) {
  return (
    <div style={{
      position: "absolute",
      background: "rgba(255,255,255,0.88)",
      backdropFilter: "blur(20px)",
      border: "1px solid rgba(255,255,255,0.7)",
      borderRadius: 18, padding: "14px 16px",
      boxShadow: "0 12px 40px rgba(107,95,160,0.18)",
      fontFamily: "'Outfit', sans-serif",
      ...style,
    }}>
      {children}
    </div>
  );
}

function StoryContent({ eyebrow, title, body, color }) {
  return (
    <div>
      <div style={{ fontSize: 10, fontWeight: 800, color, letterSpacing: "1.5px", textTransform: "uppercase", marginBottom: 14 }}>{eyebrow}</div>
      <h2 style={{ fontSize: "clamp(24px, 3.5vw, 36px)", fontWeight: 900, color: "#18182e", letterSpacing: "-0.8px", margin: "0 0 18px", lineHeight: 1.15 }}>
        {title}
      </h2>
      <p style={{ fontSize: 15, color: "#5a5880", lineHeight: 1.75, margin: 0 }}>{body}</p>
    </div>
  );
}

function ExpenseVisual() {
  return (
    <div style={{ background: "#fff", borderRadius: 20, padding: 24, boxShadow: "0 8px 36px rgba(107,95,160,0.12)", border: "1px solid rgba(107,95,160,0.08)" }}>
      {[{ cat: "🍱 Food", pct: 38, val: "₹3,800", color: "#6b5fa0" }, { cat: "🚗 Transport", pct: 22, val: "₹2,200", color: "#9b8ec8" }, { cat: "🛍️ Shopping", pct: 28, val: "₹2,800", color: "#c9a96e" }, { cat: "💊 Health", pct: 12, val: "₹1,200", color: "#5aaa82" }].map((row, i) => (
        <div key={i} style={{ marginBottom: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 6 }}>
            <span style={{ color: "#3d3a52", fontWeight: 600 }}>{row.cat}</span>
            <span style={{ color: "#6b5fa0", fontWeight: 700 }}>{row.val}</span>
          </div>
          <div style={{ background: "#f5f3fc", borderRadius: 100, height: 8, overflow: "hidden" }}>
            <div style={{ width: `${row.pct}%`, height: "100%", background: row.color, borderRadius: 100, transition: "width 1s ease" }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function WardrobeVisual() {
  return (
    <div style={{ background: "#fff", borderRadius: 20, padding: 20, boxShadow: "0 8px 36px rgba(107,95,160,0.12)", border: "1px solid rgba(107,95,160,0.08)", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
      {[
        { emoji: "👗", name: "Black Dress", wears: 8, cpw: "₹125", badge: "Best Value", badgeColor: "#5aaa82" },
        { emoji: "👕", name: "White Tee", wears: 14, cpw: "₹36", badge: "🔥 Most Worn", badgeColor: "#6b5fa0" },
        { emoji: "👖", name: "Blue Jeans", wears: 6, cpw: "₹200", badge: "Good", badgeColor: "#c9a96e" },
        { emoji: "🧥", name: "Blazer", wears: 0, cpw: "—", badge: "⚠ Unworn", badgeColor: "#d96b6b" },
      ].map((item, i) => (
        <div key={i} style={{ background: "#faf9ff", borderRadius: 14, padding: "12px 14px", border: "1px solid rgba(107,95,160,0.08)" }}>
          <div style={{ fontSize: 26, marginBottom: 6 }}>{item.emoji}</div>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#18182e", marginBottom: 2 }}>{item.name}</div>
          <div style={{ fontSize: 10, color: "#9898b8", marginBottom: 6 }}>{item.wears}× worn · {item.cpw}/wear</div>
          <span style={{ fontSize: 9, fontWeight: 800, padding: "2px 7px", borderRadius: 100, background: `${item.badgeColor}15`, color: item.badgeColor }}>{item.badge}</span>
        </div>
      ))}
    </div>
  );
}

function InsightVisual() {
  return (
    <div style={{ background: "#fff", borderRadius: 20, padding: 20, boxShadow: "0 8px 36px rgba(107,95,160,0.12)", border: "1px solid rgba(107,95,160,0.08)", display: "flex", flexDirection: "column", gap: 12 }}>
      {[
        { icon: "🚨", text: "You've used 88% of your budget. Slow down!", bg: "#fff8f8", border: "#fad5d5", badge: "Alert" },
        { icon: "📈", text: "Spending rose 23% vs last month — mostly food delivery.", bg: "#fffbf0", border: "#f5e4b8", badge: "Trend" },
        { icon: "✅", text: "Your black tee costs ₹4/wear — best value in your wardrobe!", bg: "#f0fbf4", border: "#b8e8cc", badge: "Insight" },
      ].map((ins, i) => (
        <div key={i} style={{ background: ins.bg, border: `1px solid ${ins.border}`, borderRadius: 12, padding: "12px 14px", display: "flex", gap: 10, alignItems: "flex-start" }}>
          <span style={{ fontSize: 18, flexShrink: 0 }}>{ins.icon}</span>
          <span style={{ fontSize: 12, color: "#3d3a52", lineHeight: 1.55 }}>{ins.text}</span>
        </div>
      ))}
    </div>
  );
}