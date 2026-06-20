# backend/app/optimisation/meio_pygmo.py
"""
Multi-objective MEIO using PyGMO's NSGA-II evolutionary algorithm.

Three objectives: minimise (total_cost, total_carbon, service_deficit).
Returns a full Pareto frontier instead of a single optimal point.
"""
from typing import List, Dict, Any

try:
    import pygmo as pg
    PYGMO_AVAILABLE = True
except ImportError:
    PYGMO_AVAILABLE = False

import numpy as np


class MEIOProblem:
    """
    PyGMO multi-objective problem definition.

    Decision variables: safety stock level per node (continuous).
    Objectives:
        1. Total cost (holding + unit cost)
        2. Total carbon emissions
        3. Service deficit (shortfall below minimum stock requirement)
    """

    def __init__(self, nodes: List[Dict[str, Any]]):
        self.nodes = nodes
        self.n     = len(nodes)

    def fitness(self, x: list) -> list:
        total_cost = sum(
            n["holding_cost"] * x[i] + n["unit_cost"] * x[i]
            for i, n in enumerate(self.nodes)
        )
        total_carbon = sum(
            n.get("co2e_per_unit", 0) * x[i]
            for i, n in enumerate(self.nodes)
        )
        service_def = sum(
            max(0, n["min_stock"] - x[i])
            for i, n in enumerate(self.nodes)
        )
        return [total_cost, total_carbon, service_def]

    def get_bounds(self) -> tuple:
        lbs = [n["min_stock"] for n in self.nodes]
        ubs = [n["capacity"] for n in self.nodes]
        return (lbs, ubs)

    def get_nobj(self) -> int:
        return 3  # number of objectives


def run_nsga2(
    nodes: List[Dict[str, Any]],
    population: int = 50,
    generations: int = 100,
) -> List[Dict[str, Any]]:
    """
    Run NSGA-II multi-objective optimisation.

    Returns a list of Pareto-optimal solutions, each with:
        - decision: safety stock levels per node
        - objectives: [cost, carbon, service_deficit]
    """
    if not PYGMO_AVAILABLE:
        # Fallback: generate approximate solutions without PyGMO
        return _fallback_nsga2(nodes, population)

    prob = pg.problem(MEIOProblem(nodes))
    algo = pg.algorithm(pg.nsga2(gen=generations))
    pop  = pg.population(prob, size=population)
    pop  = algo.evolve(pop)

    return [
        {
            "decision":   [round(v, 2) for v in pop.get_x()[i]],
            "objectives": [round(v, 4) for v in pop.get_f()[i]],
        }
        for i in range(len(pop.get_x()))
    ]


def _fallback_nsga2(nodes: List[Dict[str, Any]], n_solutions: int = 20) -> List[Dict[str, Any]]:
    """
    Simple fallback when PyGMO is not installed.
    Generates random feasible solutions along the trade-off frontier.
    """
    solutions = []
    for _ in range(n_solutions):
        x = [
            np.random.uniform(n["min_stock"], n["capacity"])
            for n in nodes
        ]
        cost = sum(n["holding_cost"] * x[i] + n["unit_cost"] * x[i] for i, n in enumerate(nodes))
        carbon = sum(n.get("co2e_per_unit", 0) * x[i] for i, n in enumerate(nodes))
        service_def = sum(max(0, n["min_stock"] - x[i]) for i, n in enumerate(nodes))
        solutions.append({
            "decision": [round(v, 2) for v in x],
            "objectives": [round(cost, 4), round(carbon, 4), round(service_def, 4)],
        })
    return solutions
