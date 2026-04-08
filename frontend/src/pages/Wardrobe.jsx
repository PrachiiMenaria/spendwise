// fenora/frontend/src/pages/Wardrobe.jsx
import { useState, useEffect } from "react";

const API = "http://localhost:5000";

function formatINR(n) {
  return "₹" + Number(n || 0).toLocaleString("en-IN");
}

const CATEGORIES = ["Tops", "Bottoms", "Dresses", "Outerwear", "Footwear", "Accessories", "Ethnic", "Formals", "Other"];
const COLORS = ["Black", "White", "Blue", "Red", "Green", "Yellow", "Pink", "Grey", "Brown", "Other"];

const CATEGORY_EMOJIS = {
  Tops: "👕", Bottoms: "👖", Dresses: "👗", Outerwear: "🧥",
  Footwear: "👟", Accessories: "👜", Ethnic: "🥻", Formals: "👔", Other: "🧺",
};

const COLOR_SWATCHES = {
  Black: "#1a1a1a", White: "#f5f5f5", Blue: "#4a90d9", Red: "#e07070",
  Green: "#6aaa8a", Yellow: "#f5c842", Pink: "#f0a0c0", Grey: "#9898a8",
  Brown: "#a0785a", Other: "#c8c8c8",
};

const CATEGORY_BG = {
  Tops: "#f0eef8", Bottoms: "#e8f4fd", Dresses: "#fde8f8", Outerwear: "#fdf0e8",
  Footwear: "#e8fdf0", Accessories: "#fdf8e8", Ethnic: "#fce8f8", Formals: "#e8f0fd", Other: "#f0f0f0",
};

export default function Wardrobe() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [filter, setFilter] = useState("All");
  const [form, setForm] = useState({ item_name: "", category: "Tops", color: "Black", purchase_price: "" });

  const fetchItems = async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetch(`${API}/api/wardrobe`, { credentials: "include" });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      setItems(Array.isArray(data) ? data : []);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchItems(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.item_name.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/api/wardrobe`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ ...form, purchase_price: parseFloat(form.purchase_price) || 0 }),
      });
      if (!res.ok) throw new Error("Failed to add item");
      setForm({ item_name: "", category: "Tops", color: "Black", purchase_price: "" });
      setShowForm(false);
      await fetchItems();
    } catch (err) { setError(err.message); }
    finally { setSubmitting(false); }
  };

  const handleDelete = async (id) => {
    if (!confirm("Remove this item?")) return;
    try {
      await fetch(`${API}/api/wardrobe/${id}`, { method: "DELETE", credentials: "include" });
      setItems(prev => prev.filter(i => i.id !== id));
    } catch (err) { setError(err.message); }
  };

  const handleWear = async (id) => {
    try {
      await fetch(`${API}/api/log-wear/${id}`, { method: "POST", credentials: "include" });
      setItems(prev => prev.map(i => i.id === id ? { ...i, wear_count: (i.wear_count || 0) + 1 } : i));
    } catch {}
  };

  const categories = ["All", ...new Set(items.map(i => i.category).filter(Boolean))];
  const filtered = filter === "All" ? items : items.filter(i => i.category === filter);
  const neverWorn = items.filter(i => (i.wear_count || 0) === 0).length;
  const totalValue = items.reduce((s, i) => s + parseFloat(i.purchase_price || 0), 0);
  const totalWears = items.reduce((s, i) => s + (i.wear_count || 0), 0);
  const avgCPW = items.filter(i => (i.wear_count || 0) > 0 && parseFloat(i.purchase_price || 0) > 0)
    .map(i => parseFloat(i.purchase_price) / i.wear_count);
  const avgCostPerWear = avgCPW.length > 0 ? avgCPW.reduce((a, b) => a + b, 0) / avgCPW.length : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: "#1a1a2e", margin: 0, letterSpacing: "-0.5px" }}>My Wardrobe 👗</h1>
          <p style={{ color: "#9898b8", marginTop: 4, fontSize: 13 }}>Track your clothes, utilization & cost-per-wear</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} style={{
          background: showForm ? "#f0eef8" : "linear-gradient(135deg,#7c6fa0,#a89cc8)",
          color: showForm ? "#7c6fa0" : "#fff", border: "none", borderRadius: 50,
          padding: "10px 22px", fontSize: 13, fontWeight: 700, cursor: "pointer",
          boxShadow: showForm ? "none" : "0 4px 16px rgba(124,111,160,0.3)",
          transition: "all 0.2s", fontFamily: "inherit",
        }}>
          {showForm ? "✕ Cancel" : "+ Add Item"}
        </button>
      </div>

      {/* Summary Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12 }}>
        {[
          { label: "Total Items", value: items.length, icon: "👚", color: "#7c6fa0", sub: "in wardrobe" },
          { label: "Never Worn", value: neverWorn, icon: "😴", color: neverWorn > 0 ? "#e07070" : "#6aaa8a", sub: neverWorn > 0 ? "sitting idle" : "All worn ✓" },
          { label: "Total Value", value: formatINR(totalValue), icon: "💎", color: "#c9a96e", sub: "invested" },
          { label: "Avg Cost/Wear", value: avgCostPerWear > 0 ? formatINR(Math.round(avgCostPerWear)) : "—", icon: "✨", color: "#6aaa8a", sub: "per wear avg" },
        ].map((c, i) => (
          <div key={i} style={{
            background: "#fff", borderRadius: 14, padding: "14px 16px 12px",
            boxShadow: "0 2px 12px rgba(124,111,160,0.07)",
            border: "1px solid rgba(124,111,160,0.08)", position: "relative", overflow: "hidden",
            animation: `fadeUp 0.4s ease both`, animationDelay: `${i * 0.06}s`,
          }}>
            <div style={{ position: "absolute", top: 10, right: 12, fontSize: 18, opacity: 0.6 }}>{c.icon}</div>
            <div style={{ fontSize: 9, color: "#9898b8", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 4 }}>{c.label}</div>
            <div style={{ fontSize: 19, fontWeight: 800, color: c.color }}>{c.value}</div>
            <div style={{ fontSize: 10, color: "#b0aec8", marginTop: 3 }}>{c.sub}</div>
          </div>
        ))}
      </div>

      {/* AI Wardrobe Tips */}
      {neverWorn > 0 && (
        <div style={{ background: "linear-gradient(135deg,#fffbf0,#fff8f8)", border: "1px solid #f5e4b8", borderRadius: 14, padding: "14px 16px", display: "flex", gap: 12, alignItems: "flex-start" }}>
          <span style={{ fontSize: 22, flexShrink: 0 }}>🧠</span>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#1a1a2e", marginBottom: 4 }}>Wardrobe Intelligence</div>
            <p style={{ fontSize: 12, color: "#6b6888", lineHeight: 1.6, margin: 0 }}>
              You have <strong style={{ color: "#e07070" }}>{neverWorn} unworn item{neverWorn > 1 ? "s" : ""}</strong> worth {formatINR(items.filter(i => (i.wear_count || 0) === 0).reduce((s, i) => s + parseFloat(i.purchase_price || 0), 0))} sitting idle.
              Wear them before buying anything new — you'll save money and discover forgotten favourites!
            </p>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={{ background: "#fff8f8", border: "1px solid #fad5d5", borderRadius: 12, padding: "12px 16px", display: "flex", gap: 10, alignItems: "center" }}>
          <span>⚠️</span><span style={{ fontSize: 13, color: "#e07070" }}>{error}</span>
        </div>
      )}

      {/* Add Form */}
      {showForm && (
        <div style={{
          background: "#fff", borderRadius: 18, padding: "22px",
          boxShadow: "0 4px 24px rgba(124,111,160,0.12)",
          border: "1px solid #e8e4f5", animation: "fadeUp 0.3s ease both",
        }}>
          <h3 style={{ margin: "0 0 16px", fontSize: 15, fontWeight: 700, color: "#1a1a2e" }}>Add New Item</h3>
          <form onSubmit={handleSubmit}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
              <div style={{ gridColumn: "1 / -1" }}>
                <label style={labelStyle}>Item Name *</label>
                <input style={inputStyle} placeholder="e.g. Blue Denim Jacket" value={form.item_name}
                  onChange={e => setForm({ ...form, item_name: e.target.value })} required />
              </div>
              <div>
                <label style={labelStyle}>Purchase Price (₹)</label>
                <input style={inputStyle} type="number" placeholder="0" value={form.purchase_price}
                  onChange={e => setForm({ ...form, purchase_price: e.target.value })} />
              </div>
              <div>
                <label style={labelStyle}>Category</label>
                <select style={inputStyle} value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}>
                  {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div style={{ gridColumn: "1 / -1" }}>
                <label style={labelStyle}>Color</label>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {COLORS.map(c => (
                    <button key={c} type="button" onClick={() => setForm({ ...form, color: c })} style={{
                      width: 28, height: 28, borderRadius: "50%",
                      background: COLOR_SWATCHES[c] || "#ccc",
                      border: form.color === c ? "3px solid #7c6fa0" : "2px solid rgba(0,0,0,0.1)",
                      cursor: "pointer", flexShrink: 0, transition: "transform 0.15s",
                      transform: form.color === c ? "scale(1.2)" : "scale(1)",
                    }} title={c} />
                  ))}
                </div>
              </div>
            </div>
            <button type="submit" disabled={submitting} style={{
              width: "100%", background: "linear-gradient(135deg,#7c6fa0,#a89cc8)",
              color: "#fff", border: "none", borderRadius: 12, padding: "11px",
              fontSize: 13, fontWeight: 700, cursor: submitting ? "not-allowed" : "pointer",
              opacity: submitting ? 0.7 : 1, fontFamily: "inherit",
            }}>
              {submitting ? "Adding…" : "Add to Wardrobe"}
            </button>
          </form>
        </div>
      )}

      {/* Category Filter */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {categories.map(cat => (
          <button key={cat} onClick={() => setFilter(cat)} style={{
            padding: "6px 14px", borderRadius: 100, fontSize: 11, fontWeight: 600,
            border: filter === cat ? "none" : "1.5px solid #e8e4f5",
            background: filter === cat ? "linear-gradient(135deg,#7c6fa0,#a89cc8)" : "#fff",
            color: filter === cat ? "#fff" : "#9898b8",
            cursor: "pointer", transition: "all 0.2s", fontFamily: "inherit",
          }}>
            {CATEGORY_EMOJIS[cat] || ""} {cat}
          </button>
        ))}
      </div>

      {/* Items Grid - COMPACT 3-col layout */}
      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "40px 0" }}>
          <div style={{ width: 32, height: 32, borderRadius: "50%", border: "4px solid #e8e4f3", borderTopColor: "#7c6fa0", animation: "spin 0.9s linear infinite" }} />
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12 }}>

          {/* Add Item Card (glassmorphism) - First in grid */}
          <button onClick={() => setShowForm(true)} style={{
            background: "rgba(248,246,255,0.7)",
            backdropFilter: "blur(12px)",
            border: "1.5px dashed rgba(124,111,160,0.3)",
            borderRadius: 14, padding: "20px 16px",
            display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
            gap: 8, cursor: "pointer", fontFamily: "inherit",
            transition: "all 0.2s", minHeight: 160,
          }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = "#7c6fa0"; e.currentTarget.style.background = "rgba(124,111,160,0.06)"; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = "rgba(124,111,160,0.3)"; e.currentTarget.style.background = "rgba(248,246,255,0.7)"; }}
          >
            <div style={{ width: 36, height: 36, borderRadius: "50%", background: "rgba(124,111,160,0.1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>+</div>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#7c6fa0", textAlign: "center" }}>Add Item</div>
            <div style={{ fontSize: 10, color: "#b0aec8", textAlign: "center" }}>Track something new</div>
          </button>

          {filtered.length === 0 ? null : filtered.map((item, i) => {
            const wearCount = item.wear_count || 0;
            const price = parseFloat(item.purchase_price || 0);
            const cpw = wearCount > 0 && price > 0 ? price / wearCount : 0;
            const neverWornItem = wearCount === 0;
            const catBg = CATEGORY_BG[item.category] || "#f0f0f0";
            return (
              <div key={item.id} style={{
                background: "#fff", borderRadius: 14,
                boxShadow: "0 2px 12px rgba(124,111,160,0.07)",
                border: neverWornItem ? "1.5px solid rgba(224,112,112,0.2)" : "1px solid rgba(124,111,160,0.08)",
                overflow: "hidden",
                animation: `fadeUp 0.35s ease both`, animationDelay: `${i * 0.035}s`,
                transition: "box-shadow 0.2s, transform 0.2s",
                display: "flex", flexDirection: "column",
              }}
                onMouseEnter={e => { e.currentTarget.style.boxShadow = "0 6px 22px rgba(124,111,160,0.13)"; e.currentTarget.style.transform = "translateY(-2px)"; }}
                onMouseLeave={e => { e.currentTarget.style.boxShadow = "0 2px 12px rgba(124,111,160,0.07)"; e.currentTarget.style.transform = "translateY(0)"; }}
              >
                {/* Card Header */}
                <div style={{
                  background: catBg, padding: "14px 14px 10px",
                  display: "flex", alignItems: "center", gap: 10, position: "relative",
                }}>
                  <div style={{ fontSize: 28, flexShrink: 0 }}>{CATEGORY_EMOJIS[item.category] || "👕"}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 800, color: "#1a1a2e", fontSize: 12, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {item.item_name}
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 5, marginTop: 3 }}>
                      <div style={{ width: 8, height: 8, borderRadius: "50%", background: COLOR_SWATCHES[item.color] || "#ccc", border: "1.5px solid rgba(0,0,0,0.1)", flexShrink: 0 }} />
                      <span style={{ fontSize: 10, color: "#9898b8" }}>{item.color}</span>
                    </div>
                  </div>
                  {neverWornItem && (
                    <div style={{ position: "absolute", top: 8, right: 8, fontSize: 8, background: "#fdf0f0", color: "#e07070", padding: "2px 6px", borderRadius: 100, fontWeight: 800 }}>UNWORN</div>
                  )}
                </div>

                {/* Card Body */}
                <div style={{ padding: "10px 14px 12px", flex: 1, display: "flex", flexDirection: "column", gap: 8 }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
                    <div style={{ background: "#faf9ff", borderRadius: 8, padding: "6px 8px" }}>
                      <div style={{ fontSize: 8, color: "#9898b8", fontWeight: 700, textTransform: "uppercase", marginBottom: 2 }}>Price</div>
                      <div style={{ fontSize: 12, fontWeight: 800, color: "#7c6fa0" }}>{price > 0 ? formatINR(price) : "—"}</div>
                    </div>
                    <div style={{ background: "#faf9ff", borderRadius: 8, padding: "6px 8px" }}>
                      <div style={{ fontSize: 8, color: "#9898b8", fontWeight: 700, textTransform: "uppercase", marginBottom: 2 }}>Wears</div>
                      <div style={{ fontSize: 12, fontWeight: 800, color: "#6aaa8a" }}>{wearCount}×</div>
                    </div>
                  </div>
                  {cpw > 0 && (
                    <div style={{ fontSize: 10, color: "#9898b8" }}>
                      ₹{Math.round(cpw)}/wear · <span style={{ color: cpw < 100 ? "#6aaa8a" : cpw < 300 ? "#c9a96e" : "#e07070", fontWeight: 600 }}>{cpw < 100 ? "Great value" : cpw < 300 ? "Fair" : "Underused"}</span>
                    </div>
                  )}
                  <div style={{ display: "flex", gap: 6, marginTop: "auto" }}>
                    <button onClick={() => handleWear(item.id)} style={{
                      flex: 1, background: "linear-gradient(135deg,#7c6fa0,#a89cc8)",
                      color: "#fff", border: "none", borderRadius: 8,
                      padding: "7px 0", fontSize: 11, fontWeight: 700, cursor: "pointer", fontFamily: "inherit",
                    }}>+1 Wear</button>
                    <button onClick={() => handleDelete(item.id)} style={{
                      background: "#fff8f8", border: "1px solid #fad5d5",
                      borderRadius: 8, padding: "7px 10px", color: "#e07070",
                      fontSize: 11, cursor: "pointer", fontFamily: "inherit",
                    }}>✕</button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Empty state when no items at all */}
      {!loading && filtered.length === 0 && items.length === 0 && (
        <div style={{ textAlign: "center", padding: "40px 0", opacity: 0.6 }}>
          <div style={{ fontSize: 40 }}>👚</div>
          <p style={{ color: "#9898b8", marginTop: 10, fontSize: 13 }}>No items yet. Click "Add Item" to start building your wardrobe!</p>
        </div>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}

const labelStyle = { display: "block", fontSize: 10, fontWeight: 700, color: "#9898b8", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 6 };
const inputStyle = {
  width: "100%", padding: "9px 12px", borderRadius: 10, border: "1.5px solid #e8e4f5",
  fontSize: 13, color: "#1a1a2e", background: "#faf9ff", outline: "none",
  fontFamily: "inherit", boxSizing: "border-box",
};