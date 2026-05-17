<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SCADA — Analizador de Red</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --blue:    #378ADD;
    --amber:   #BA7517;
    --green:   #639922;
    --teal:    #1D9E75;
    --coral:   #D85A30;
    --purple:  #7F77DD;
    --bg-page: #F4F3EE;
    --bg-card: #FFFFFF;
    --border:  #D3D1C7;
    --text-sec:#888780;
    --text-ter:#B4B2A9;
    --ok-bg:   #EAF3DE;
    --ok-txt:  #3B6D11;
    --warn-bg: #FAEEDA;
    --warn-txt:#854F0B;
    --mono: 'JetBrains Mono', monospace;
    --sans: 'DM Sans', sans-serif;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: var(--sans);
    background: var(--bg-page);
    color: #2B2B2A;
    min-height: 100vh;
    padding: 20px;
  }

  /* ── Header ── */
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }
  .header-left { display: flex; align-items: center; gap: 10px; }
  .dot-online  { width: 10px; height: 10px; border-radius: 50%; background: var(--ok-txt); }
  .header-title { font-size: 15px; font-weight: 500; }
  .badge-online {
    background: var(--ok-bg); color: var(--ok-txt);
    font-size: 12px; font-weight: 500;
    padding: 3px 10px; border-radius: 6px;
  }
  .header-ts { font-size: 12px; color: var(--text-sec); font-family: var(--mono); }

  /* ── Section titles ── */
  .section-title {
    font-size: 11px; font-weight: 500; letter-spacing: .08em;
    color: var(--text-sec); text-transform: uppercase;
    padding: 16px 0 8px;
  }

  /* ── Cards grid ── */
  .cards-row { display: flex; gap: 12px; }
  .metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    flex: 1;
    transition: box-shadow .2s;
  }
  .metric-card:hover { box-shadow: 0 2px 12px #0000000d; }
  .card-accent { height: 2px; border-radius: 2px; margin-bottom: 8px; }
  .card-label  { font-size: 12px; color: var(--text-sec); margin-bottom: 4px; }
  .card-value  {
    font-family: var(--mono);
    font-size: 24px; font-weight: 500;
    display: flex; align-items: baseline; gap: 4px;
  }
  .card-unit   { font-size: 13px; color: var(--text-sec); font-family: var(--sans); }
  .card-sub    { font-size: 11px; color: var(--text-ter); margin-top: 4px; }

  /* ── Charts row ── */
  .charts-row { display: flex; gap: 12px; }
  .chart-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    flex: 1;
    cursor: pointer;
    transition: box-shadow .2s, transform .1s;
  }
  .chart-card:hover {
    box-shadow: 0 4px 16px #0000001a;
    transform: translateY(-1px);
  }
  .chart-header {
    display: flex; justify-content: space-between;
    align-items: center; margin-bottom: 8px;
  }
  .chart-title { font-size: 13px; font-weight: 500; }
  .legend { display: flex; gap: 12px; align-items: center; }
  .legend-item { display: flex; align-items: center; gap: 4px; font-size: 11px; color: var(--text-sec); }
  .legend-dot  { width: 8px; height: 8px; border-radius: 50%; }
  .chart-img   { width: 100%; height: 130px; display: block; }
  .chart-hint  {
    font-size: 10px; color: var(--blue); font-weight: 500;
    font-style: italic; text-align: right; margin-top: 6px;
  }

  /* ── Weekly card ── */
  .weekly-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
  }
  .weekly-top  { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
  .weekly-total-label { font-size: 12px; color: var(--text-sec); margin-bottom: 4px; }
  .weekly-total-val   {
    font-family: var(--mono);
    font-size: 26px; font-weight: 500;
    display: flex; align-items: baseline; gap: 4px;
  }
  .weekly-total-unit  { font-size: 13px; color: var(--text-sec); font-family: var(--sans); }
  .weekly-right { text-align: right; }
  .weekly-avg-label { font-size: 11px; color: var(--text-ter); }
  .weekly-avg-val   { font-size: 15px; font-weight: 500; font-family: var(--mono); }
  .weekly-today-val { font-size: 11px; color: var(--text-ter); }

  .bars-row { display: flex; justify-content: space-between; align-items: flex-end; }
  .day-col  { display: flex; flex-direction: column; align-items: center; gap: 3px; }
  .bar-wrap {
    width: 36px; height: 80px;
    background: #E8E7E0; border-radius: 4px;
    overflow: hidden; position: relative;
  }
  .bar-fill {
    position: absolute; bottom: 0; left: 0; right: 0;
    border-radius: 4px 4px 0 0;
    transition: height .5s ease;
  }
  .day-lbl  { font-size: 10px; color: var(--text-sec); }
  .day-val  { font-size: 10px; font-weight: 500; font-family: var(--mono); }
  .day-unit { font-size: 9px; color: var(--text-ter); }

  /* ── Alarms card ── */
  .alarms-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 4px 16px;
  }
  .alarm-row {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
  }
  .alarm-row:last-child { border-bottom: none; }
  .alarm-icon {
    width: 24px; height: 24px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; flex-shrink: 0;
  }
  .alarm-text  { flex: 1; font-size: 13px; }
  .alarm-detail{ font-size: 12px; color: var(--text-sec); font-family: var(--mono); }

  /* ── Modal ── */
  .modal-overlay {
    display: none; position: fixed; inset: 0;
    background: #00000050; z-index: 1000;
    align-items: center; justify-content: center;
  }
  .modal-overlay.open { display: flex; }
  .modal-box {
    background: var(--bg-card);
    border-radius: 16px;
    padding: 24px;
    width: 720px; max-width: 95vw;
    box-shadow: 0 20px 60px #00000030;
    animation: modal-in .18s ease;
  }
  @keyframes modal-in {
    from { opacity: 0; transform: scale(.96) translateY(8px); }
    to   { opacity: 1; transform: scale(1)  translateY(0); }
  }
  .modal-title { font-size: 16px; font-weight: 600; margin-bottom: 16px; }
  .modal-img   { width: 100%; height: 220px; display: block; border-radius: 8px; }
  .modal-stats {
    background: var(--bg-page);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px; margin-top: 14px;
  }
  .modal-stats-title { font-size: 10px; font-weight: 700; color: var(--text-sec); letter-spacing: .06em; margin-bottom: 6px; }
  .modal-stat { font-size: 12px; color: #2B2B2A; font-family: var(--mono); margin-top: 4px; }
  .modal-footer { display: flex; justify-content: flex-end; margin-top: 16px; }
  .btn-close {
    font-family: var(--sans); font-size: 13px; color: var(--blue);
    background: none; border: none; cursor: pointer; padding: 6px 12px;
    border-radius: 6px; transition: background .15s;
  }
  .btn-close:hover { background: var(--ok-bg); }

  /* ── Responsive ── */
  @media (max-width: 700px) {
    .cards-row, .charts-row { flex-direction: column; }
    .modal-box { padding: 16px; }
  }
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="header-left">
    <div class="dot-online"></div>
    <span class="header-title">Analizador de Red — Monofásico</span>
    <span class="badge-online">SCADA Activo</span>
  </div>
  <span class="header-ts" id="ts">--/--/----  |  --:--:--</span>
</div>

<!-- Métricas -->
<div class="section-title">Mediciones en tiempo real</div>
<div class="cards-row">
  <div class="metric-card">
    <div class="card-accent" style="background:var(--blue)"></div>
    <div class="card-label">Tensión</div>
    <div class="card-value"><span id="val-v">--</span><span class="card-unit">V</span></div>
    <div class="card-sub">Nominal: 220 V</div>
  </div>
  <div class="metric-card">
    <div class="card-accent" style="background:var(--amber)"></div>
    <div class="card-label">Corriente</div>
    <div class="card-value"><span id="val-i">--</span><span class="card-unit">A</span></div>
    <div class="card-sub">Estable</div>
  </div>
  <div class="metric-card">
    <div class="card-accent" style="background:var(--green)"></div>
    <div class="card-label">Pot. activa</div>
    <div class="card-value"><span id="val-p">--</span><span class="card-unit">kW</span></div>
    <div class="card-sub">Monitoreo</div>
  </div>
  <div class="metric-card">
    <div class="card-accent" style="background:var(--teal)"></div>
    <div class="card-label">Frecuencia</div>
    <div class="card-value"><span id="val-f">--</span><span class="card-unit">Hz</span></div>
    <div class="card-sub">Nominal: 50 Hz</div>
  </div>
</div>

<!-- Gráficos -->
<div class="section-title">Gráficos SCADA (clic para ampliar)</div>
<div class="charts-row">
  <div class="chart-card" onclick="openModal('VI')">
    <div class="chart-header">
      <span class="chart-title">Tensión y Corriente — últimos 60 s</span>
      <div class="legend">
        <div class="legend-item"><div class="legend-dot" style="background:var(--blue)"></div>Tensión (V)</div>
        <div class="legend-item"><div class="legend-dot" style="background:var(--amber)"></div>Corriente (A)</div>
      </div>
    </div>
    <img class="chart-img" id="chart-vi" src="" alt="Gráfico V/I">
    <div class="chart-hint">➔ Clic para ampliar y ver valores detallados</div>
  </div>
  <div class="chart-card" onclick="openModal('P')">
    <div class="chart-header">
      <span class="chart-title">Consumo — últimos 60 s</span>
      <div class="legend">
        <div class="legend-item"><div class="legend-dot" style="background:var(--purple)"></div>Potencia (W)</div>
      </div>
    </div>
    <img class="chart-img" id="chart-p" src="" alt="Gráfico Potencia">
    <div class="chart-hint">➔ Clic para ampliar y ver valores detallados</div>
  </div>
</div>

<!-- Consumo semanal -->
<div class="section-title">Registro semanal acumulado</div>
<div class="weekly-card">
  <div style="height:2px;background:var(--coral);border-radius:2px;margin-bottom:12px"></div>
  <div class="weekly-top">
    <div>
      <div class="weekly-total-label">Consumo total semana</div>
      <div class="weekly-total-val"><span id="e-total">--</span><span class="weekly-total-unit">kWh</span></div>
    </div>
    <div class="weekly-right">
      <div class="weekly-avg-label">Promedio diario</div>
      <div class="weekly-avg-val" id="e-avg">--</div>
      <div class="weekly-today-val" id="e-today">--</div>
    </div>
  </div>
  <div class="bars-row" id="bars-row"></div>
</div>

<!-- Estado -->
<div class="section-title">Estado y diagnósticos</div>
<div class="alarms-card">
  <div class="alarm-row">
    <div class="alarm-icon" style="background:var(--ok-bg)">✓</div>
    <span class="alarm-text">Tensión Estable (Rango Normal)</span>
    <span class="alarm-detail" id="al-v">-- V</span>
  </div>
  <div class="alarm-row">
    <div class="alarm-icon" style="background:var(--ok-bg)">✓</div>
    <span class="alarm-text">Frecuencia Estable</span>
    <span class="alarm-detail" id="al-f">-- Hz</span>
  </div>
  <div class="alarm-row">
    <div class="alarm-icon" style="background:var(--ok-bg)">ℹ</div>
    <span class="alarm-text">Análisis de Red — Simulación activa</span>
    <span class="alarm-detail" id="al-i">-- A</span>
  </div>
</div>

<div style="height:20px"></div>

<!-- Modal -->
<div class="modal-overlay" id="modal-overlay" onclick="closeModalOutside(event)">
  <div class="modal-box">
    <div class="modal-title" id="modal-title">Detalle del Histórico</div>
    <img class="modal-img" id="modal-img" src="" alt="Gráfico ampliado">
    <div class="modal-stats">
      <div class="modal-stats-title">MÉTRICAS DETALLADAS (VENTANA DE 60 SEGUNDOS):</div>
      <div class="modal-stat" id="modal-stat1">--</div>
      <div class="modal-stat" id="modal-stat2">--</div>
    </div>
    <div class="modal-footer">
      <button class="btn-close" onclick="closeModal()">Cerrar Ventana</button>
    </div>
  </div>
</div>

<script>
// ── Paleta ──────────────────────────────────────────────────────────────────
const C = {
  blue:   '#378ADD', amber:  '#BA7517', green:  '#639922',
  teal:   '#1D9E75', coral:  '#D85A30', purple: '#7F77DD',
  tsec:   '#888780', tter:   '#B4B2A9', gcol:   '#00000020',
};

// ── Estado global ────────────────────────────────────────────────────────────
const HIST_N     = 60;
const INTERVAL_S = 5.0;
const ML = 40, MR_DUAL = 36, MR_SINGLE = 8, MB = 18;

let vHist = Array.from({length: HIST_N}, () => 220 + rand(-1, 1));
let iHist = Array.from({length: HIST_N}, () => 2.0 + rand(-0.2, 0.2));
let pHist = vHist.map((v, k) => v * iHist[k] * 0.85);

let weekData  = [18.4, 22.1, 19.8, 24.3, 20.7, 23.5, 0.1];
const MAX_DAY = 30.0;
let todayAccum = 0.1;

let heladeraOn   = false;
let cicloContador = 0;
let modalType    = null;   // 'VI' | 'P' | null

// ── Utilidades ───────────────────────────────────────────────────────────────
function rand(a, b) { return a + Math.random() * (b - a); }

function svgToSrc(svgStr) {
  return 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgStr)));
}

// ── Generadores SVG ──────────────────────────────────────────────────────────
function buildAxesSingle(W, H, mn, mx, n) {
  const pw = W - ML - MR_SINGLE;
  const ph = H - MB;
  const rng = mx - mn || 1;
  const font = "font-family='DM Sans,sans-serif'";
  let parts = [];

  // Grilla + labels Y izquierdo
  for (let k = 0; k <= 4; k++) {
    const frac = k / 4;
    const val  = mx - frac * rng;
    const y    = frac * ph;
    parts.push(`<line x1="${ML}" y1="${y.toFixed(1)}" x2="${ML+pw}" y2="${y.toFixed(1)}" stroke="${C.gcol}" stroke-width="0.8"/>`);
    parts.push(`<text x="${ML-3}" y="${(y+4).toFixed(1)}" text-anchor="end" ${font} font-size="9" fill="${C.tsec}">${val.toFixed(0)}</text>`);
  }

  // Labels X (tiempo)
  const totalS = (n - 1) * INTERVAL_S;
  for (let k = 0; k < 5; k++) {
    const frac = k / 4;
    const x    = ML + frac * pw;
    const ago  = totalS * (1 - frac);
    const lbl  = ago < 1 ? 'ahora' : `-${ago.toFixed(0)}s`;
    const anchor = k === 0 ? 'start' : (k === 4 ? 'end' : 'middle');
    parts.push(`<text x="${x.toFixed(1)}" y="${H-3}" text-anchor="${anchor}" ${font} font-size="9" fill="${C.tsec}">${lbl}</text>`);
  }

  return { axes: parts.join('\n'), pw, ph };
}

function svgSingle(data, color, unitY='W', W=400, H=130, minY=null, maxY=null, filled=false) {
  if (!data.length) return '';
  const mn = minY !== null ? minY : Math.min(...data);
  const mx = maxY !== null ? maxY : Math.max(...data);
  const rng = mx - mn || 1;
  const n   = data.length;

  const {axes, pw, ph} = buildAxesSingle(W, H, mn, mx, n);

  const px = i => ML + (i / (n-1)) * pw;
  const py = v => (mx - v) / rng * ph;

  const pts = data.map((v, i) => `${px(i).toFixed(1)},${py(v).toFixed(1)}`).join(' ');
  const font = "font-family='DM Sans,sans-serif'";

  let fillEl = '';
  if (filled) {
    fillEl = `<polygon points="${px(0).toFixed(1)},${ph} ${pts} ${px(n-1).toFixed(1)},${ph}" fill="${color}" fill-opacity="0.15"/>`;
  }

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">
    <rect width="${W}" height="${H}" fill="none"/>
    <text x="2" y="10" ${font} font-size="9" fill="${C.tsec}">${unitY}</text>
    ${axes}${fillEl}
    <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>
  </svg>`;
}

function svgDual(d1, d2, c1, c2, unitY1='V', unitY2='A', W=400, H=130, minY=null, maxY=null) {
  if (!d1.length || !d2.length) return '';
  const mn1 = minY !== null ? minY : Math.min(...d1);
  const mx1 = maxY !== null ? maxY : Math.max(...d1);
  const mn2 = Math.min(...d2), mx2 = Math.max(...d2);
  const rng1 = mx1 - mn1 || 1, rng2 = mx2 - mn2 || 1;
  const pw = W - ML - MR_DUAL, ph = H - MB;
  const n  = d1.length;
  const font = "font-family='DM Sans,sans-serif'";

  let parts = [];

  // Grilla + eje Y izquierdo + eje Y derecho
  for (let k = 0; k <= 4; k++) {
    const frac = k / 4;
    const val1 = mx1 - frac * rng1;
    const val2 = mx2 - frac * rng2;
    const y    = frac * ph;
    parts.push(`<line x1="${ML}" y1="${y.toFixed(1)}" x2="${ML+pw}" y2="${y.toFixed(1)}" stroke="${C.gcol}" stroke-width="0.8"/>`);
    parts.push(`<text x="${ML-3}" y="${(y+4).toFixed(1)}" text-anchor="end" ${font} font-size="9" fill="${c1}">${val1.toFixed(0)}</text>`);
    parts.push(`<text x="${ML+pw+3}" y="${(y+4).toFixed(1)}" text-anchor="start" ${font} font-size="9" fill="${c2}">${val2.toFixed(1)}</text>`);
  }

  // Unidades
  parts.push(`<text x="2" y="10" ${font} font-size="9" fill="${c1}">${unitY1}</text>`);
  parts.push(`<text x="${W-2}" y="10" text-anchor="end" ${font} font-size="9" fill="${c2}">${unitY2}</text>`);

  // Labels X
  const totalS = (n - 1) * INTERVAL_S;
  for (let k = 0; k < 5; k++) {
    const frac = k / 4;
    const x    = ML + frac * pw;
    const ago  = totalS * (1 - frac);
    const lbl  = ago < 1 ? 'ahora' : `-${ago.toFixed(0)}s`;
    const anchor = k === 0 ? 'start' : (k === 4 ? 'end' : 'middle');
    parts.push(`<text x="${x.toFixed(1)}" y="${H-3}" text-anchor="${anchor}" ${font} font-size="9" fill="${C.tsec}">${lbl}</text>`);
  }

  const px  = i => ML + (i / (n-1)) * pw;
  const py1 = v => (mx1 - v) / rng1 * ph;
  const py2 = v => (mx2 - v) / rng2 * ph;

  const pts1 = d1.map((v, i) => `${px(i).toFixed(1)},${py1(v).toFixed(1)}`).join(' ');
  const pts2 = d2.map((v, i) => `${px(i).toFixed(1)},${py2(v).toFixed(1)}`).join(' ');

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">
    <rect width="${W}" height="${H}" fill="none"/>
    ${parts.join('\n')}
    <polyline points="${pts1}" fill="none" stroke="${c1}" stroke-width="1.8" stroke-linejoin="round"/>
    <polyline points="${pts2}" fill="none" stroke="${c2}" stroke-width="1.8" stroke-linejoin="round"/>
  </svg>`;
}

// ── Render de gráficos ────────────────────────────────────────────────────────
function renderVI() {
  document.getElementById('chart-vi').src = svgToSrc(
    svgDual(vHist, iHist, C.blue, C.amber, 'V', 'A', 400, 130, 215, 225)
  );
}
function renderP() {
  document.getElementById('chart-p').src = svgToSrc(
    svgSingle(pHist, C.purple, 'W', 400, 130, 0, 3000, true)
  );
}

// ── Inicializar barras semanales ──────────────────────────────────────────────
const daysLabels = ['Lun','Mar','Mié','Jue','Vie','Sáb','Hoy'];
function initBars() {
  const row = document.getElementById('bars-row');
  row.innerHTML = '';
  daysLabels.forEach((lbl, i) => {
    const isToday = i === 6;
    const color   = isToday ? 'var(--coral)' : 'var(--purple)';
    const pct     = weekData[i] / MAX_DAY;
    const h       = Math.max(2, Math.round(pct * 80));
    row.innerHTML += `
      <div class="day-col">
        <div class="bar-wrap">
          <div class="bar-fill" id="bar-${i}"
               style="background:${color};height:${h}px;opacity:${isToday?1:0.65}"></div>
        </div>
        <span class="day-lbl">${lbl}</span>
        <span class="day-val" id="bar-val-${i}" style="color:${isToday?'var(--coral)':'inherit'}">${weekData[i].toFixed(1)}</span>
        <span class="day-unit">kWh</span>
      </div>`;
  });
}
function updateBars() {
  for (let i = 0; i < 7; i++) {
    const pct = weekData[i] / MAX_DAY;
    const h   = Math.max(2, Math.round(pct * 80));
    const bar = document.getElementById(`bar-${i}`);
    const val = document.getElementById(`bar-val-${i}`);
    if (bar) bar.style.height = h + 'px';
    if (val) val.textContent = weekData[i].toFixed(1);
  }
}

// ── Timestamp ────────────────────────────────────────────────────────────────
function updateTS() {
  const now = new Date();
  const d   = now.toLocaleDateString('es-AR', {day:'2-digit', month:'2-digit', year:'numeric'});
  const t   = now.toLocaleTimeString('es-AR', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
  document.getElementById('ts').textContent = `${d}  |  ${t}`;
}

// ── Ciclo SCADA (cada 5 s) ────────────────────────────────────────────────────
function scadaUpdate() {
  cicloContador++;

  const v    = parseFloat((rand(217.5, 223.8)).toFixed(1));
  const iBase = 1.2;
  if (cicloContador % 4 === 0) heladeraOn = !heladeraOn;
  const iHel = heladeraOn ? rand(2.2, 3.2) : 0;
  const ii   = parseFloat((iBase + iHel + rand(-0.1, 0.1)).toFixed(1));
  const fp   = ii > 3 ? 0.95 : parseFloat(rand(0.82, 0.86).toFixed(2));
  const p    = Math.round(v * ii * fp);
  const f    = parseFloat(rand(49.95, 50.05).toFixed(2));

  // Métricas
  document.getElementById('val-v').textContent = v.toFixed(1);
  document.getElementById('val-i').textContent = ii.toFixed(1);
  document.getElementById('val-p').textContent = (p / 1000).toFixed(2);
  document.getElementById('val-f').textContent = f.toFixed(2);

  // Alarmas
  document.getElementById('al-v').textContent = `${v.toFixed(1)} V`;
  document.getElementById('al-f').textContent = `${f.toFixed(2)} Hz`;
  document.getElementById('al-i').textContent = `${ii.toFixed(1)} A / lim 15 A`;

  // Histórico
  vHist.push(v);   vHist.shift();
  iHist.push(ii);  iHist.shift();
  pHist.push(p);   pHist.shift();

  renderVI();
  renderP();

  // Energía semanal
  todayAccum += (p / 1000) / 3600 * INTERVAL_S;
  weekData[6] = parseFloat(todayAccum.toFixed(2));

  const total = weekData.reduce((a, b) => a + b, 0);
  const avg   = total / weekData.length;
  document.getElementById('e-total').textContent = total.toFixed(1);
  document.getElementById('e-avg').textContent   = `${avg.toFixed(1)} kWh`;
  document.getElementById('e-today').textContent  = `Hoy: ${weekData[6].toFixed(2)} kWh`;
  updateBars();

  updateTS();

  // Actualizar modal si está abierto
  if (modalType) updateModalData();
}

// ── Modal ─────────────────────────────────────────────────────────────────────
function openModal(type) {
  modalType = type;
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.add('open');
  updateModalData();
}

function updateModalData() {
  if (modalType === 'VI') {
    document.getElementById('modal-title').textContent = 'Análisis: Tensión (V) y Corriente (A)';
    document.getElementById('modal-img').src = svgToSrc(
      svgDual(vHist, iHist, C.blue, C.amber, 'V', 'A', 660, 220, 0, 500)
    );
    const vNow = vHist[vHist.length-1], iNow = iHist[iHist.length-1];
    document.getElementById('modal-stat1').textContent =
      `Tensión ➔ Actual: ${vNow.toFixed(1)} V  |  Máxima: ${Math.max(...vHist).toFixed(1)} V  |  Mínima: ${Math.min(...vHist).toFixed(1)} V`;
    document.getElementById('modal-stat2').textContent =
      `Corriente ➔ Actual: ${iNow.toFixed(1)} A  |  Máxima: ${Math.max(...iHist).toFixed(1)} A  |  Promedio: ${(iHist.reduce((a,b)=>a+b)/iHist.length).toFixed(2)} A`;
  } else if (modalType === 'P') {
    document.getElementById('modal-title').textContent = 'Análisis: Potencia Activa de Carga (W)';
    document.getElementById('modal-img').src = svgToSrc(
      svgSingle(pHist, C.purple, 'W', 660, 220, 0, 3000, true)
    );
    const pNow = pHist[pHist.length-1];
    document.getElementById('modal-stat1').textContent =
      `Potencia Activa ➔ Actual: ${pNow.toFixed(0)} W  |  Pico Máximo: ${Math.max(...pHist).toFixed(0)} W`;
    document.getElementById('modal-stat2').textContent =
      `Energía Promedio en Ventana: ${(pHist.reduce((a,b)=>a+b)/pHist.length).toFixed(1)} W`;
  }
}

function closeModal() {
  modalType = null;
  document.getElementById('modal-overlay').classList.remove('open');
}
function closeModalOutside(e) {
  if (e.target === document.getElementById('modal-overlay')) closeModal();
}

// ── Arranque ──────────────────────────────────────────────────────────────────
initBars();
renderVI();
renderP();
updateTS();

// Primera lectura inmediata
scadaUpdate();

// Ciclo cada 5 s
setInterval(scadaUpdate, INTERVAL_S * 1000);
setInterval(updateTS, 1000);
</script>
</body>
</html>
