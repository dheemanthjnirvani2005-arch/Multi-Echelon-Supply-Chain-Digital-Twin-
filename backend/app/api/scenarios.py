# backend/app/api/scenarios.py
"""API endpoints for scenario (what-if) management."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.db.session import get_db
from app.models.supply_chain import Scenario, SimulationRun

router = APIRouter()


class ScenarioCreate(BaseModel):
    name: str
    base_scenario_id: Optional[int] = None
    disruption_events: List[Dict[str, Any]] = []
    description: Optional[str] = None
    created_by: str = "system"


@router.post("/")
def create_scenario(req: ScenarioCreate, db: Session = Depends(get_db)):
    """Create or branch a new scenario."""
    scenario = Scenario(**req.dict())
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return {"id": scenario.id, "name": scenario.name}


@router.get("/")
def list_scenarios(db: Session = Depends(get_db)):
    """List all scenarios."""
    scenarios = db.query(Scenario).order_by(Scenario.created_at.desc()).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "base_scenario_id": s.base_scenario_id,
            "disruption_events": s.disruption_events,
            "created_by": s.created_by,
            "created_at": str(s.created_at),
        }
        for s in scenarios
    ]


@router.get("/{scenario_id}")
def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    """Get a single scenario by ID."""
    s = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {
        "id": s.id,
        "name": s.name,
        "base_scenario_id": s.base_scenario_id,
        "disruption_events": s.disruption_events,
        "description": s.description,
        "created_by": s.created_by,
    }


@router.get("/{scenario_id}/compare")
def compare_scenarios(scenario_id: int, compare_with: str = "", db: Session = Depends(get_db)):
    """
    Compare 2–4 scenarios by their simulation KPI results.
    compare_with: comma-separated list of other scenario IDs.
    """
    ids = [scenario_id]
    if compare_with:
        ids += [int(x.strip()) for x in compare_with.split(",")]

    results = {}
    for sid in ids:
        run = (
            db.query(SimulationRun)
            .filter(SimulationRun.scenario_id == sid, SimulationRun.status == "done")
            .order_by(SimulationRun.created_at.desc())
            .first()
        )
        if run and run.result:
            # Summarise KPIs across all nodes
            node_results = run.result
            if isinstance(node_results, dict) and "error" not in node_results:
                avg_sl = sum(
                    v.get("service_level", 0) for v in node_results.values()
                ) / max(len(node_results), 1)
                total_so = sum(v.get("stockouts", 0) for v in node_results.values())
                avg_stock = sum(
                    v.get("avg_stock", 0) for v in node_results.values()
                ) / max(len(node_results), 1)

                results[str(sid)] = {
                    "avg_service_level": round(avg_sl, 4),
                    "total_stockouts": total_so,
                    "avg_stock": round(avg_stock, 2),
                    "node_count": len(node_results),
                }

    return {"comparison": results, "scenario_ids": ids}
