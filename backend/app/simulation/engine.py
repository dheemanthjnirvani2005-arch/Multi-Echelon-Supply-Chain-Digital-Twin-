# backend/app/simulation/engine.py
"""
Discrete Event Simulation (DES) engine powered by SimPy.

Each supply chain node is modelled as an autonomous agent with:
  - An (s, Q) continuous-review replenishment policy
  - Poisson demand arrivals
  - Stochastic lead times (Normal distribution)

The engine supports Monte Carlo mode: run N trials and aggregate
P10/P50/P90 confidence bands.
"""
import simpy
import numpy as np
from typing import List, Dict, Any, Optional


class SupplyChainNode:
    """Simulates a single node in the supply network."""

    def __init__(
        self,
        env: simpy.Environment,
        node_id: int,
        capacity: float,
        initial_stock: float,
        reorder_point: float,
        order_qty: float,
        lead_time_mu: float,
        lead_time_sigma: float,
    ):
        self.env        = env
        self.node_id    = node_id
        self.stock      = simpy.Container(env, capacity=capacity, init=initial_stock)
        self.reorder_pt = reorder_point
        self.order_qty  = order_qty
        self.lt_mu      = lead_time_mu
        self.lt_sigma   = lead_time_sigma
        self.stockouts  = 0
        self.total_demand = 0
        self.fulfilled    = 0
        self.history: List[tuple] = []  # (time, stock_level)

    def replenishment_policy(self):
        """Continuous review (s, Q) policy — checks stock daily."""
        while True:
            yield self.env.timeout(1)
            if self.stock.level < self.reorder_pt:
                # Stochastic lead time
                lead_time = max(1, np.random.normal(self.lt_mu, self.lt_sigma))
                yield self.env.timeout(lead_time)
                amount = min(self.order_qty, self.stock.capacity - self.stock.level)
                if amount > 0:
                    yield self.stock.put(amount)

    def demand_process(self, demand_rate: float):
        """Poisson demand arrivals throughout each day."""
        while True:
            inter_arrival = np.random.exponential(1 / max(demand_rate, 0.01))
            yield self.env.timeout(inter_arrival)
            demand = max(1, np.random.poisson(demand_rate * inter_arrival))
            self.total_demand += demand

            if self.stock.level >= demand:
                yield self.stock.get(demand)
                self.fulfilled += demand
            else:
                # Partial fulfilment
                filled = int(self.stock.level)
                if filled > 0:
                    yield self.stock.get(filled)
                    self.fulfilled += filled
                self.stockouts += 1

            self.history.append((round(self.env.now, 2), self.stock.level))


def run_simulation(
    nodes_config: List[Dict[str, Any]],
    sim_days: int = 365,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run a full supply chain simulation.

    Args:
        nodes_config: list of dicts, one per node. Required keys:
            id, capacity, initial_stock, reorder_point, order_qty,
            lead_time_mu, lead_time_sigma, daily_demand_rate
        sim_days: number of days to simulate (default 365)
        seed: optional random seed for reproducibility

    Returns:
        dict keyed by node_id with stockouts, avg_stock, service_level, history
    """
    if seed is not None:
        np.random.seed(seed)

    env = simpy.Environment()
    node_objects: Dict[int, SupplyChainNode] = {}

    for cfg in nodes_config:
        n = SupplyChainNode(
            env,
            cfg["id"],
            cfg["capacity"],
            cfg["initial_stock"],
            cfg["reorder_point"],
            cfg["order_qty"],
            cfg["lead_time_mu"],
            cfg["lead_time_sigma"],
        )
        env.process(n.replenishment_policy())
        env.process(n.demand_process(cfg["daily_demand_rate"]))
        node_objects[cfg["id"]] = n

    env.run(until=sim_days)

    results = {}
    for node_id, n in node_objects.items():
        stock_levels = [h[1] for h in n.history] if n.history else [0]
        fill_rate = n.fulfilled / max(n.total_demand, 1)
        results[str(node_id)] = {
            "stockouts":     n.stockouts,
            "total_demand":  n.total_demand,
            "fulfilled":     n.fulfilled,
            "avg_stock":     round(float(np.mean(stock_levels)), 2),
            "min_stock":     round(float(np.min(stock_levels)), 2),
            "max_stock":     round(float(np.max(stock_levels)), 2),
            "service_level": round(float(1 - n.stockouts / max(sim_days, 1)), 4),
            "fill_rate":     round(float(fill_rate), 4),
            "history":       n.history[:500],  # cap for response size
        }

    return results


def run_monte_carlo(
    nodes_config: List[Dict[str, Any]],
    sim_days: int = 365,
    n_trials: int = 100,
) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation — multiple trials with different random seeds.

    Returns aggregated P10/P50/P90 bands for each node's KPIs.
    """
    all_results = []
    for trial in range(n_trials):
        result = run_simulation(nodes_config, sim_days, seed=trial * 42 + 7)
        all_results.append(result)

    # Aggregate per node
    node_ids = list(all_results[0].keys())
    aggregated = {}

    for nid in node_ids:
        service_levels = [r[nid]["service_level"] for r in all_results]
        avg_stocks     = [r[nid]["avg_stock"] for r in all_results]
        stockouts_list = [r[nid]["stockouts"] for r in all_results]

        aggregated[nid] = {
            "service_level": {
                "p10": round(float(np.percentile(service_levels, 10)), 4),
                "p50": round(float(np.percentile(service_levels, 50)), 4),
                "p90": round(float(np.percentile(service_levels, 90)), 4),
                "mean": round(float(np.mean(service_levels)), 4),
            },
            "avg_stock": {
                "p10": round(float(np.percentile(avg_stocks, 10)), 2),
                "p50": round(float(np.percentile(avg_stocks, 50)), 2),
                "p90": round(float(np.percentile(avg_stocks, 90)), 2),
            },
            "stockouts": {
                "p10": int(np.percentile(stockouts_list, 10)),
                "p50": int(np.percentile(stockouts_list, 50)),
                "p90": int(np.percentile(stockouts_list, 90)),
            },
            "n_trials": n_trials,
        }

    return aggregated
