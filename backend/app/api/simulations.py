# backend/app/api/simulations.py
"""API endpoints for running and monitoring simulations."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.db.session import get_db
from app.models.supply_chain import SimulationRun
from app.simulation.engine import run_simulation, run_monte_carlo

router = APIRouter()


class SimRequest(BaseModel):
    scenario_id: int = 1
    sim_days: int = 365
    nodes_config: List[Dict[str, Any]]
    monte_carlo: bool = False
    n_trials: int = 100


@router.post("/")
def start_simulation(req: SimRequest, bg: BackgroundTasks, db: Session = Depends(get_db)):
    """Start a new simulation run (async via background task)."""
    run = SimulationRun(
        scenario_id=req.scenario_id,
        status="pending",
        config=req.dict(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    bg.add_task(
        _run_sim,
        run.id,
        req.nodes_config,
        req.sim_days,
        req.monte_carlo,
        req.n_trials,
    )
    return {"run_id": run.id, "status": "pending"}


def _run_sim(
    run_id: int,
    nodes_config: List[Dict[str, Any]],
    sim_days: int,
    monte_carlo: bool,
    n_trials: int,
):
    """Background task that executes the simulation."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        run = db.query(SimulationRun).filter(SimulationRun.id == run_id).first()
        run.status = "running"
        db.commit()

        if monte_carlo:
            result = run_monte_carlo(nodes_config, sim_days, n_trials)
        else:
            result = run_simulation(nodes_config, sim_days)

        run.result = result
        run.status = "done"
        db.commit()
    except Exception as e:
        run.status = "failed"
        run.result = {"error": str(e)}
        db.commit()
    finally:
        db.close()


@router.get("/{run_id}")
def get_simulation(run_id: int, db: Session = Depends(get_db)):
    """Poll simulation status & results."""
    run = db.query(SimulationRun).filter(SimulationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    return {"run_id": run.id, "status": run.status, "result": run.result}


@router.get("/")
def list_simulations(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List recent simulation runs."""
    runs = (
        db.query(SimulationRun)
        .order_by(SimulationRun.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "run_id": r.id,
            "scenario_id": r.scenario_id,
            "status": r.status,
            "created_at": str(r.created_at),
        }
        for r in runs
    ]
