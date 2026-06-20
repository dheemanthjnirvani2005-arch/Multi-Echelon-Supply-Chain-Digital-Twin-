// SupplyChain-Twin — Main Application Entry Point (v2.0)
import { renderSidebar, bindSidebarEvents } from './components/sidebar.js';
import { renderDashboard, renderNetwork, renderSimulation, renderScenarios, renderOptimise, renderPlaybook, initPageEffects } from './pages/pages.js';
import { renderLiveFeed, renderMonteCarlo, renderAlertsPage, initLiveFeedEffects, initMonteCarloEffects, initAlertsEffects } from './pages/phase3_pages.js';
import { renderCarbon, initCarbonEffects, renderSuppliers, initSuppliersEffects } from './pages/phase4_pages.js';
import { connectWebSocket, getConnectionStatus } from './realtime/ws_client.js';
import { getUnreadCount } from './realtime/alert_store.js';

const PAGE_RENDERERS = {
  dashboard: renderDashboard,
  network: renderNetwork,
  carbon: renderCarbon,
  suppliers: renderSuppliers,
  simulation: renderSimulation,
  livefeed: renderLiveFeed,
  scenarios: renderScenarios,
  optimise: renderOptimise,
  montecarlo: renderMonteCarlo,
  playbook: renderPlaybook,
  alerts: renderAlertsPage,
};

const PAGE_TITLES = {
  dashboard: 'Executive Command Centre',
  network: 'Global Network Map',
  carbon: 'Scope-3 Carbon Dashboard',
  suppliers: 'Supplier HHI Intelligence',
  simulation: 'Simulation Engine',
  livefeed: 'Live Sensor Feed',
  scenarios: 'Scenario Sandbox',
  optimise: 'Inventory Optimisation',
  montecarlo: 'Monte Carlo Simulation',
  playbook: 'AI Playbook Generator',
  alerts: 'Alert Management',
};

let currentPage = 'dashboard';

function navigate(page) {
  currentPage = page;
  render();
}

function render() {
  const app = document.getElementById('app');
  const pageRenderer = PAGE_RENDERERS[currentPage] || renderDashboard;
  const wsStatus = getConnectionStatus();
  const wsColor = wsStatus === 'connected' ? '#10b981' : wsStatus === 'connecting' ? '#f59e0b' : '#64748b';
  const alertCount = getUnreadCount();

  app.innerHTML = `
    ${renderSidebar(currentPage, navigate)}
    <div class="main-content">
      <div class="topbar">
        <div class="topbar-title">${PAGE_TITLES[currentPage] || 'Dashboard'}</div>
        <div class="topbar-actions">
          <div class="topbar-badge" style="color:${wsColor}"><span class="dot" style="background:${wsColor}"></span> ${wsStatus === 'connected' ? 'Live' : 'Offline'}</div>
          <button class="btn btn-sm" data-page="alerts" id="topbar-alerts-btn">🔔 ${alertCount > 0 ? alertCount + ' Alerts' : 'Alerts'}</button>
        </div>
      </div>
      ${pageRenderer()}
    </div>
  `;

  bindSidebarEvents(navigate);

  // Topbar alerts button
  const alertsBtn = document.getElementById('topbar-alerts-btn');
  if (alertsBtn) alertsBtn.addEventListener('click', () => navigate('alerts'));

  // Page-specific effects
  initPageEffects(currentPage);
  if (currentPage === 'livefeed') initLiveFeedEffects();
  if (currentPage === 'montecarlo') initMonteCarloEffects();
  if (currentPage === 'alerts') initAlertsEffects();
  if (currentPage === 'carbon') initCarbonEffects();
  if (currentPage === 'suppliers') initSuppliersEffects();
}

// Try to connect WebSocket on load
connectWebSocket();

// Initial render
render();

// Setup NPS Widget
const npsFab = document.getElementById('nps-fab');
const npsModal = document.getElementById('nps-modal');
const npsCancel = document.getElementById('nps-cancel');
const npsSubmit = document.getElementById('nps-submit');
const npsBtns = document.querySelectorAll('.nps-score-btn');
let selectedNps = null;

if (npsFab && npsModal) {
  npsFab.addEventListener('click', () => {
    npsModal.style.display = npsModal.style.display === 'none' ? 'block' : 'none';
  });
  
  npsCancel.addEventListener('click', () => {
    npsModal.style.display = 'none';
  });

  npsBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      npsBtns.forEach(b => {
        b.style.background = 'var(--bg-color)';
        b.style.color = 'var(--text-primary)';
      });
      e.target.style.background = 'var(--primary-color)';
      e.target.style.color = 'white';
      selectedNps = parseInt(e.target.dataset.score);
    });
  });

  npsSubmit.addEventListener('click', async () => {
    if (selectedNps === null) return alert('Please select a score');
    const comment = document.getElementById('nps-comment').value;
    
    try {
      await fetch('http://localhost:8000/api/v1/nps/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ score: selectedNps, comment })
      });
      npsModal.innerHTML = '<div style="text-align: center; padding: 20px;"><h4>Thank you for your feedback!</h4><p>Your input helps us improve SupplyChain-Twin.</p><button id="nps-close-thanks" class="btn btn-sm">Close</button></div>';
      document.getElementById('nps-close-thanks').addEventListener('click', () => {
        npsModal.style.display = 'none';
        npsFab.style.display = 'none';
      });
      setTimeout(() => { npsModal.style.display = 'none'; npsFab.style.display = 'none'; }, 3000);
    } catch (err) {
      console.error(err);
      alert('Failed to submit NPS score.');
    }
  });
}
