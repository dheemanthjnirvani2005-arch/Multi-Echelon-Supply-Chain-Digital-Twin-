# backend/app/api/monte_carlo_api.py
"""Monte Carlo simulation API endpoint."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.db.session import SessionLocal
from app.models.supply_chain import SimulationRun
from app.simulation.engine import run_monte_carlo
from app.simulation.monte_carlo import run_monte_carlo_enhanced

router = APIRouter()


class MonteCarloRequest(BaseModel):
    scenario_id: int = 1
    nodes_config: list = []
    sim_days: int = Field(default=90, ge=1, le=730)
    n_trials: int = Field(default=500, ge=10, le=10000)
    async_run: bool = False  # True = Celery background, False = synchronous


# Default nodes for testing when no config provided
DEFAULT_NODES = [
    {"id": "shanghai-factory", "capacity": 5000, "initial_stock": 3200,
     "reorder_point": 1000, "order_qty": 2000, "lead_time_mu": 7,
     "lead_time_sigma": 2, "daily_demand_rate": 35},
    {"id": "rotterdam-dc", "capacity": 8000, "initial_stock": 5600,
     "reorder_point": 2000, "order_qty": 3000, "lead_time_mu": 28,
     "lead_time_sigma": 5, "daily_demand_rate": 25},
    {"id": "la-distribution", "capacity": 7000, "initial_stock": 6500,
     "reorder_point": 1800, "order_qty": 2500, "lead_time_mu": 18,
     "lead_time_sigma": 4, "daily_demand_rate": 40},
]


@router.post("/")
def start_monte_carlo(req: MonteCarloRequest):
    """
    Start a Monte Carlo simulation.

    If async_run=True, returns immediately with a run_id (requires Celery + Redis).
    If async_run=False, blocks until done (good for testing with small n_trials).
    """
    nodes_config = req.nodes_config if req.nodes_config else DEFAULT_NODES

    db = SessionLocal()
    try:
        run = SimulationRun(
            scenario_id=req.scenario_id,
            status="pending",
            config={"type": "monte_carlo", "sim_days": req.sim_days, "n_trials": req.n_trials},
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        if req.async_run:
            try:
                from app.simulation.monte_carlo import run_monte_carlo_task, CELERY_AVAILABLE
                if CELERY_AVAILABLE:
                    run_monte_carlo_task.delay(run.id, nodes_config, req.sim_days, req.n_trials)
                    return {
                        "run_id": run.id,
                        "status": "pending",
                        "message": f"Monte Carlo started ({req.n_trials} trials). Poll /api/v1/simulations/{run.id} for results.",
                    }
                else:
                    raise HTTPException(status_code=503, detail="Celery not available. Set async_run=false.")
            except ImportError:
                raise HTTPException(status_code=503, detail="Celery not available. Set async_run=false.")
        else:
            # Synchronous — use the enhanced parallel version
            result = run_monte_carlo_enhanced(nodes_config, req.sim_days, req.n_trials)
            run.result = result
            run.status = "done"
            db.commit()
            return {"run_id": run.id, "status": "done", "result": result}
    finally:
        db.close()


@router.get("/latest")
def get_latest_monte_carlo():
    """Get the most recent completed Monte Carlo result."""
    db = SessionLocal()
    try:
        run = db.query(SimulationRun).filter(
            SimulationRun.status == "done",
        ).order_by(SimulationRun.id.desc()).first()

        if not run:
            return {"status": "no_results", "message": "No Monte Carlo runs found."}

        return {
            "run_id": run.id,
            "status": run.status,
            "config": run.config,
            "result": run.result,
        }
    finally:
        db.close()
