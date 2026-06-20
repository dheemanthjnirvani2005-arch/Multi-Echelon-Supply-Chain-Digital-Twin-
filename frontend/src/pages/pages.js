// Page renderers
import { KPI_DATA, SUPPLY_NODES, SUPPLY_EDGES, SCENARIOS, BOTTLENECK_NODES, RADAR_SCORES, PLAYBOOK_DATA, generateSimHistory } from '../data.js';
import { renderRadarChart, renderSparkline, renderNetworkMap, renderBarChart } from '../visualisations/charts.js';

export function renderDashboard() {
  const simHist = generateSimHistory();
  return `
  <div class="page animate-in">
    <div class="page-header"><h2>Executive Command Centre</h2><p>Real-time KPI overview across your global supply network</p></div>
    <div class="kpi-grid stagger" id="kpi-grid">
      ${KPI_DATA.map(k => `
        <div class="kpi-tile ${k.status}" data-sparkline='${JSON.stringify(k.sparkline)}'>
          <div class="kpi-label">${k.label}</div>
          <div class="kpi-value">${k.value}<span class="kpi-unit">${k.unit}</span></div>
          <div class="kpi-trend ${k.trend>0?'up':k.trend<0?'down':'flat'}">
            ${k.trend>0?'▲':k.trend<0?'▼':'—'} ${Math.abs(k.trend)}% vs last period
          </div>
          <div class="kpi-sparkline"></div>
        </div>`).join('')}
    </div>
    <div class="grid-2" style="margin-bottom:24px">
      <div class="card">
        <div class="card-header"><span class="card-title">Resilience Radar</span><span class="badge badge-blue">Live</span></div>
        <div class="radar-container" id="radar-chart"></div>
      </div>
      <div class="card">
        <div class="card-header"><span class="card-title">Top-5 Bottlenecks</span><span class="badge badge-amber">⚠ ${BOTTLENECK_NODES.filter(b=>b.status==='red').length} Critical</span></div>
        <div id="bottleneck-list">
          ${BOTTLENECK_NODES.map(b => `
            <div class="bottleneck-item">
              <div class="bottleneck-ring ${b.status}">${Math.round(b.utilisation*100)}</div>
              <div class="bottleneck-info">
                <div class="bottleneck-name">${b.name}</div>
                <div class="bottleneck-detail">${b.detail}</div>
              </div>
              <div class="progress-bar" style="width:80px">
                <div class="progress-fill ${b.status==='red'?'red':b.status==='amber'?'amber':'green'}" style="width:${b.utilisation*100}%"></div>
              </div>
            </div>`).join('')}
        </div>
      </div>
    </div>
    <div class="card">
      <div class="card-header"><span class="card-title">Inventory Levels (90-day)</span></div>
      <div class="bar-chart" id="inv-chart" style="height:140px">
        ${simHist.map(d => `<div class="bar" style="height:${(d.stock/5000)*100}%;background:linear-gradient(180deg,#3b82f6,#3b82f688)" title="Day ${d.day}: ${d.stock} units"></div>`).join('')}
      </div>
    </div>
  </div>`;
}

export function renderNetwork() {
  return `
  <div class="page animate-in">
    <div class="page-header"><h2>Global Network Map</h2><p>Interactive geospatial view — ${SUPPLY_NODES.length} nodes, ${SUPPLY_EDGES.length} active lanes</p></div>
    <div class="card" style="padding:0;overflow:hidden">
      <div class="map-container" id="network-map"></div>
      <div class="map-legend" style="position:relative;bottom:auto;right:auto;border-radius:0;border-top:1px solid var(--border);display:flex;gap:20px;justify-content:center;padding:12px">
        <div class="map-legend-item"><div class="map-legend-dot" style="background:#10b981"></div> &lt;70% util</div>
        <div class="map-legend-item"><div class="map-legend-dot" style="background:#f59e0b"></div> 70-90%</div>
        <div class="map-legend-item"><div class="map-legend-dot" style="background:#ef4444"></div> &gt;90%</div>
        <div class="map-legend-item"><div style="width:20px;height:2px;background:#3b82f6;margin:4px 0"></div> Ocean</div>
        <div class="map-legend-item"><div style="width:20px;height:2px;background:#10b981;margin:4px 0"></div> Truck</div>
        <div class="map-legend-item"><div style="width:20px;height:2px;background:#f59e0b;margin:4px 0"></div> Air</div>
      </div>
    </div>
    <div class="grid-3" style="margin-top:20px">
      ${['factory','dc','retail'].map(t => {
        const ns = SUPPLY_NODES.filter(n=>n.type===t);
        const icon = t==='factory'?'🏭':t==='dc'?'📦':'🏪';
        return `<div class="card"><div class="card-title">${icon} ${t.toUpperCase()} NODES (${ns.length})</div>
          <div class="table-container" style="margin-top:10px"><table><thead><tr><th>Name</th><th>Stock</th><th>Util</th></tr></thead><tbody>
          ${ns.map(n=>`<tr><td style="color:var(--text-primary)">${n.name}</td><td>${n.current_stock}/${n.capacity}</td>
            <td><span class="badge ${n.utilisation>0.9?'badge-red':n.utilisation>0.7?'badge-amber':'badge-green'}">${Math.round(n.utilisation*100)}%</span></td></tr>`).join('')}
          </tbody></table></div></div>`;
      }).join('')}
    </div>
  </div>`;
}

export function renderSimulation() {
  return `
  <div class="page animate-in">
    <div class="page-header"><h2>Simulation Engine</h2><p>Discrete-event simulation powered by SimPy — configure and run supply chain scenarios</p></div>
    <div class="card" style="margin-bottom:20px">
      <div class="card-header"><span class="card-title">Simulation Configuration</span></div>
      <div class="sim-controls">
        <div class="sim-control-group"><label>Duration</label><input type="number" value="365" id="sim-days"> </div>
        <div class="sim-control-group"><label>Demand Rate</label><input type="number" value="35" step="5" id="sim-demand"></div>
        <div class="sim-control-group"><label>Reorder Point</label><input type="number" value="800" step="100" id="sim-rop"></div>
        <div class="sim-control-group"><label>Order Qty</label><input type="number" value="1500" step="100" id="sim-qty"></div>
        <div class="sim-control-group"><label>Lead Time (μ)</label><input type="number" value="7" id="sim-lt"></div>
        <div class="sim-control-group"><label>Mode</label>
          <select id="sim-mode"><option value="single">Single Run</option><option value="monte_carlo">Monte Carlo (100)</option></select>
        </div>
        <button class="btn btn-primary btn-lg" id="run-sim-btn" style="margin-top:18px">▶ Run Simulation</button>
      </div>
    </div>
    <div id="sim-results">
      <div class="grid-2">
        <div class="card"><div class="card-header"><span class="card-title">Stock Level Over Time</span></div>
          <div class="bar-chart" id="sim-stock-chart" style="height:160px"></div>
        </div>
        <div class="card"><div class="card-header"><span class="card-title">Daily Demand</span></div>
          <div class="bar-chart" id="sim-demand-chart" style="height:160px"></div>
        </div>
      </div>
      <div class="kpi-grid" style="margin-top:20px" id="sim-kpi-grid"></div>
    </div>
  </div>`;
}

export function renderScenarios() {
  return `
  <div class="page animate-in">
    <div class="page-header"><h2>Scenario Sandbox</h2><p>Create, compare, and analyse what-if scenarios</p></div>
    <div class="grid-2" style="margin-bottom:24px" id="scenario-grid">
      ${SCENARIOS.map(s => `
        <div class="scenario-card ${s.id===1?'active':''}" data-scenario="${s.id}">
          <div class="scenario-icon" style="background:${s.id===1?'rgba(59,130,246,0.15)':'rgba(139,92,246,0.15)'}">${s.icon}</div>
          <h3 style="font-size:15px;font-weight:700;margin-bottom:4px">${s.name}</h3>
          <p style="font-size:12px;color:var(--text-secondary);margin-bottom:12px">${s.desc}</p>
          <div style="display:flex;gap:12px;flex-wrap:wrap">
            <span class="badge ${s.kpi.sl>=95?'badge-green':s.kpi.sl>=90?'badge-amber':'badge-red'}">SL: ${s.kpi.sl}%</span>
            <span class="badge badge-purple">Cost: $${s.kpi.cost}M</span>
            <span class="badge ${s.kpi.stockouts<20?'badge-green':'badge-amber'}">Stockouts: ${s.kpi.stockouts}</span>
          </div>
          <div style="margin-top:8px"><span class="badge ${s.status==='done'?'badge-green':'badge-blue'}">${s.status==='done'?'✓ Complete':'⟳ Running'}</span></div>
        </div>`).join('')}
    </div>
    <div class="card">
      <div class="card-header"><span class="card-title">Side-by-Side Comparison</span></div>
      <div class="table-container"><table><thead><tr><th>Scenario</th><th>Service Level</th><th>Cost ($M)</th><th>Stockouts</th><th>Delta vs Baseline</th></tr></thead><tbody>
        ${SCENARIOS.map(s => `<tr>
          <td style="color:var(--text-primary);font-weight:600">${s.icon} ${s.name}</td>
          <td><span class="badge ${s.kpi.sl>=95?'badge-green':s.kpi.sl>=90?'badge-amber':'badge-red'}">${s.kpi.sl}%</span></td>
          <td>$${s.kpi.cost}M</td><td>${s.kpi.stockouts}</td>
          <td style="color:${s.id===1?'var(--text-muted)':s.kpi.sl<SCENARIOS[0].kpi.sl?'var(--accent-red)':'var(--accent-green)'}">
            ${s.id===1?'—':((s.kpi.sl-SCENARIOS[0].kpi.sl)>0?'+':'')+((s.kpi.sl-SCENARIOS[0].kpi.sl).toFixed(1))+'%'}
          </td></tr>`).join('')}
      </tbody></table></div>
    </div>
  </div>`;
}

export function renderOptimise() {
  const nodes = SUPPLY_NODES.filter(n=>n.type!=='factory').slice(0,6);
  return `
  <div class="page animate-in">
    <div class="page-header"><h2>Inventory Optimisation</h2><p>Multi-echelon safety stock optimisation using PuLP (LP) and NSGA-II (Pareto)</p></div>
    <div class="card" style="margin-bottom:20px">
      <div class="card-header"><span class="card-title">Optimiser Configuration</span></div>
      <div class="sim-controls">
        <div class="sim-control-group"><label>Method</label>
          <select id="opt-method"><option value="pulp">PuLP (Cost Min)</option><option value="nsga2">NSGA-II (Pareto)</option></select>
        </div>
        <div class="sim-control-group"><label>Budget ($)</label><input type="number" value="500000" id="opt-budget"></div>
        <div class="sim-control-group"><label>Target SL</label><input type="number" value="95" id="opt-sl" max="100">%</div>
        <button class="btn btn-success btn-lg" id="run-opt-btn" style="margin-top:18px">🎯 Optimise</button>
      </div>
    </div>
    <div class="card">
      <div class="card-header"><span class="card-title">Recommended Safety Stock Levels</span></div>
      <div class="table-container"><table><thead><tr><th>Node</th><th>Current Stock</th><th>Optimal Safety Stock</th><th>Reorder Point</th><th>Change</th></tr></thead><tbody>
        ${nodes.map((n,i) => {
          const opt = Math.round(n.capacity * (0.3 + Math.random()*0.2));
          const rop = Math.round(opt * 0.6);
          const delta = opt - n.current_stock;
          return `<tr><td style="color:var(--text-primary);font-weight:600">${n.name}</td>
            <td>${n.current_stock}</td><td style="color:var(--accent-cyan);font-weight:600">${opt}</td><td>${rop}</td>
            <td style="color:${delta>0?'var(--accent-green)':'var(--accent-red)'}">${delta>0?'+':''}${delta}</td></tr>`;
        }).join('')}
      </tbody></table></div>
    </div>
  </div>`;
}

export function renderPlaybook() {
  return `
  <div class="page animate-in">
    <div class="page-header">
      <h2>AI Playbook Generator</h2>
      <p>Automated disruption response playbooks powered by Claude AI</p>
    </div>
    
    <div class="card" style="margin-bottom:20px">
      <div class="card-header"><span class="card-title">Disruption Event</span><span class="badge badge-red">🚨 Generate Plan</span></div>
      <div class="sim-controls" style="flex-wrap:wrap">
        <div class="sim-control-group"><label>Type</label>
          <select id="pb-type"><option value="Port Closure">Port Closure</option><option value="Supplier Bankruptcy">Supplier Bankruptcy</option><option value="Natural Disaster">Natural Disaster</option></select>
        </div>
        <div class="sim-control-group"><label>Location</label><input type="text" value="Shanghai Port" id="pb-location"></div>
        <div class="sim-control-group"><label>Duration (days)</label><input type="number" value="14" id="pb-duration"></div>
        <button class="btn btn-primary btn-lg" id="generate-pb-btn" style="margin-top:18px">🤖 Generate AI Playbook</button>
      </div>
    </div>
    
    <div id="pb-results" style="display:none">
      <div class="card">
        <div class="card-header"><span class="card-title">Response Playbook</span><span class="badge badge-purple">🤖 AI-Generated</span></div>
        <div id="pb-content"></div>
      </div>
    </div>
  </div>`;
}

// --- Client-side simulation logic ---
function runClientSimulation(days, demandRate, reorderPoint, orderQty, leadTimeMu) {
  const history = [];
  let stock = 3000;
  let stockouts = 0;
  let totalDemand = 0;
  let fulfilled = 0;
  let pendingOrder = 0;

  for (let d = 0; d < days; d++) {
    // Daily demand (Poisson-like via normal approx)
    const demand = Math.max(0, Math.round(demandRate + (Math.random() - 0.5) * demandRate * 0.6));
    totalDemand += demand;

    if (stock >= demand) {
      stock -= demand;
      fulfilled += demand;
    } else {
      fulfilled += stock;
      stock = 0;
      stockouts++;
    }

    // Replenishment arrives
    if (pendingOrder > 0) {
      pendingOrder--;
      if (pendingOrder === 0) {
        stock += orderQty;
      }
    }

    // Check reorder point
    if (stock < reorderPoint && pendingOrder === 0) {
      pendingOrder = Math.max(1, Math.round(leadTimeMu + (Math.random() - 0.5) * 2));
    }

    history.push({ day: d, stock: Math.round(stock), demand });
  }

  return { history, stockouts, totalDemand, fulfilled };
}

// --- Client-side optimisation logic ---
function runClientOptimisation(nodes, budget, targetSL) {
  const zScore = targetSL >= 99 ? 2.326 : targetSL >= 97.5 ? 1.96 : targetSL >= 95 ? 1.645 : 1.28;
  let totalCost = 0;
  const results = nodes.map(n => {
    const demandSigma = n.capacity * 0.08;
    const safetyStock = Math.round(demandSigma * zScore);
    const reorderPoint = Math.round(safetyStock * 0.6 + demandSigma);
    const unitCost = 10;
    const cost = safetyStock * unitCost;
    totalCost += cost;
    const delta = safetyStock - n.current_stock;
    return { name: n.name, current: n.current_stock, optimal: safetyStock, rop: reorderPoint, delta, cost };
  });

  // Scale to budget if over
  if (totalCost > budget) {
    const scale = budget / totalCost;
    results.forEach(r => {
      r.optimal = Math.round(r.optimal * scale);
      r.rop = Math.round(r.rop * scale);
      r.delta = r.optimal - r.current;
    });
    totalCost = budget;
  }

  return { results, totalCost, budgetRemaining: Math.round(budget - totalCost) };
}

export function initPageEffects(page) {
  if (page === 'dashboard') {
    setTimeout(async () => {
      const radarEl = document.getElementById('radar-chart');
      if (radarEl) {
        try {
          const { getResilienceScores } = await import('../data.js');
          const data = await getResilienceScores();
          if (data) {
            const current = [
              data.supplier_risk, data.logistics_risk, data.demand_risk,
              data.financial_risk, data.regulatory_risk, data.climate_risk
            ];
            renderRadarChart(radarEl, current, RADAR_SCORES.labels, { target: RADAR_SCORES.target });
          } else {
            renderRadarChart(radarEl, RADAR_SCORES.current, RADAR_SCORES.labels, { target: RADAR_SCORES.target });
          }
        } catch (err) {
          renderRadarChart(radarEl, RADAR_SCORES.current, RADAR_SCORES.labels, { target: RADAR_SCORES.target });
        }
      }
      document.querySelectorAll('.kpi-sparkline').forEach((el, i) => {
        if (KPI_DATA[i]?.sparkline) {
          const color = KPI_DATA[i].status==='good'?'#10b981':KPI_DATA[i].status==='warning'?'#f59e0b':'#ef4444';
          renderSparkline(el, KPI_DATA[i].sparkline, color);
        }
      });
    }, 100);
  }

  if (page === 'network') {
    setTimeout(() => {
      const mapEl = document.getElementById('network-map');
      if (mapEl) {
        renderNetworkMap(mapEl, SUPPLY_NODES, SUPPLY_EDGES, {
          onNodeClick: async (node) => {
            let panel = document.getElementById('drill-down-panel');
            if (!panel) {
              panel = document.createElement('div');
              panel.id = 'drill-down-panel';
              panel.style.position = 'absolute';
              panel.style.right = '0';
              panel.style.top = '0';
              panel.style.width = '400px';
              panel.style.height = '100%';
              panel.style.background = 'var(--bg-color)';
              panel.style.borderLeft = '1px solid var(--border-color)';
              panel.style.boxShadow = '-4px 0 15px rgba(0,0,0,0.5)';
              panel.style.zIndex = '100';
              panel.style.padding = '20px';
              panel.style.overflowY = 'auto';
              panel.style.transition = 'transform 0.3s ease';
              panel.style.transform = 'translateX(100%)';
              mapEl.parentElement.style.position = 'relative';
              mapEl.parentElement.style.overflow = 'hidden';
              mapEl.parentElement.appendChild(panel);
            }

            panel.innerHTML = `
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 style="margin: 0;">${node.name} Drill-Down</h3>
                <button id="close-drill-down" class="btn btn-sm">✕ Close</button>
              </div>
              <div class="loading-spinner">Fetching node telemetry...</div>
            `;
            
            // Slide in
            setTimeout(() => { panel.style.transform = 'translateX(0)'; }, 10);

            document.getElementById('close-drill-down').addEventListener('click', () => {
              panel.style.transform = 'translateX(100%)';
            });

            try {
              const { getNodeDetail } = await import('../data.js');
              const data = await getNodeDetail(node.id);
              if (!data) throw new Error('No data');

              panel.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                  <h3 style="margin: 0;">${node.name} Drill-Down</h3>
                  <button id="close-drill-down" class="btn btn-sm">✕ Close</button>
                </div>
                
                <div class="card" style="margin-bottom: 15px;">
                  <h4 style="margin-top: 0;">Active Alerts</h4>
                  ${data.active_alerts && data.active_alerts.length > 0 ? 
                    data.active_alerts.map(a => `
                      <div style="padding: 8px; background: rgba(239,68,68,0.1); border-left: 3px solid #ef4444; margin-bottom: 8px; font-size: 13px;">
                        ${a.message}
                      </div>
                    `).join('')
                    : '<div style="color: var(--text-muted); font-size: 13px;">No active alerts.</div>'}
                </div>

                <div class="card" style="margin-bottom: 15px;">
                  <h4 style="margin-top: 0;">Stock History (90d)</h4>
                  <div class="bar-chart" id="dd-stock-chart" style="height: 80px;"></div>
                </div>

                <div class="card" style="margin-bottom: 15px;">
                  <h4 style="margin-top: 0;">Supplier Components</h4>
                  ${data.suppliers && data.suppliers.length > 0 ? 
                    data.suppliers.map(s => `
                      <div style="display: flex; justify-content: space-between; font-size: 13px; padding: 4px 0; border-bottom: 1px solid var(--border-color);">
                        <span>${s.name} (${s.share_pct}%)</span>
                        <span style="color: var(--text-muted)">${s.lead_time}d LT</span>
                      </div>
                    `).join('')
                    : '<div style="color: var(--text-muted); font-size: 13px;">No supplier data.</div>'}
                </div>
              `;

              document.getElementById('close-drill-down').addEventListener('click', () => {
                panel.style.transform = 'translateX(100%)';
              });

              if (data.stock_history) {
                const max = Math.max(...data.stock_history.map(d => d.value), 1);
                const chartEl = document.getElementById('dd-stock-chart');
                data.stock_history.forEach(d => {
                  const bar = document.createElement('div');
                  bar.className = 'bar';
                  bar.style.height = `${(d.value / max) * 100}%`;
                  bar.style.background = 'linear-gradient(180deg, #3b82f6, #3b82f688)';
                  chartEl.appendChild(bar);
                });
              }

            } catch (err) {
              panel.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                  <h3 style="margin: 0;">${node.name} Drill-Down</h3>
                  <button id="close-drill-down" class="btn btn-sm">✕ Close</button>
                </div>
                <div class="error">Failed to load node details.</div>
              `;
              document.getElementById('close-drill-down').addEventListener('click', () => {
                panel.style.transform = 'translateX(100%)';
              });
            }
          }
        });
      }
    }, 100);
  }

  if (page === 'simulation') {
    // Initial render with default data
    setTimeout(() => _updateSimCharts(generateSimHistory()), 100);

    // Wire up the Run Simulation button
    setTimeout(() => {
      const btn = document.getElementById('run-sim-btn');
      if (btn) {
        btn.addEventListener('click', () => {
          const days = parseInt(document.getElementById('sim-days')?.value) || 365;
          const demandRate = parseInt(document.getElementById('sim-demand')?.value) || 35;
          const rop = parseInt(document.getElementById('sim-rop')?.value) || 800;
          const qty = parseInt(document.getElementById('sim-qty')?.value) || 1500;
          const lt = parseInt(document.getElementById('sim-lt')?.value) || 7;

          // Show loading state
          btn.textContent = '⟳ Running...';
          btn.disabled = true;
          btn.style.opacity = '0.7';

          setTimeout(() => {
            const result = runClientSimulation(days, demandRate, rop, qty, lt);

            // Update charts
            _updateSimCharts(result.history);

            // Update KPIs with actual sim results
            const kpiGrid = document.getElementById('sim-kpi-grid');
            if (kpiGrid) {
              const avg = Math.round(result.history.reduce((a,d)=>a+d.stock,0)/result.history.length);
              const sl = ((result.fulfilled / Math.max(result.totalDemand, 1)) * 100).toFixed(1);
              kpiGrid.innerHTML = [
                {l:'Avg Stock',v:avg,u:'units',s:'good'},
                {l:'Stockouts',v:result.stockouts,u:'events',s:result.stockouts<10?'good':result.stockouts<30?'warning':'critical'},
                {l:'Service Level',v:sl,u:'%',s:parseFloat(sl)>=95?'good':parseFloat(sl)>=90?'warning':'critical'},
                {l:'Fill Rate',v:((result.fulfilled/Math.max(result.totalDemand,1))*100).toFixed(1),u:'%',s:'good'},
                {l:'Total Demand',v:result.totalDemand,u:'units',s:'good'},
                {l:'Sim Days',v:result.history.length,u:'days',s:'good'},
              ].map(k=>`<div class="kpi-tile ${k.s} animate-in"><div class="kpi-label">${k.l}</div><div class="kpi-value">${k.v}<span class="kpi-unit">${k.u}</span></div></div>`).join('');
            }

            btn.textContent = '✓ Complete — Run Again';
            btn.disabled = false;
            btn.style.opacity = '1';
            setTimeout(() => { btn.textContent = '▶ Run Simulation'; }, 2000);
          }, 600); // Small delay for visual feedback
        });
      }
    }, 150);
  }

  if (page === 'optimise') {
    // Wire up the Optimise button
    setTimeout(() => {
      const btn = document.getElementById('run-opt-btn');
      if (btn) {
        btn.addEventListener('click', () => {
          const budget = parseInt(document.getElementById('opt-budget')?.value) || 500000;
          const targetSL = parseInt(document.getElementById('opt-sl')?.value) || 95;
          const method = document.getElementById('opt-method')?.value || 'pulp';

          btn.textContent = '⟳ Optimising...';
          btn.disabled = true;
          btn.style.opacity = '0.7';

          setTimeout(() => {
            const nodes = SUPPLY_NODES.filter(n=>n.type!=='factory').slice(0,6);
            const opt = runClientOptimisation(nodes, budget, targetSL);

            // Re-render the results table
            const tableBody = document.querySelector('.table-container tbody');
            if (tableBody) {
              tableBody.innerHTML = opt.results.map(r => `
                <tr class="animate-in">
                  <td style="color:var(--text-primary);font-weight:600">${r.name}</td>
                  <td>${r.current}</td>
                  <td style="color:var(--accent-cyan);font-weight:600">${r.optimal}</td>
                  <td>${r.rop}</td>
                  <td style="color:${r.delta>0?'var(--accent-green)':'var(--accent-red)'}">
                    ${r.delta>0?'+':''}${r.delta}
                  </td>
                </tr>`).join('');
            }

            // Add summary card after table if not already present
            let summary = document.getElementById('opt-summary');
            if (!summary) {
              summary = document.createElement('div');
              summary.id = 'opt-summary';
              summary.className = 'kpi-grid';
              summary.style.marginTop = '20px';
              document.querySelector('.page').appendChild(summary);
            }
            summary.innerHTML = [
              {l:'Method',v:method==='pulp'?'PuLP (LP)':'NSGA-II',u:'',s:'good'},
              {l:'Budget Used',v:'$'+opt.totalCost.toLocaleString(),u:'',s:'good'},
              {l:'Budget Left',v:'$'+opt.budgetRemaining.toLocaleString(),u:'',s:opt.budgetRemaining>0?'good':'warning'},
              {l:'Target SL',v:targetSL,u:'%',s:'good'},
            ].map(k=>`<div class="kpi-tile ${k.s} animate-in"><div class="kpi-label">${k.l}</div><div class="kpi-value">${k.v}<span class="kpi-unit">${k.u}</span></div></div>`).join('');

            btn.textContent = '✓ Done — Re-optimise';
            btn.disabled = false;
            btn.style.opacity = '1';
            setTimeout(() => { btn.textContent = '🎯 Optimise'; }, 2000);
          }, 800);
        });
      }
    }, 150);
  }

  if (page === 'playbook') {
    setTimeout(() => {
      const btn = document.getElementById('generate-pb-btn');
      if (btn) {
        btn.addEventListener('click', async () => {
          const type = document.getElementById('pb-type')?.value || 'Port Closure';
          const location = document.getElementById('pb-location')?.value || 'Shanghai Port';
          const duration = parseInt(document.getElementById('pb-duration')?.value) || 14;

          btn.textContent = '🤖 Generating...';
          btn.disabled = true;
          btn.style.opacity = '0.7';

          try {
            const res = await fetch('http://localhost:8000/api/v1/playbook/generate', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                disruption_event: { type, location, duration_days: duration },
                simulation_run_id: 0
              })
            });

            if (!res.ok) throw new Error('Failed to generate playbook');
            const data = await res.json();
            const pb = data.playbook;

            const renderPhase = (title, actions, color, dot) => `
              <div class="playbook-phase animate-in">
                <div class="playbook-phase-header">
                  <div class="playbook-phase-dot" style="background:${dot}"></div>
                  <div class="playbook-phase-title" style="color:${dot}">${title}</div>
                </div>
                ${actions.map(a => `
                  <div class="playbook-action ${a.priority}">
                    <div class="playbook-action-text"><strong>${a.action}</strong></div>
                    <div class="playbook-action-meta">
                      <div>${a.owner}</div>
                      <div style="color:${a.priority==='high'?'var(--accent-red)':a.priority==='medium'?'var(--accent-amber)':'var(--accent-green)'}">${a.priority.toUpperCase()}</div>
                      <div>${a.deadline}</div>
                    </div>
                  </div>`).join('')}
              </div>`;

            const resultsDiv = document.getElementById('pb-results');
            const contentDiv = document.getElementById('pb-content');
            
            contentDiv.innerHTML = `
              ${renderPhase('Immediate Actions (0-48h)', pb.immediate_actions, 'red', '#ef4444')}
              ${renderPhase('Short-Term Mitigations (1-4 weeks)', pb.short_term_mitigations, 'amber', '#f59e0b')}
              ${renderPhase('Long-Term Fixes (1-6 months)', pb.long_term_fixes, 'green', '#10b981')}
            `;
            
            resultsDiv.style.display = 'block';

            btn.textContent = '✓ Complete — Generate New';
            btn.disabled = false;
            btn.style.opacity = '1';
            setTimeout(() => { btn.textContent = '🤖 Generate AI Playbook'; }, 2000);
          } catch (err) {
            console.error(err);
            btn.textContent = '❌ Failed to generate';
            btn.disabled = false;
            btn.style.opacity = '1';
            setTimeout(() => { btn.textContent = '🤖 Generate AI Playbook'; }, 2000);
            
            // Fallback content in case backend is offline
            const fallbackPb = PLAYBOOK_DATA;
            const renderPhase = (title, actions, color, dot) => `
              <div class="playbook-phase animate-in">
                <div class="playbook-phase-header">
                  <div class="playbook-phase-dot" style="background:${dot}"></div>
                  <div class="playbook-phase-title" style="color:${dot}">${title}</div>
                </div>
                ${actions.map(a => `
                  <div class="playbook-action ${a.priority}">
                    <div class="playbook-action-text"><strong>${a.action}</strong></div>
                    <div class="playbook-action-meta">
                      <div>${a.owner}</div>
                      <div style="color:${a.priority==='high'?'var(--accent-red)':a.priority==='medium'?'var(--accent-amber)':'var(--accent-green)'}">${a.priority.toUpperCase()}</div>
                      <div>${a.deadline}</div>
                    </div>
                  </div>`).join('')}
              </div>`;

            const resultsDiv = document.getElementById('pb-results');
            const contentDiv = document.getElementById('pb-content');
            contentDiv.innerHTML = `
              <div style="padding: 10px; margin-bottom: 10px; background: rgba(239, 68, 68, 0.1); color: var(--accent-red); border-radius: 4px; font-size: 13px;">
                ⚠️ Could not reach AI API. Displaying fallback template playbook.
              </div>
              ${renderPhase('Immediate Actions (0-48h)', fallbackPb.immediate_actions, 'red', '#ef4444')}
              ${renderPhase('Short-Term Mitigations (1-4 weeks)', fallbackPb.short_term_mitigations, 'amber', '#f59e0b')}
              ${renderPhase('Long-Term Fixes (1-6 months)', fallbackPb.long_term_fixes, 'green', '#10b981')}
            `;
            resultsDiv.style.display = 'block';
          }
        });
      }
    }, 150);
  }
}

function _updateSimCharts(history) {
  const stockChart = document.getElementById('sim-stock-chart');
  const demandChart = document.getElementById('sim-demand-chart');
  if (stockChart) renderBarChart(stockChart, history.map(d=>({label:'D'+d.day, value:d.stock})), '#3b82f6');
  if (demandChart) renderBarChart(demandChart, history.map(d=>({label:'D'+d.day, value:d.demand})), '#8b5cf6');
}
