/* ========================================================================
   MT5 Status
   ======================================================================== */

const TIMEFRAMES = ['M1','M5','M15','M30','H1','H4','D1','W1','MN'];

async function refreshStatus() {
  const dot  = document.getElementById('statusDot');
  const text = document.getElementById('statusText');
  const detail = document.getElementById('statusDetail');

  dot.className  = 'status-dot checking';
  text.textContent = 'Checking MT5 connection…';
  detail.textContent = '';

  try {
    const resp = await fetch('/api/status');
    const data = await resp.json();

    if (data.connected) {
      dot.className = 'status-dot connected';
      text.textContent = 'MT5 Connected';
      const balanceStr = fmtUSD(data.balance || 0);
      const parts = [data.broker, `Account ${data.account}`, `Balance ${balanceStr}`].filter(Boolean);
      detail.textContent = parts.join(' · ');
    } else {
      dot.className = 'status-dot disconnected';
      text.textContent = 'MT5 Disconnected';
      detail.textContent = data.error || 'Terminal not reachable';
    }
  } catch {
    dot.className = 'status-dot disconnected';
    text.textContent = 'MT5 Disconnected';
    detail.textContent = 'Cannot reach backend';
  }
}

/* ========================================================================
   Load symbols into the <select>
   ======================================================================== */

async function loadSymbols() {
  const sel = document.getElementById('symbol');
  sel.innerHTML = '<option value="">Loading symbols…</option>';

  try {
    const resp = await fetch('/api/symbols');
    const data = await resp.json();

    if (data.error || !data.symbols || !data.symbols.length) {
      sel.innerHTML = '<option value="">MT5 unavailable – type symbol below</option>';
      showSymbolInput(true);
      return;
    }

    sel.innerHTML = data.symbols
      .map(s => `<option value="${s}"${s === 'EURUSD' ? ' selected' : ''}>${s}</option>`)
      .join('');
    showSymbolInput(false);
  } catch {
    sel.innerHTML = '<option value="">MT5 unavailable – type symbol below</option>';
    showSymbolInput(true);
  }
}

function showSymbolInput(show) {
  document.getElementById('symbolInputWrap').style.display = show ? 'block' : 'none';
}

/* ========================================================================
   File drop zones
   ======================================================================== */

function setupDropZone(zoneId, inputId, nameId) {
  const zone  = document.getElementById(zoneId);
  const input = document.getElementById(inputId);
  const name  = document.getElementById(nameId);

  input.addEventListener('change', () => {
    if (input.files[0]) name.textContent = '✓ ' + input.files[0].name;
  });
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    if (e.dataTransfer.files[0]) {
      const dt = e.dataTransfer;
      input.files = dt.files;
      name.textContent = '✓ ' + dt.files[0].name;
    }
  });
}

/* ========================================================================
   Form submission
   ======================================================================== */

document.getElementById('runBtn').addEventListener('click', runBacktest);

async function runBacktest() {
  const errorBox = document.getElementById('formError');
  errorBox.style.display = 'none';

  const strategyFile = document.getElementById('strategyFile').files[0];
  if (!strategyFile) { showError('Please upload a strategy .py file.'); return; }

  // Symbol: prefer dropdown, fall back to text input
  const symbolSel   = document.getElementById('symbol');
  const symbolInput = document.getElementById('symbolInput');
  const symbol = (symbolSel.value || symbolInput.value).trim().toUpperCase();
  if (!symbol) { showError('Please select or enter a trading symbol.'); return; }

  const timeframe  = document.getElementById('timeframe').value;
  const startDate  = document.getElementById('startDate').value;
  const endDate    = document.getElementById('endDate').value;
  const capital    = parseFloat(document.getElementById('capital').value) || 1000;
  const posSize    = parseFloat(document.getElementById('positionSize').value) || 100;

  if (!startDate || !endDate) { showError('Please select a date range.'); return; }
  if (startDate >= endDate)   { showError('Start date must be before end date.'); return; }

  const fd = new FormData();
  fd.append('strategy',        strategyFile);
  fd.append('symbol',          symbol);
  fd.append('timeframe',       timeframe);
  fd.append('start_date',      startDate);
  fd.append('end_date',        endDate);
  fd.append('initial_capital', capital);
  fd.append('position_size',   posSize);

  setLoading(true);

  try {
    const resp = await fetch('/api/backtest', { method: 'POST', body: fd });
    const data = await resp.json();

    if (!resp.ok || data.error) {
      showError(data.error || 'An unexpected error occurred.');
    } else {
      renderResults(data);
    }
  } catch {
    showError('Could not reach the server. Is the backend running?');
  } finally {
    setLoading(false);
  }
}

/* ========================================================================
   Render results
   ======================================================================== */

function renderResults(d) {
  const isPositive = d.net_pnl >= 0;
  const retClass   = isPositive ? 'positive' : 'negative';

  // Run context badges
  document.getElementById('runContext').innerHTML = [
    d.symbol    ? `<div class="ctx-badge">Symbol <span>${d.symbol}</span></div>` : '',
    d.timeframe ? `<div class="ctx-badge">Timeframe <span>${d.timeframe}</span></div>` : '',
    d.start_date ? `<div class="ctx-badge">From <span>${d.start_date}</span></div>` : '',
    d.end_date   ? `<div class="ctx-badge">To <span>${d.end_date}</span></div>` : '',
  ].join('');

  // Summary cards
  const cards = [
    { label: 'Total Return',  value: fmt(d.total_return, '%'),            cls: retClass },
    { label: 'Net P&L',       value: fmtUSD(d.net_pnl),                  cls: retClass },
    { label: 'Final Value',   value: fmtUSD(d.final_value),               cls: 'neutral' },
    { label: 'Win Rate',      value: fmt(d.win_rate, '%'),                cls: d.win_rate >= 50 ? 'positive' : 'negative' },
    { label: 'Total Trades',  value: d.total_trades,                      cls: 'neutral' },
    { label: 'Sharpe Ratio',  value: d.sharpe_ratio.toFixed(2),           cls: d.sharpe_ratio >= 0.5 ? 'positive' : 'negative' },
    { label: 'Max Drawdown',  value: fmt(d.max_drawdown, '%'),            cls: d.max_drawdown <= 20 ? 'positive' : 'negative' },
    { label: 'Wins / Losses', value: `${d.wins} / ${d.losses}`,          cls: 'neutral' },
  ];

  document.getElementById('metricsGrid').innerHTML = cards.map(c => `
    <div class="metric-card ${c.cls}">
      <div class="m-label">${c.label}</div>
      <div class="m-value">${c.value}</div>
    </div>`).join('');

  // Detail table
  const rows = [
    ['Starting Capital', fmtUSD(d.starting_capital), ''],
    ['Final Value',      fmtUSD(d.final_value),      d.final_value >= d.starting_capital ? 'pos' : 'neg'],
    ['Net P&L',          fmtUSD(d.net_pnl),          d.net_pnl >= 0 ? 'pos' : 'neg'],
    ['Total Return',     fmt(d.total_return, '%'),    d.total_return >= 0 ? 'pos' : 'neg'],
    ['Total Trades',     d.total_trades,              ''],
    ['Won / Lost',       `${d.wins} / ${d.losses}`,  ''],
    ['Win Rate',         fmt(d.win_rate, '%'),        d.win_rate >= 50 ? 'pos' : 'neg'],
    ['Sharpe Ratio',     d.sharpe_ratio.toFixed(2),   d.sharpe_ratio >= 0.5 ? 'pos' : 'neg'],
    ['Max Drawdown',     fmt(d.max_drawdown, '%'),    d.max_drawdown <= 20 ? 'pos' : 'neg'],
  ];

  document.getElementById('detailTable').innerHTML =
    rows.map(([label, val, cls]) =>
      `<tr><td class="tl">${label}</td><td class="tr ${cls}">${val}</td></tr>`
    ).join('');

  // Rating
  const ratingLabels = {
    return:   'Return',
    win_rate: 'Win Rate',
    drawdown: 'Drawdown',
    sharpe:   'Sharpe',
  };

  document.getElementById('ratingGrid').innerHTML =
    Object.entries(d.rating).map(([key, info]) => {
      const pass = info.icon === '✓';
      return `
        <div class="rating-item ${pass ? 'pass' : 'fail'}">
          <span class="ri-icon">${pass ? '✅' : '❌'}</span>
          <div class="ri-info">
            <span class="ri-name">${ratingLabels[key] || key}</span>
            <span class="ri-label">${info.label}</span>
          </div>
        </div>`;
    }).join('');

  document.getElementById('results').style.display = 'block';
  document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
}

/* ========================================================================
   Utilities
   ======================================================================== */

function fmtUSD(val) {
  const sign = val < 0 ? '-' : '';
  return sign + '$' + Math.abs(val).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function fmt(val, suffix) {
  return val.toFixed(2) + suffix;
}

function showError(msg) {
  const box = document.getElementById('formError');
  box.textContent = '⚠️ ' + msg;
  box.style.display = 'block';
}

function setLoading(on) {
  document.getElementById('loader').style.display = on ? 'block' : 'none';
  document.getElementById('runBtn').disabled = on;
  if (on) document.getElementById('results').style.display = 'none';
}

/* ========================================================================
   Initialise
   ======================================================================== */

// Set default date range: last 1 year
(function setDefaultDates() {
  const today = new Date();
  const lastYear = new Date(today);
  lastYear.setFullYear(today.getFullYear() - 1);

  document.getElementById('endDate').value   = today.toISOString().slice(0, 10);
  document.getElementById('startDate').value = lastYear.toISOString().slice(0, 10);
})();

setupDropZone('dropZone', 'strategyFile', 'fileName');

document.getElementById('refreshStatus').addEventListener('click', refreshStatus);

refreshStatus();
loadSymbols();
