// SupplyChain-Twin — Mock Data & State
// Realistic demo data for the digital twin platform

export const SUPPLY_NODES = [
  { id: 1, name: "Shanghai Factory", type: "factory", lat: 31.23, lng: 121.47, capacity: 5000, current_stock: 3200, country: "China", city: "Shanghai", utilisation: 0.92 },
  { id: 2, name: "Shenzhen Plant", type: "factory", lat: 22.54, lng: 114.06, capacity: 4000, current_stock: 2800, country: "China", city: "Shenzhen", utilisation: 0.85 },
  { id: 3, name: "Rotterdam DC", type: "dc", lat: 51.92, lng: 4.48, capacity: 8000, current_stock: 5600, country: "Netherlands", city: "Rotterdam", utilisation: 0.78 },
  { id: 4, name: "Hamburg Warehouse", type: "dc", lat: 53.55, lng: 9.99, capacity: 6000, current_stock: 4100, country: "Germany", city: "Hamburg", utilisation: 0.68 },
  { id: 5, name: "LA Distribution", type: "dc", lat: 33.94, lng: -118.41, capacity: 7000, current_stock: 6500, country: "USA", city: "Los Angeles", utilisation: 0.93 },
  { id: 6, name: "Mumbai Hub", type: "dc", lat: 19.08, lng: 72.88, capacity: 3500, current_stock: 2100, country: "India", city: "Mumbai", utilisation: 0.72 },
  { id: 7, name: "São Paulo Retail", type: "retail", lat: -23.55, lng: -46.63, capacity: 2000, current_stock: 1400, country: "Brazil", city: "São Paulo", utilisation: 0.65 },
  { id: 8, name: "London Store", type: "retail", lat: 51.51, lng: -0.13, capacity: 1500, current_stock: 1100, country: "UK", city: "London", utilisation: 0.73 },
  { id: 9, name: "Tokyo Outlet", type: "retail", lat: 35.68, lng: 139.69, capacity: 1800, current_stock: 900, country: "Japan", city: "Tokyo", utilisation: 0.55 },
  { id: 10, name: "Dubai Logistics", type: "dc", lat: 25.20, lng: 55.27, capacity: 4500, current_stock: 3800, country: "UAE", city: "Dubai", utilisation: 0.88 },
  { id: 11, name: "Singapore Hub", type: "dc", lat: 1.35, lng: 103.82, capacity: 5500, current_stock: 4200, country: "Singapore", city: "Singapore", utilisation: 0.76 },
  { id: 12, name: "New York Retail", type: "retail", lat: 40.71, lng: -74.01, capacity: 2200, current_stock: 1800, country: "USA", city: "New York", utilisation: 0.82 },
];

export const SUPPLY_EDGES = [
  { from: 1, to: 3, volume: 850, mode: "ocean", days: 28 },
  { from: 1, to: 5, volume: 720, mode: "ocean", days: 18 },
  { from: 1, to: 11, volume: 500, mode: "ocean", days: 8 },
  { from: 2, to: 10, volume: 400, mode: "ocean", days: 14 },
  { from: 2, to: 6, volume: 350, mode: "ocean", days: 10 },
  { from: 2, to: 11, volume: 600, mode: "ocean", days: 5 },
  { from: 3, to: 4, volume: 420, mode: "truck", days: 2 },
  { from: 3, to: 8, volume: 380, mode: "truck", days: 3 },
  { from: 4, to: 8, volume: 200, mode: "truck", days: 4 },
  { from: 5, to: 12, volume: 550, mode: "truck", days: 5 },
  { from: 6, to: 10, volume: 300, mode: "ocean", days: 4 },
  { from: 10, to: 9, volume: 250, mode: "air", days: 2 },
  { from: 11, to: 9, volume: 350, mode: "ocean", days: 6 },
  { from: 5, to: 7, volume: 180, mode: "ocean", days: 12 },
];

export const KPI_DATA = [
  { label: "Service Level", value: 96.8, unit: "%", trend: 2.3, status: "good", sparkline: [92,93,94,93,95,94,96,95,96,97,96,97] },
  { label: "Fill Rate", value: 98.2, unit: "%", trend: 1.5, status: "good", sparkline: [95,96,97,96,97,98,97,98,98,98,99,98] },
  { label: "Inventory Turns", value: 8.4, unit: "x/yr", trend: 4.1, status: "good", sparkline: [7.1,7.3,7.5,7.8,7.9,8.0,8.1,8.0,8.2,8.3,8.5,8.4] },
  { label: "OTIF", value: 94.1, unit: "%", trend: -1.2, status: "warning", sparkline: [95,96,95,94,95,94,93,94,95,94,94,94] },
  { label: "Days of Cover", value: 32, unit: "days", trend: -3.5, status: "good", sparkline: [38,37,36,35,34,35,34,33,33,32,33,32] },
  { label: "Total Stockouts", value: 12, unit: "events", trend: -18, status: "warning", sparkline: [22,20,18,19,16,15,17,14,15,13,14,12] },
];

export const RADAR_SCORES = {
  labels: ["Supplier Risk", "Logistics", "Demand", "Financial", "Regulatory", "Climate"],
  current: [0.72, 0.85, 0.68, 0.91, 0.78, 0.55],
  target:  [0.85, 0.90, 0.80, 0.95, 0.85, 0.75],
};

export const SCENARIOS = [
  { id: 1, name: "Baseline 2026", icon: "📊", desc: "Current network configuration with Q1 demand forecast", status: "done", kpi: { sl: 96.8, cost: 2.4, stockouts: 12 } },
  { id: 2, name: "Port Strike — Rotterdam", icon: "🚢", desc: "14-day port closure at Rotterdam; reroute via Hamburg", status: "done", kpi: { sl: 88.2, cost: 3.1, stockouts: 47 } },
  { id: 3, name: "Demand Surge +40%", icon: "📈", desc: "Holiday season demand spike across all retail nodes", status: "done", kpi: { sl: 91.5, cost: 2.9, stockouts: 28 } },
  { id: 4, name: "Chip Shortage", icon: "🔧", desc: "Semiconductor shortage reduces Shanghai capacity by 60%", status: "running", kpi: { sl: 82.1, cost: 3.8, stockouts: 65 } },
];

export const BOTTLENECK_NODES = [
  { name: "LA Distribution", utilisation: 0.93, status: "red", detail: "Near max capacity — overflow risk" },
  { name: "Shanghai Factory", utilisation: 0.92, status: "red", detail: "High output pressure — maintenance due" },
  { name: "Dubai Logistics", utilisation: 0.88, status: "amber", detail: "Elevated throughput — monitor" },
  { name: "Shenzhen Plant", utilisation: 0.85, status: "amber", detail: "Stable but elevated" },
  { name: "New York Retail", utilisation: 0.82, status: "amber", detail: "Seasonal demand increase" },
];

export const PLAYBOOK_DATA = {
  disruption: { type: "port_closure", location: "Rotterdam", duration_days: 14 },
  immediate_actions: [
    { action: "Redirect inbound vessels to Hamburg and Antwerp", owner: "Logistics Manager", priority: "high", deadline: "Within 6 hours" },
    { action: "Notify all downstream DCs of expected 5-7 day delay", owner: "SC Coordinator", priority: "high", deadline: "Within 4 hours" },
    { action: "Activate safety stock release at Hamburg Warehouse", owner: "Inventory Analyst", priority: "high", deadline: "Within 12 hours" },
  ],
  short_term_mitigations: [
    { action: "Negotiate expedited rail transport from Hamburg to UK", owner: "Procurement Lead", priority: "medium", deadline: "Within 1 week" },
    { action: "Increase reorder quantities at London and NY stores by 25%", owner: "Demand Planner", priority: "medium", deadline: "Within 2 weeks" },
    { action: "Engage spot-market carriers for overflow capacity", owner: "Logistics Manager", priority: "medium", deadline: "Within 10 days" },
  ],
  long_term_fixes: [
    { action: "Establish permanent secondary route via Mediterranean ports", owner: "VP Supply Chain", priority: "high", deadline: "Within 3 months" },
    { action: "Dual-source critical SKUs from both Shanghai and Shenzhen", owner: "Procurement Director", priority: "medium", deadline: "Within 6 months" },
    { action: "Deploy port congestion monitoring via Marine Traffic API", owner: "IT/Data Eng.", priority: "low", deadline: "Within 4 months" },
  ],
};

export function generateSimHistory(days = 90) {
  const data = [];
  let stock = 3000 + Math.random() * 1000;
  for (let d = 0; d < days; d++) {
    const demand = 30 + Math.random() * 40;
    stock -= demand;
    if (stock < 800) stock += 1500 + Math.random() * 500;
    data.push({ day: d, stock: Math.round(stock), demand: Math.round(demand) });
  }
  return data;
}

const API_BASE = 'http://localhost:8000/api/v1';

export async function getCarbonDashboard() {
  try {
    const res = await fetch(`${API_BASE}/carbon/dashboard`);
    if (!res.ok) throw new Error('Failed to fetch carbon data');
    return await res.json();
  } catch (err) {
    console.error(err);
    return { error: err.message };
  }
}

export async function getHhiScores() {
  try {
    const res = await fetch(`${API_BASE}/suppliers/hhi-scores`);
    if (!res.ok) throw new Error('Failed to fetch HHI data');
    return await res.json();
  } catch (err) {
    console.error(err);
    return { error: err.message };
  }
}

export async function getNodeDetail(nodeId) {
  try {
    const res = await fetch(`${API_BASE}/network/nodes/${nodeId}/detail`);
    if (!res.ok) throw new Error('Failed to fetch node detail');
    return await res.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}

export async function getResilienceScores() {
  try {
    const res = await fetch(`${API_BASE}/resilience/scores`);
    if (!res.ok) throw new Error('Failed to fetch resilience scores');
    return await res.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}
