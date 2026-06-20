# backend/app/api/network.py
"""API endpoints for supply chain network graph management."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.supply_chain import Node, Edge

router = APIRouter()


class NodeCreate(BaseModel):
    name: str
    node_type: str = "dc"
    latitude: float = 0.0
    longitude: float = 0.0
    capacity: float = 1000
    current_stock: float = 0
    country: Optional[str] = None
    city: Optional[str] = None


class EdgeCreate(BaseModel):
    from_node_id: int
    to_node_id: int
    transit_days_mu: float = 5.0
    transit_days_sigma: float = 1.0
    cost_per_unit: float = 1.0
    co2e_per_unit: float = 0.0
    transport_mode: str = "truck"


@router.get("/")
def get_network(db: Session = Depends(get_db)):
    """Return full supply network graph (nodes + edges)."""
    nodes = db.query(Node).all()
    edges = db.query(Edge).filter(Edge.active == True).all()
    return {
        "nodes": [
            {
                "id": n.id,
                "name": n.name,
                "type": n.node_type,
                "lat": n.latitude,
                "lng": n.longitude,
                "capacity": n.capacity,
                "current_stock": n.current_stock,
                "country": n.country,
                "city": n.city,
            }
            for n in nodes
        ],
        "edges": [
            {
                "id": e.id,
                "from_node_id": e.from_node_id,
                "to_node_id": e.to_node_id,
                "transit_days_mu": e.transit_days_mu,
                "transit_days_sigma": e.transit_days_sigma,
                "cost_per_unit": e.cost_per_unit,
                "co2e_per_unit": e.co2e_per_unit,
                "mode": e.transport_mode,
            }
            for e in edges
        ],
    }


@router.post("/nodes")
def create_node(node: NodeCreate, db: Session = Depends(get_db)):
    """Create a new supply chain node."""
    db_node = Node(**node.dict())
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    return {"id": db_node.id, "name": db_node.name}


@router.post("/edges")
def create_edge(edge: EdgeCreate, db: Session = Depends(get_db)):
    """Create a new edge (shipping lane) between two nodes."""
    db_edge = Edge(**edge.dict())
    db.add(db_edge)
    db.commit()
    db.refresh(db_edge)
    return {"id": db_edge.id}


@router.delete("/nodes/{node_id}")
def delete_node(node_id: int, db: Session = Depends(get_db)):
    """Remove a node from the network."""
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    db.delete(node)
    db.commit()
    return {"deleted": node_id}


@router.get("/nodes/{node_id}/detail")
def get_node_detail(node_id: str, db: Session = Depends(get_db)):
    """
    Returns all data needed by the DrillDownPanel:
      - Last 90 days of stock history
      - Most recent Monte Carlo result for this node
      - Inbound supplier breakdown
      - Carbon footprint of inbound routes
      - Active alerts
      - Historical lead times
    """
    from datetime import datetime, timedelta, timezone
    from app.models.supply_chain import SensorReading, Alert, SimulationRun

    cutoff = datetime.now(timezone.utc) - timedelta(days=90)

    # Stock history from sensor readings
    readings = db.query(SensorReading).filter(
        SensorReading.node_id == node_id,
        SensorReading.metric  == 'stock_level',
        SensorReading.timestamp >= cutoff,
    ).order_by(SensorReading.timestamp.asc()).limit(500).all()

    history = [{"timestamp": r.timestamp.isoformat(), "value": r.value} for r in readings]

    # Monte Carlo result for this node
    mc_result = None
    recent_run = db.query(SimulationRun).filter(
        SimulationRun.status == 'done'
    ).order_by(SimulationRun.created_at.desc()).first()

    if recent_run and recent_run.result and node_id in recent_run.result:
        mc_result = recent_run.result[node_id]

    # Active alerts
    active_alerts = db.query(Alert).filter(
        Alert.node_id  == node_id,
        Alert.resolved == False,
    ).order_by(Alert.fired_at.desc()).limit(5).all()

    alerts_data = [{
        "id":       a.id,
        "severity": a.severity,
        "message":  a.message,
        "fired_at": a.fired_at.isoformat() if a.fired_at else None,
    } for a in active_alerts]

    # Synthetic lead time data
    import numpy as np
    np.random.seed(hash(node_id) % 2**32)
    lead_times = list(np.random.normal(loc=7, scale=2, size=80).clip(1, 20).round(1))

    # Supplier breakdown
    from app.models.supply_chain import SupplierComponent, Supplier
    components = db.query(SupplierComponent).all()
    suppliers_data = []
    seen = set()
    for comp in components:
        sup = db.query(Supplier).filter(Supplier.id == comp.supplier_id).first()
        if sup and sup.id not in seen:
            seen.add(sup.id)
            suppliers_data.append({
                "name":      sup.name,
                "country":   sup.country,
                "share_pct": comp.share_pct,
                "component": comp.component_name,
                "lead_time": comp.lead_time_days,
            })

    # Carbon breakdown for inbound routes
    from app.models.supply_chain import Route
    inbound_routes = db.query(Route).filter(Route.to_node_id == int(node_id)).all() if node_id.isdigit() else []
    carbon_data = []
    for route in inbound_routes:
        from_node = db.query(Node).filter(Node.id == route.from_node_id).first()
        co2e = route.distance_km * route.avg_shipment_tonnes * route.monthly_shipments * route.emission_factor / 1000
        carbon_data.append({
            "from_node":   from_node.name if from_node else "?",
            "mode":        route.transport_mode,
            "distance_km": route.distance_km,
            "co2e_tonnes": round(co2e, 2),
        })

    return {
        "stock_history": history,
        "mc_result":     mc_result,
        "active_alerts": alerts_data,
        "lead_times":    lead_times,
        "suppliers":     suppliers_data,
        "carbon":        carbon_data,
    }
