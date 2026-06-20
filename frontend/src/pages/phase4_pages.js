import { getCarbonDashboard, getHhiScores } from '../data.js';

export function renderCarbon() {
  return `
    <div class="page-container">
      <div class="card fade-in">
        <div class="card-header">
          <h2>Scope-3 Carbon Dashboard</h2>
          <button class="btn" id="refresh-carbon-btn">Refresh Data</button>
        </div>
        <div id="carbon-content" style="padding: 1rem;">
          <div class="loading-spinner">Loading emission data...</div>
        </div>
      </div>
    </div>
  `;
}

export function initCarbonEffects() {
  const content = document.getElementById('carbon-content');
  const refreshBtn = document.getElementById('refresh-carbon-btn');

  if (!content) return;

  const loadData = async () => {
    content.innerHTML = '<div class="loading-spinner">Loading emission data...</div>';
    try {
      const data = await getCarbonDashboard();
      if (data.error) {
        content.innerHTML = `<div class="error">${data.error}</div>`;
        return;
      }
      content.innerHTML = buildCarbonHtml(data);
    } catch (err) {
      content.innerHTML = `<div class="error">Failed to load carbon data. Backend might be down.</div>`;
    }
  };

  if (refreshBtn) refreshBtn.addEventListener('click', loadData);
  loadData();
}

function buildCarbonHtml(data) {
  const formatCo2e = (val) => Number(val).toLocaleString(undefined, { maximumFractionDigits: 1 }) + ' t';

  return `
    <div class="grid grid-3" style="margin-bottom: 2rem;">
      <div class="metric-card">
        <div class="metric-label">Monthly CO₂e (Tonnes)</div>
        <div class="metric-value">${formatCo2e(data.total_monthly_co2e_tonnes)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Annual Projection</div>
        <div class="metric-value">${formatCo2e(data.total_annual_co2e_tonnes)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Potential Monthly Saving</div>
        <div class="metric-value" style="color: var(--success-color)">${formatCo2e(data.potential_monthly_saving_tonnes)}</div>
      </div>
    </div>

    <div class="grid grid-2">
      <div class="card">
        <h3>Highest Emission Routes (Top 5)</h3>
        <table style="width: 100%; border-collapse: collapse; margin-top: 1rem;">
          <thead>
            <tr style="border-bottom: 1px solid var(--border-color); text-align: left;">
              <th style="padding: 8px">From</th>
              <th style="padding: 8px">To</th>
              <th style="padding: 8px">Mode</th>
              <th style="padding: 8px">CO₂e/mo</th>
            </tr>
          </thead>
          <tbody>
            ${data.top_5_routes.map(r => `
              <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 8px">${r.from_node}</td>
                <td style="padding: 8px">${r.to_node}</td>
                <td style="padding: 8px">${r.mode.toUpperCase()}</td>
                <td style="padding: 8px"><b>${r.co2e_tonnes}</b>t</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>

      <div class="card">
        <h3>Optimisation Opportunities</h3>
        ${data.optimisation_opportunities.length === 0 ? '<p>No obvious mode-shift opportunities found.</p>' : ''}
        <ul style="list-style: none; padding: 0; margin: 0; margin-top: 1rem;">
          ${data.optimisation_opportunities.map(o => `
            <li style="padding: 10px; background: rgba(16, 185, 129, 0.1); border-left: 4px solid var(--success-color); margin-bottom: 10px; border-radius: 4px;">
              <b>Shift ${o.from_node} → ${o.to_node}</b> from ${o.current_mode} to ${o.recommended_mode}.<br>
              <span style="font-size: 0.9em; color: var(--success-color);">Save ${o.potential_saving_tonnes}t CO₂e/mo (${o.saving_pct}% reduction)</span>
            </li>
          `).join('')}
        </ul>
      </div>
    </div>
  `;
}

export function renderSuppliers() {
  return `
    <div class="page-container">
      <div class="card fade-in">
        <div class="card-header">
          <h2>Supplier Concentration (HHI) Risk</h2>
          <button class="btn" id="refresh-hhi-btn">Refresh Data</button>
        </div>
        <div id="hhi-content" style="padding: 1rem;">
          <div class="loading-spinner">Loading HHI scores...</div>
        </div>
      </div>
    </div>
  `;
}

export function initSuppliersEffects() {
  const content = document.getElementById('hhi-content');
  const refreshBtn = document.getElementById('refresh-hhi-btn');

  if (!content) return;

  const loadData = async () => {
    content.innerHTML = '<div class="loading-spinner">Loading HHI scores...</div>';
    try {
      const data = await getHhiScores();
      content.innerHTML = buildHhiHtml(data);
    } catch (err) {
      content.innerHTML = `<div class="error">Failed to load HHI data.</div>`;
    }
  };

  if (refreshBtn) refreshBtn.addEventListener('click', loadData);
  loadData();
}

function buildHhiHtml(data) {
  return `
    <div class="grid grid-3" style="margin-bottom: 2rem;">
      <div class="metric-card">
        <div class="metric-label">Portfolio HHI Average</div>
        <div class="metric-value">${data.portfolio_hhi}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">High Risk Components</div>
        <div class="metric-value" style="color: ${data.high_risk_count > 0 ? 'var(--danger-color)' : 'var(--success-color)'}">
          ${data.high_risk_count} / ${data.total_components}
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Alerts Fired</div>
        <div class="metric-value">${data.alerts_fired}</div>
      </div>
    </div>

    <div class="grid grid-1">
      ${data.components.map(c => `
        <div class="card" style="margin-bottom: 1rem; border-left: 4px solid ${c.risk_color};">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3 style="margin: 0">${c.component_name}</h3>
            <span class="badge" style="background: ${c.risk_color}; color: white; padding: 4px 8px; border-radius: 4px;">HHI: ${c.hhi_score} (${c.risk_level.toUpperCase()})</span>
          </div>
          <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
            ${c.suppliers.map(s => `
              <div style="background: var(--bg-color); padding: 8px 12px; border-radius: 4px; border: 1px solid var(--border-color); flex: 1; min-width: 200px;">
                <div style="font-weight: 600;">${s.supplier_name}</div>
                <div style="font-size: 0.85em; color: var(--text-muted); margin-top: 4px;">Share: ${s.share_pct}% | Lead time: ${s.lead_time}d</div>
              </div>
            `).join('')}
          </div>
          <div style="margin-top: 1rem; padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 4px;">
            <b>AI Recommendation:</b> ${c.recommendation}
          </div>
        </div>
      `).join('')}
    </div>
  `;
}
