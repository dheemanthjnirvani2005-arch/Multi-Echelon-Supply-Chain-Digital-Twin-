// Sidebar + Navigation Component
const NAV_ITEMS = [
  { id: 'dashboard', icon: '📊', label: 'Dashboard' },
  { id: 'network', icon: '🌐', label: 'Network Map' },
  { id: 'carbon', icon: '🌱', label: 'Carbon Footprint' },
  { id: 'suppliers', icon: '🏭', label: 'Supplier Risk' },
  { id: 'simulation', icon: '⚡', label: 'Simulation' },
  { id: 'livefeed', icon: '🔴', label: 'Live Feed' },
  { id: 'scenarios', icon: '🔀', label: 'Scenarios' },
  { id: 'optimise', icon: '🎯', label: 'Optimisation' },
  { id: 'montecarlo', icon: '🎲', label: 'Monte Carlo' },
  { id: 'playbook', icon: '📋', label: 'AI Playbook' },
  { id: 'alerts', icon: '🚨', label: 'Alerts' },
];

export function renderSidebar(activePage, onNavigate) {
  const analytics = NAV_ITEMS.filter(i => ['dashboard','network','carbon','suppliers','simulation'].includes(i.id));
  const realtime = NAV_ITEMS.filter(i => ['livefeed','montecarlo','alerts'].includes(i.id));
  const planning = NAV_ITEMS.filter(i => ['scenarios','optimise','playbook'].includes(i.id));

  const renderItems = (items) => items.map(i => `
    <button class="nav-item ${activePage===i.id?'active':''}" data-page="${i.id}">
      <span>${i.icon}</span> ${i.label}
    </button>`).join('');

  return `
  <div class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-logo">
        <div class="sidebar-logo-icon">⚡</div>
        <div><h1>SupplyChain</h1><span>Digital Twin v2.0</span></div>
      </div>
    </div>
    <nav class="sidebar-nav">
      <div class="nav-section-label">Analytics</div>
      ${renderItems(analytics)}
      <div class="nav-section-label">Real-Time</div>
      ${renderItems(realtime)}
      <div class="nav-section-label">Planning</div>
      ${renderItems(planning)}
    </nav>
    <div class="sidebar-footer">
      <div style="font-size:11px;color:var(--text-muted)">Last sync: 2 min ago</div>
    </div>
  </div>`;
}

export function bindSidebarEvents(onNavigate) {
  document.querySelectorAll('.nav-item[data-page]').forEach(btn => {
    btn.addEventListener('click', () => onNavigate(btn.dataset.page));
  });
}
