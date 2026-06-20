# backend/app/api/playbook.py
"""API endpoint for AI disruption playbook generation."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from app.ai.playbook import generate_playbook
from app.db.session import SessionLocal
from app.models.supply_chain import SimulationRun

router = APIRouter()


class PlaybookRequest(BaseModel):
    disruption_event: Dict[str, Any]
    simulation_run_id: int = 0  # 0 = use fallback without sim results


@router.post("/generate")
def create_playbook(req: PlaybookRequest):
    """Generate an AI-powered disruption response playbook."""
    kpi_summary = {}

    if req.simulation_run_id > 0:
        db = SessionLocal()
        run = db.query(SimulationRun).filter(
            SimulationRun.id == req.simulation_run_id
        ).first()
        db.close()

        if not run or run.status != "done":
            raise HTTPException(status_code=400, detail="Simulation run not complete")

        result = run.result or {}
        kpi_summary = {
            "affected_nodes": list(result.keys()),
            "avg_service_level": round(
                sum(v.get("service_level", 1) for v in result.values())
                / max(len(result), 1),
                4,
            ),
            "total_stockouts": sum(v.get("stockouts", 0) for v in result.values()),
        }

    try:
        playbook = generate_playbook(req.disruption_event, kpi_summary)
        return {"playbook": playbook, "disruption": req.disruption_event}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
