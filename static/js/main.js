/* ═══════════════════════════════════════════════
   SpendWise — Global Script
   GSAP + ScrollTrigger + Chart.js + Fetch helpers
   ═══════════════════════════════════════════════ */

/* ── COLOUR PALETTE for Chart.js ── */
const PALETTE = ['#A8896A','#C9A84C','#8B6F52','#6E5540','#D4B896','#52402F','#E8D5A3','#B8956A'];
const PALETTE_DANGER = '#C0392B';
const PALETTE_WARN   = '#B7770D';
const PALETTE_SAFE   = '#2E7D5B';

/* ══════════════════════════════════════
   1. SCROLL REVEAL (IntersectionObserver)
══════════════════════════════════════ */
function initReveal() {
  const els = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
  if (!els.length) return;
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  els.forEach(el => io.observe(el));
}

/* ══════════════════════════════════════
   2. GSAP PAGE ENTRANCE (if GSAP loaded)
══════════════════════════════════════ */
function initGSAP() {
  if (typeof gsap === 'undefined') return;
  gsap.registerPlugin(ScrollTrigger);

  // Hero section entrance
  const hero = document.querySelector('.hero-section');
  if (hero) {
    gsap.from(hero.querySelectorAll('.hero-eyebrow, .hero-title, .hero-subtitle, .hero-month-badge'), {
      y: 30, opacity: 0, duration: 0.8, stagger: 0.12,
      ease: 'power3.out', delay: 0.15
    });
  }

  // KPI cards stagger on scroll
  const kpiCards = document.querySelectorAll('.kpi-card');
  if (kpiCards.length) {
    gsap.from(kpiCards, {
      scrollTrigger: { trigger: '.kpi-grid', start: 'top 85%' },
      y: 40, opacity: 0, duration: 0.65,
      stagger: 0.1, ease: 'power2.out'
    });
  }

  // Cards stagger
  document.querySelectorAll('.card, .glass-card').forEach((card, i) => {
    gsap.from(card, {
      scrollTrigger: { trigger: card, start: 'top 88%' },
      y: 24, opacity: 0, duration: 0.55,
      delay: (i % 3) * 0.08,
      ease: 'power2.out'
    });
  });

  // Story insight
  const story = document.querySelector('.story-insight');
  if (story) {
    gsap.from(story, {
      scrollTrigger: { trigger: story, start: 'top 85%' },
      x: -30, opacity: 0, duration: 0.7, ease: 'power3.out'
    });
  }

  // Insight items
  gsap.utils.toArray('.insight-item').forEach((item, i) => {
    gsap.from(item, {
      scrollTrigger: { trigger: item, start: 'top 90%' },
      x: -20, opacity: 0, duration: 0.5,
      delay: i * 0.07, ease: 'power2.out'
    });
  });
}

/* ══════════════════════════════════════
   3. COUNT-UP ANIMATION
══════════════════════════════════════ */
function countUp(el, from, to, duration, prefix, suffix) {
  const start = performance.now();
  const diff = to - from;
  const isCurrency = prefix === '₹';
  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    const current = from + diff * ease;
    if (isCurrency) {
      el.textContent = prefix + Math.round(current).toLocaleString('en-IN') + suffix;
    } else {
      el.textContent = prefix + current.toFixed(1) + suffix;
    }
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function initCountUps() {
  document.querySelectorAll('[data-countup]').forEach(el => {
    const to      = parseFloat(el.dataset.countup) || 0;
    const from    = parseFloat(el.dataset.from)    || 0;
    const dur     = parseFloat(el.dataset.dur)     || 1400;
    const prefix  = el.dataset.prefix || '';
    const suffix  = el.dataset.suffix || '';
    const io = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        countUp(el, from, to, dur, prefix, suffix);
        io.disconnect();
      }
    }, { threshold: 0.5 });
    io.observe(el);
  });
}

/* ══════════════════════════════════════
   4. PROGRESS BAR ANIMATION
══════════════════════════════════════ */
function initProgressBars() {
  document.querySelectorAll('.prog-fill, .health-fill').forEach(bar => {
    const target = bar.dataset.pct || bar.style.width;
    bar.style.width = '0';
    const io = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        requestAnimationFrame(() => { bar.style.width = target; });
        io.disconnect();
      }
    }, { threshold: 0.3 });
    io.observe(bar);
  });
}

/* ══════════════════════════════════════
   5. CHART HELPERS
══════════════════════════════════════ */
Chart.defaults.font.family = "'Poppins', sans-serif";
Chart.defaults.color = '#A8896A';

function spendPieChart(canvasId, labels, values) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: PALETTE,
        borderWidth: 2,
        borderColor: '#FAF7F2',
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#2C1F14',
          titleColor: '#FAF7F2',
          bodyColor: '#C9A84C',
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            label: ctx => ` ₹${ctx.parsed.toLocaleString('en-IN')}`
          }
        }
      },
      animation: { animateRotate: true, duration: 900, easing: 'easeInOutQuart' }
    }
  });
}

function spendBarChart(canvasId, labels, datasets) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  return new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#A8896A', font: { size: 11 } }
        },
        y: {
          grid: { color: 'rgba(168,137,106,0.1)', drawBorder: false },
          ticks: {
            color: '#A8896A', font: { size: 11 },
            callback: v => '₹' + (v >= 1000 ? (v/1000).toFixed(0)+'k' : v)
          }
        }
      },
      animation: { duration: 900, easing: 'easeInOutQuart' }
    }
  });
}

function trendLineChart(canvasId, labels, values) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        data: values,
        borderColor: '#C9A84C',
        backgroundColor: 'rgba(201,168,76,0.1)',
        fill: true,
        tension: 0.45,
        pointBackgroundColor: '#C9A84C',
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#A8896A', font: { size: 11 } } },
        y: {
          grid: { color: 'rgba(168,137,106,0.1)' },
          ticks: { color: '#A8896A', font: { size: 11 }, callback: v => '₹' + (v >= 1000 ? (v/1000).toFixed(0)+'k' : v) }
        }
      },
      animation: { duration: 900 }
    }
  });
}

function cpwBarChart(canvasId, labels, values) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  const colors = values.map(v => v > 500 ? PALETTE_DANGER : v > 200 ? PALETTE_WARN : PALETTE_SAFE);
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        borderRadius: 6,
        borderSkipped: false
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { color: 'rgba(168,137,106,0.1)' },
          ticks: { color: '#A8896A', font: { size: 11 }, callback: v => '₹' + v }
        },
        y: { grid: { display: false }, ticks: { color: '#A8896A', font: { size: 11 } } }
      },
      animation: { duration: 900 }
    }
  });
}

/* ══════════════════════════════════════
   6. FETCH HELPERS
══════════════════════════════════════ */
async function fetchJSON(url) {
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error('Network error');
    return await r.json();
  } catch (e) {
    console.error('Fetch error:', url, e);
    return null;
  }
}

/* Load expense category chart */
async function loadExpensePieChart(canvasId, month, year) {
  const data = await fetchJSON(`/api/chart/expense-by-category?month=${month}&year=${year}`);
  if (!data || !data.labels.length) {
    const c = document.getElementById(canvasId);
    if (c) c.closest('.chart-wrap').innerHTML = '<div class="empty-state" style="padding:32px;text-align:center;color:#C9B99A;font-size:13px">No expense data for this month</div>';
    return;
  }
  spendPieChart(canvasId, data.labels, data.values);
}

/* Load trend chart */
async function loadTrendChart(canvasId) {
  const data = await fetchJSON('/api/chart/expense-trend');
  if (!data) return;
  trendLineChart(canvasId, data.labels, data.values);
}

/* Load spending vs budget chart */
async function loadBudgetChart(canvasId) {
  const data = await fetchJSON('/api/chart/spending-vs-budget');
  if (!data || !data.labels.length) return;
  spendBarChart(canvasId, data.labels, [
    { label: 'Budget',    data: data.budget,    backgroundColor: 'rgba(201,168,76,0.5)',  borderRadius: 6 },
    { label: 'Predicted', data: data.predicted, backgroundColor: 'rgba(168,137,106,0.8)', borderRadius: 6 }
  ]);
}

/* Load CPW chart */
async function loadCPWChart(canvasId) {
  const data = await fetchJSON('/api/chart/cpw-by-category');
  if (!data || !data.labels.length) return;
  cpwBarChart(canvasId, data.labels, data.values);
}

/* Load category distribution (wardrobe) */
async function loadCatDistChart(canvasId) {
  const data = await fetchJSON('/api/chart/category-distribution');
  if (!data) return;
  spendPieChart(canvasId, data.labels, data.values);
}

/* ══════════════════════════════════════
   7. FLASH DISMISS
══════════════════════════════════════ */
function initFlashDismiss() {
  document.querySelectorAll('.flash-msg').forEach(msg => {
    setTimeout(() => {
      msg.style.transition = 'opacity 0.5s, transform 0.5s';
      msg.style.opacity = '0';
      msg.style.transform = 'translateY(-8px)';
      setTimeout(() => msg.remove(), 500);
    }, 4000);
  });
}

/* ══════════════════════════════════════
   8. SIDEBAR MOBILE TOGGLE
══════════════════════════════════════ */
function initSidebarToggle() {
  const btn = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar');
  if (btn && sidebar) {
    btn.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', (e) => {
      if (!sidebar.contains(e.target) && !btn.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }
}

/* ══════════════════════════════════════
   9. ACTIVE NAV HIGHLIGHT
══════════════════════════════════════ */
function initActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && (path === href || path.startsWith(href + '/') && href !== '/')) {
      link.classList.add('active');
    }
  });
}

/* ══════════════════════════════════════
   10. CATEGORY SELECTOR (expense add)
══════════════════════════════════════ */
function initCategorySelector() {
  const btns = document.querySelectorAll('.category-btn');
  const hiddenInput = document.getElementById('categoryInput');
  if (!btns.length) return;
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      btns.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      if (hiddenInput) hiddenInput.value = btn.dataset.cat;
    });
  });
}

/* ══════════════════════════════════════
   11. SUCCESS OVERLAY
══════════════════════════════════════ */
function showSuccess() {
  const overlay = document.getElementById('successOverlay');
  if (overlay) {
    overlay.classList.add('show');
    setTimeout(() => {
      overlay.classList.remove('show');
    }, 2500);
  }
}

/* ══════════════════════════════════════
   12. SPENDING ALERT FORM LOADER FIX
══════════════════════════════════════ */
function initSpendingAlertForm() {
  const form = document.getElementById('spendingAlertForm');
  const btn  = document.getElementById('analyzeBtn');
  const spin = document.getElementById('analyzeSpinner');
  if (!form || !btn) return;
  form.addEventListener('submit', () => {
    btn.disabled = true;
    if (spin) spin.style.display = 'inline-block';
    btn.textContent = 'Analyzing…';
  });
}

/* ══════════════════════════════════════
   13. MONTH FILTER (expense list)
══════════════════════════════════════ */
function initMonthFilter() {
  const sel = document.getElementById('monthYearSelect');
  if (!sel) return;
  sel.addEventListener('change', () => {
    const [month, year] = sel.value.split('-');
    window.location.href = `/expenses?month=${month}&year=${year}`;
  });
}

/* ══════════════════════════════════════
   INIT ALL
══════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  initReveal();
  initGSAP();
  initCountUps();
  initProgressBars();
  initFlashDismiss();
  initSidebarToggle();
  initActiveNav();
  initCategorySelector();
  initSpendingAlertForm();
  initMonthFilter();
});