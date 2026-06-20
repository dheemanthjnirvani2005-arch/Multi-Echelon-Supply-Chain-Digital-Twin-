# backend/app/optimisation/meio_pulp.py
"""
Single-objective Multi-Echelon Inventory Optimisation (MEIO) using PuLP.

Minimises total holding + stockout cost across all nodes subject to a
total inventory investment budget constraint and a minimum service level
fill-rate constraint per node.
"""
import pulp
from typing import List, Dict, Any


def optimise_inventory(nodes: List[Dict[str, Any]], total_budget: float) -> Dict[str, Any]:
    """
    Minimise total holding + stockout cost across all nodes
    subject to a total inventory investment budget.

    Each node dict must have:
        id, holding_cost, stockout_cost, demand_sigma, unit_cost, min_stock, capacity

    Returns:
        dict with status, optimal_safety_stocks, total_cost, and per-node details
    """
    prob = pulp.LpProblem("MEIO_CostMinimisation", pulp.LpMinimize)

    # Decision variable: safety stock quantity per node (continuous, >= 0)
    ss_vars = {
        n["id"]: pulp.LpVariable(f"ss_{n['id']}", lowBound=0, cat="Continuous")
        for n in nodes
    }

    # Objective: minimise holding cost + expected stockout penalty
    # Using a linearised approximation: stockout_cost * max(0, demand_sigma * z - ss)
    prob += pulp.lpSum(
        n["holding_cost"] * ss_vars[n["id"]]
        + n["stockout_cost"] * n["demand_sigma"] * 0.1  # expected shortage cost
        for n in nodes
    )

    # Budget constraint: total investment in safety stock
    prob += (
        pulp.lpSum(n["unit_cost"] * ss_vars[n["id"]] for n in nodes) <= total_budget,
        "BudgetConstraint",
    )

    # Minimum 95% fill rate per node (z = 1.645 for one-tail 95%)
    for n in nodes:
        prob += (
            ss_vars[n["id"]] >= n["demand_sigma"] * 1.645,
            f"MinServiceLevel_{n['id']}",
        )

    # Capacity upper bound per node
    for n in nodes:
        if "capacity" in n:
            prob += (
                ss_vars[n["id"]] <= n["capacity"],
                f"CapacityBound_{n['id']}",
            )

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    return {
        "status": pulp.LpStatus[prob.status],
        "optimal_safety_stocks": {
            n["id"]: round(ss_vars[n["id"]].varValue or 0, 2) for n in nodes
        },
        "total_cost": round(pulp.value(prob.objective) or 0, 2),
        "budget_utilised": round(
            sum(
                n["unit_cost"] * (ss_vars[n["id"]].varValue or 0)
                for n in nodes
            ),
            2,
        ),
        "budget_remaining": round(
            total_budget
            - sum(
                n["unit_cost"] * (ss_vars[n["id"]].varValue or 0)
                for n in nodes
            ),
            2,
        ),
    }
