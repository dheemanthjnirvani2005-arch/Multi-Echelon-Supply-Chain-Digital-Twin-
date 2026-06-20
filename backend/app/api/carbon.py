from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.carbon import get_carbon_dashboard, EMISSION_FACTORS
from app.models.supply_chain import Route

router = APIRouter()


@router.get("/dashboard")
def carbon_dashboard(db: Session = Depends(get_db)):
    return get_carbon_dashboard(db)


@router.get("/emission-factors")
def emission_factors():
    return {"factors": EMISSION_FACTORS, "unit": "kg CO2e per tonne-km"}


class RouteCreate(BaseModel):
    from_node_id:         int
    to_node_id:           int
    transport_mode:       str
    distance_km:          float
    avg_shipment_tonnes:  float = 20.0
    monthly_shipments:    int   = 4


@router.post("/routes")
def create_route(req: RouteCreate, db: Session = Depends(get_db)):
    factor = EMISSION_FACTORS.get(req.transport_mode)
    if not factor:
        raise HTTPException(status_code=400, detail=f"Unknown mode. Choose: {list(EMISSION_FACTORS.keys())}")

    route = Route(
        from_node_id        = req.from_node_id,
        to_node_id          = req.to_node_id,
        transport_mode      = req.transport_mode,
        distance_km         = req.distance_km,
        emission_factor     = factor,
        avg_shipment_tonnes = req.avg_shipment_tonnes,
        monthly_shipments   = req.monthly_shipments,
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    return {"route_id": route.id, "message": "Route created"}
