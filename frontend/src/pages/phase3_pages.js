// SupplyChain-Twin — Phase 3 Page Renderers
// Live Feed, Monte Carlo, and Alerts pages

import { SUPPLY_NODES, SUPPLY_EDGES, generateSimHistory } from '../data.js';
import { renderNetworkMap, renderBarChart } from '../visualisations/charts.js';
import { connectWebSocket, onMessage, getConnectionStatus, getMessageCount } from '../realtime/ws_client.js';
import { getAlerts, getUnreadCount, addAlert, markRead, clearAlerts, onAlertsChange } from '../realtime/alert_store.js';


// ── Live Feed Page ──────────────────────────────────────────────────────────

export function renderLiveFeed() {
  const status = getConnectionStatus();
  const statusColor = status === 'connected' ? '#10b981' : status === 'connecting' ? '#f59e0b' : '#ef4444';

  return `
  <div class="page animate-in">
    <div class="page-header">
      <h2>🔴 Live Sensor Feed</h2>
      <p>Real-time MQTT sensor data • WebSocket push updates • Auto-refreshing dashboard</p>
    </div>

    <div class="kpi-grid" style="margin-bottom:20px">
      <div class="kpi-tile good">
        <div class="kpi-label">Connection</div>
        <div class="kpi-value" style="color:${statusColor}">${status === 'connected' ? '● Online' : status === 'connecting' ? '◌ Connecting' : '○ Offline'}</div>
      </div>
      <div class="kpi-tile good">
        <div class="kpi-label">Messages Received</div>
        <div class="kpi-value" id="ws-msg-count">${getMessageCount()}<span class="kpi-unit">msgs</span></div>
      </div>
      <div class="kpi-tile good">
        <div class="kpi-label">Active Alerts</div>
        <div class="kpi-value" id="ws-alert-count" style="color:${getUnreadCount() > 0 ? '#ef4444' : '#10b981'}">${getUnreadCount()}<span class="kpi-unit">unread</span></div>
      </div>
      <div class="kpi-tile good">
        <div class="kpi-label">Nodes Monitored</div>
        <div class="kpi-value">${SUPPLY_NODES.length}<span class="kpi-unit">nodes</span></div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card" style="padding:0;overflow:hidden">
        <div class="card-header" style="padding:16px"><span class="card-title">Network — Live Status</span><span class="badge badge-green">● Live</span></div>
        <div class="map-container" id="live-network-map"></div>
      </div>
      <div class="card">
        <div class="card-header"><span class="card-title">Sensor Activity Log</span></div>
        <div id="sensor-log" style="max-height:380px;overflow-y:auto;font-family:monospace;font-size:12px;color:var(--text-secondary)">
          <div style="color:var(--text-muted);text-align:center;padding:20px">
            ${status === 'connected' ? 'Listening for sensor updates...' : 'Connect to WebSocket to see live data. Start the backend server first.'}
          </div>
        </div>
      </div>
    </div>

    <div class="card" style="margin-top:20px">
      <div class="card-header"><span class="card-title">Recent Alerts</span><span class="badge badge-red">${getUnreadCount()} active</span></div>
      <div id="live-alerts-panel">
        ${_renderAlertsList(getAlerts().slice(0, 8))}
      </div>
    </div>
  </div>`;
}


// ── Monte Carlo Page ────────────────────────────────────────────────────────

export function renderMonteCarlo() {
  return `
  <div class="page animate-in">
    <div class="page-header">
      <h2>🎲 Monte Carlo Simulation</h2>
      <p>Run 1,000+ trials to get P10/P50/P90 probability bands instead of single-point forecasts</p>
    </div>

    <div class="card" style="margin-bottom:20px">
      <div class="card-header"><span class="card-title">Monte Carlo Configuration</span></div>
      <div class="sim-controls">
        <div class="sim-control-group"><label>Sim Days</label><input type="number" value="90" id="mc-days"></div>
        <div class="sim-control-group"><label>Trials</label><input type="number" value="100" step="50" id="mc-trials" min="10" max="5000"></div>
        <div class="sim-control-group"><label>Demand Rate</label><input type="number" value="35" step="5" id="mc-demand"></div>
        <div class="sim-control-group"><label>Reorder Pt</label><input type="number" value="800" step="100" id="mc-rop"></div>
        <div class="sim-control-group"><label>Order Qty</label><input type="number" value="1500" step="100" id="mc-qty"></div>
        <button class="btn btn-primary btn-lg" id="run-mc-btn" style="margin-top:18px">🎲 Run Monte Carlo</button>
      </div>
    </div>

    <div id="mc-results" style="display:none">
      <div class="kpi-grid" id="mc-summary-kpis" style="margin-bottom:20px"></div>

      <div class="grid-2">
        <div class="card">
          <div class="card-header"><span class="card-title">Stock Level — P10 / P50 / P90</span></div>
          <div class="table-container" id="mc-stock-table"></div>
        </div>
        <div class="card">
          <div class="card-header"><span class="card-title">Service Level Confidence</span></div>
          <div class="table-container" id="mc-service-table"></div>
        </div>
      </div>

      <div class="card" style="margin-top:20px">
        <div class="card-header"><span class="card-title">Stockout Risk by Node</span></div>
        <div id="mc-risk-bars" style="display:flex;gap:12px;flex-wrap:wrap"></div>
      </div>
    </div>
  </div>`;
}


// ── Alerts Management Page ──────────────────────────────────────────────────

export function renderAlertsPage() {
  const allAlerts = getAlerts();

  return `
  <div class="page animate-in">
    <div class="page-header">
      <h2>🚨 Alert Management</h2>
      <p>Configure alert rules, view fired alerts, and manage notifications</p>
    </div>

    <div class="kpi-grid" style="margin-bottom:20px">
      <div class="kpi-tile ${allAlerts.filter(a=>a.severity==='critical').length > 0 ? 'critical' : 'good'}">
        <div class="kpi-label">Critical</div>
        <div class="kpi-value" style="color:#ef4444">${allAlerts.filter(a=>a.severity==='critical').length}</div>
      </div>
      <div class="kpi-tile warning">
        <div class="kpi-label">Warnings</div>
        <div class="kpi-value" style="color:#f59e0b">${allAlerts.filter(a=>a.severity==='warning').length}</div>
      </div>
      <div class="kpi-tile good">
        <div class="kpi-label">Info</div>
        <div class="kpi-value" style="color:#3b82f6">${allAlerts.filter(a=>a.severity==='info').length}</div>
      </div>
      <div class="kpi-tile good">
        <div class="kpi-label">Unread</div>
        <div class="kpi-value">${getUnreadCount()}</div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-header"><span class="card-title">Active Alert Rules</span>
          <button class="btn btn-sm" id="add-rule-btn">+ Add Rule</button>
        </div>
        <div class="table-container">
          <table><thead><tr><th>Rule</th><th>Metric</th><th>Condition</th><th>Threshold</th><th>Severity</th></tr></thead>
          <tbody id="rules-table-body">
            <tr><td>Critical Low Stock</td><td>utilisation_pct</td><td>less_than</td><td>20%</td><td><span class="badge badge-red">critical</span></td></tr>
            <tr><td>Warning Low Stock</td><td>utilisation_pct</td><td>less_than</td><td>35%</td><td><span class="badge badge-amber">warning</span></td></tr>
            <tr><td>Overstock Warning</td><td>utilisation_pct</td><td>greater_than</td><td>95%</td><td><span class="badge badge-amber">warning</span></td></tr>
            <tr><td>Zero Stock — Stockout</td><td>stock_level</td><td>less_than</td><td>1</td><td><span class="badge badge-red">critical</span></td></tr>
          </tbody></table>
        </div>
      </div>

      <div class="card">
        <div class="card-header"><span class="card-title">Alert History</span>
          <button class="btn btn-sm" id="clear-alerts-btn">Clear All</button>
        </div>
        <div id="alerts-history-panel" style="max-height:400px;overflow-y:auto">
          ${_renderAlertsList(allAlerts)}
        </div>
      </div>
    </div>
  </div>`;
}


// ── Shared Helpers ──────────────────────────────────────────────────────────

function _renderAlertsList(alerts) {
  if (!alerts.length) {
    return `<div style="text-align:center;padding:30px;color:var(--text-muted)">
      <div style="font-size:32px;margin-bottom:8px">✅</div>
      <div>No alerts — all systems healthy</div>
    </div>`;
  }
  return alerts.map(a => {
    const sevColor = a.severity === 'critical' ? '#ef4444' : a.severity === 'warning' ? '#f59e0b' : '#3b82f6';
    return `
      <div class="bottleneck-item" style="border-left:3px solid ${sevColor};padding-left:12px;margin-bottom:8px;opacity:${a.read ? '0.6' : '1'}">
        <div class="bottleneck-ring" style="background:${sevColor}15;color:${sevColor};font-size:11px">${(a.severity||'info').toUpperCase().slice(0,4)}</div>
        <div class="bottleneck-info">
          <div class="bottleneck-name" style="font-size:12px">${a.message || `${a.metric} = ${a.value}`}</div>
          <div class="bottleneck-detail">${a.node_id || 'system'} • ${a.receivedAt ? new Date(a.receivedAt).toLocaleTimeString() : ''}</div>
        </div>
      </div>`;
  }).join('');
}


// ── Page Effects ────────────────────────────────────────────────────────────

export function initLiveFeedEffects() {
  // Render network map
  setTimeout(() => {
    const mapEl = document.getElementById('live-network-map');
    if (mapEl) renderNetworkMap(mapEl, SUPPLY_NODES, SUPPLY_EDGES);
  }, 100);

  // Connect WebSocket and log messages
  connectWebSocket();
  const unsub = onMessage(msg => {
    const logEl = document.getElementById('sensor-log');
    const countEl = document.getElementById('ws-msg-count');
    const alertCountEl = document.getElementById('ws-alert-count');

    if (countEl) countEl.textContent = getMessageCount();

    if (msg.type === 'sensor_update' && logEl) {
      const line = document.createElement('div');
      line.style.padding = '4px 8px';
      line.style.borderBottom = '1px solid var(--border)';
      const ts = new Date().toLocaleTimeString();
      line.innerHTML = `<span style="color:var(--text-muted)">${ts}</span> <span style="color:var(--accent-cyan)">${msg.node_id}</span> ${msg.metric} = <strong style="color:var(--text-primary)">${typeof msg.value === 'number' ? msg.value.toFixed(1) : msg.value}</strong> ${msg.unit || ''}`;
      logEl.prepend(line);
      // Keep max 50 entries
      while (logEl.children.length > 50) logEl.removeChild(logEl.lastChild);
    }

    if (msg.type === 'alert') {
      addAlert(msg);
      if (alertCountEl) {
        alertCountEl.textContent = getUnreadCount();
        alertCountEl.style.color = '#ef4444';
      }
      const panel = document.getElementById('live-alerts-panel');
      if (panel) panel.innerHTML = _renderAlertsList(getAlerts().slice(0, 8));
    }
  });
}

export function initMonteCarloEffects() {
  setTimeout(() => {
    const btn = document.getElementById('run-mc-btn');
    if (!btn) return;

    btn.addEventListener('click', () => {
      const days = parseInt(document.getElementById('mc-days')?.value) || 90;
      const trials = parseInt(document.getElementById('mc-trials')?.value) || 100;
      const demand = parseInt(document.getElementById('mc-demand')?.value) || 35;
      const rop = parseInt(document.getElementById('mc-rop')?.value) || 800;
      const qty = parseInt(document.getElementById('mc-qty')?.value) || 1500;

      btn.textContent = `⟳ Running ${trials} trials...`;
      btn.disabled = true;
      btn.style.opacity = '0.7';

      setTimeout(() => {
        const result = _runClientMonteCarlo(days, trials, demand, rop, qty);
        _displayMonteCarloResults(result);

        btn.textContent = '✓ Complete — Run Again';
        btn.disabled = false;
        btn.style.opacity = '1';
        setTimeout(() => { btn.textContent = '🎲 Run Monte Carlo'; }, 2000);
      }, 300);
    });
  }, 150);
}

export function initAlertsEffects() {
  setTimeout(() => {
    const clearBtn = document.getElementById('clear-alerts-btn');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        clearAlerts();
        const panel = document.getElementById('alerts-history-panel');
        if (panel) panel.innerHTML = _renderAlertsList([]);
      });
    }
  }, 100);
}


// ── Client-side Monte Carlo ─────────────────────────────────────────────────

function _runClientMonteCarlo(days, trials, demandRate, rop, qty) {
  const nodes = [
    { id: 'Shanghai Factory', capacity: 5000, stock: 3200 },
    { id: 'Rotterdam DC', capacity: 8000, stock: 5600 },
    { id: 'LA Distribution', capacity: 7000, stock: 6500 },
    { id: 'Mumbai Hub', capacity: 3500, stock: 2100 },
    { id: 'Singapore Hub', capacity: 5500, stock: 4200 },
  ];

  const results = {};

  for (const node of nodes) {
    const stockTrials = [];
    const slTrials = [];
    const soTrials = [];

    for (let t = 0; t < trials; t++) {
      let stock = node.stock;
      let stockouts = 0;
      let fulfilled = 0;
      let totalDemand = 0;
      let pending = 0;

      for (let d = 0; d < days; d++) {
        const demand = Math.max(0, Math.round(demandRate + (Math.random() - 0.5) * demandRate * 0.6));
        totalDemand += demand;

        if (stock >= demand) { stock -= demand; fulfilled += demand; }
        else { fulfilled += stock; stock = 0; stockouts++; }

        if (pending > 0) { pending--; if (pending === 0) stock = Math.min(node.capacity, stock + qty); }
        if (stock < rop && pending === 0) pending = Math.max(1, Math.round(7 + (Math.random() - 0.5) * 4));
      }

      stockTrials.push(stock);
      slTrials.push(totalDemand > 0 ? fulfilled / totalDemand : 1);
      soTrials.push(stockouts);
    }

    stockTrials.sort((a, b) => a - b);
    slTrials.sort((a, b) => a - b);

    const p = (arr, pct) => arr[Math.floor(arr.length * pct / 100)] || 0;

    results[node.id] = {
      stock_level: { p10: Math.round(p(stockTrials, 10)), p50: Math.round(p(stockTrials, 50)), p90: Math.round(p(stockTrials, 90)) },
      service_level: { p10: +(p(slTrials, 10) * 100).toFixed(1), p50: +(p(slTrials, 50) * 100).toFixed(1), p90: +(p(slTrials, 90) * 100).toFixed(1) },
      stockout_risk_pct: +((soTrials.filter(s => s > 0).length / trials) * 100).toFixed(1),
    };
  }

  results._summary = { n_trials: trials, sim_days: days, worst_node: Object.keys(results).reduce((worst, k) => {
    if (k.startsWith('_')) return worst;
    return (!worst || results[k].service_level.p10 < results[worst].service_level.p10) ? k : worst;
  }, null) };

  return results;
}


function _displayMonteCarloResults(result) {
  const resultsDiv = document.getElementById('mc-results');
  if (resultsDiv) resultsDiv.style.display = 'block';

  const summary = result._summary || {};
  const nodes = Object.keys(result).filter(k => !k.startsWith('_'));

  // Summary KPIs
  const kpiGrid = document.getElementById('mc-summary-kpis');
  if (kpiGrid) {
    kpiGrid.innerHTML = [
      { l: 'Trials Run', v: summary.n_trials, u: '', s: 'good' },
      { l: 'Sim Days', v: summary.sim_days, u: 'days', s: 'good' },
      { l: 'Worst Node', v: summary.worst_node?.split(' ')[0] || '—', u: '', s: 'warning' },
      { l: 'Nodes Analysed', v: nodes.length, u: '', s: 'good' },
    ].map(k => `<div class="kpi-tile ${k.s} animate-in"><div class="kpi-label">${k.l}</div><div class="kpi-value">${k.v}<span class="kpi-unit">${k.u}</span></div></div>`).join('');
  }

  // Stock level table
  const stockTable = document.getElementById('mc-stock-table');
  if (stockTable) {
    stockTable.innerHTML = `<table><thead><tr><th>Node</th><th style="color:#ef4444">P10 (worst)</th><th style="color:#3b82f6">P50 (median)</th><th style="color:#10b981">P90 (best)</th></tr></thead><tbody>
      ${nodes.map(n => {
        const sl = result[n].stock_level;
        return `<tr><td style="color:var(--text-primary);font-weight:600">${n}</td>
          <td style="color:#ef4444">${sl.p10}</td>
          <td style="color:#3b82f6;font-weight:700">${sl.p50}</td>
          <td style="color:#10b981">${sl.p90}</td></tr>`;
      }).join('')}
    </tbody></table>`;
  }

  // Service level table
  const serviceTable = document.getElementById('mc-service-table');
  if (serviceTable) {
    serviceTable.innerHTML = `<table><thead><tr><th>Node</th><th>P10</th><th>P50</th><th>P90</th></tr></thead><tbody>
      ${nodes.map(n => {
        const sl = result[n].service_level;
        return `<tr><td style="color:var(--text-primary);font-weight:600">${n}</td>
          <td><span class="badge ${sl.p10 >= 95 ? 'badge-green' : sl.p10 >= 90 ? 'badge-amber' : 'badge-red'}">${sl.p10}%</span></td>
          <td><span class="badge badge-blue">${sl.p50}%</span></td>
          <td><span class="badge badge-green">${sl.p90}%</span></td></tr>`;
      }).join('')}
    </tbody></table>`;
  }

  // Risk bars
  const riskBars = document.getElementById('mc-risk-bars');
  if (riskBars) {
    riskBars.innerHTML = nodes.map(n => {
      const risk = result[n].stockout_risk_pct;
      const color = risk > 50 ? '#ef4444' : risk > 20 ? '#f59e0b' : '#10b981';
      return `<div class="kpi-tile" style="flex:1;min-width:140px;border-left:3px solid ${color}">
        <div class="kpi-label">${n}</div>
        <div class="kpi-value" style="color:${color}">${risk}<span class="kpi-unit">%</span></div>
        <div style="font-size:11px;color:var(--text-muted)">stockout risk</div>
        <div class="progress-bar" style="margin-top:8px"><div class="progress-fill" style="width:${risk}%;background:${color}"></div></div>
      </div>`;
    }).join('');
  }
}
