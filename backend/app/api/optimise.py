# backend/app/api/optimise.py
"""API endpoint for inventory optimisation."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from app.optimisation.meio_pulp import optimise_inventory
from app.optimisation.meio_pygmo import run_nsga2

router = APIRouter()


class OptimiseRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    total_budget: float = 100000
    method: str = "pulp"  # 'pulp' or 'nsga2'
    population: int = 50
    generations: int = 100


@router.post("/")
def run_optimisation(req: OptimiseRequest):
    """
    Run inventory optimisation.
    
    method='pulp' → single-objective cost minimisation
    method='nsga2' → multi-objective Pareto frontier (cost, carbon, service)
    """
    if req.method == "nsga2":
        result = run_nsga2(req.nodes, req.population, req.generations)
    else:
        result = optimise_inventory(req.nodes, req.total_budget)

    return {"method": req.method, "result": result}
