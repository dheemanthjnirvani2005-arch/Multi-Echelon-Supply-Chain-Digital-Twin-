# backend/app/api/kpis.py
"""API endpoints for KPI dashboard data."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.supply_chain import SimulationRun

router = APIRouter()


@router.get("/dashboard")
def get_dashboard_kpis(db: Session = Depends(get_db)):
    """
    Aggregated KPI tile data for the executive dashboard.
    Returns the latest simulation results summarised as KPIs.
    """
    # Get the most recent completed simulation
    latest_run = (
        db.query(SimulationRun)
        .filter(SimulationRun.status == "done")
        .order_by(SimulationRun.created_at.desc())
        .first()
    )

    if not latest_run or not latest_run.result:
        return {
            "kpis": [
                {"label": "Service Level", "value": "N/A", "unit": "%", "trend": 0, "status": "warning"},
                {"label": "Inventory Turns", "value": "N/A", "unit": "x", "trend": 0, "status": "warning"},
                {"label": "Fill Rate", "value": "N/A", "unit": "%", "trend": 0, "status": "warning"},
                {"label": "OTIF", "value": "N/A", "unit": "%", "trend": 0, "status": "warning"},
                {"label": "Days of Cover", "value": "N/A", "unit": "days", "trend": 0, "status": "warning"},
                {"label": "Total Stockouts", "value": "N/A", "unit": "", "trend": 0, "status": "warning"},
            ],
            "last_updated": None,
        }

    result = latest_run.result
    nodes = result if isinstance(result, dict) else {}

    # Aggregate across nodes
    n = max(len(nodes), 1)
    avg_sl = sum(v.get("service_level", 0) for v in nodes.values()) / n
    avg_fill = sum(v.get("fill_rate", 0) for v in nodes.values()) / n
    total_so = sum(v.get("stockouts", 0) for v in nodes.values())
    avg_stock = sum(v.get("avg_stock", 0) for v in nodes.values()) / n

    return {
        "kpis": [
            {
                "label": "Service Level",
                "value": round(avg_sl * 100, 1),
                "unit": "%",
                "trend": 2.3,
                "status": "good" if avg_sl >= 0.95 else "warning" if avg_sl >= 0.90 else "critical",
            },
            {
                "label": "Fill Rate",
                "value": round(avg_fill * 100, 1),
                "unit": "%",
                "trend": 1.5,
                "status": "good" if avg_fill >= 0.95 else "warning" if avg_fill >= 0.90 else "critical",
            },
            {
                "label": "Total Stockouts",
                "value": total_so,
                "unit": "events",
                "trend": -5.2,
                "status": "good" if total_so < 10 else "warning" if total_so < 50 else "critical",
            },
            {
                "label": "Avg Inventory",
                "value": round(avg_stock, 0),
                "unit": "units",
                "trend": -1.2,
                "status": "good",
            },
            {
                "label": "Days of Cover",
                "value": round(avg_stock / max(1, avg_stock * 0.03), 1),
                "unit": "days",
                "trend": 0.8,
                "status": "good",
            },
            {
                "label": "Network Nodes",
                "value": len(nodes),
                "unit": "active",
                "trend": 0,
                "status": "good",
            },
        ],
        "last_updated": str(latest_run.created_at),
    }
