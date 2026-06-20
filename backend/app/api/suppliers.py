from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.supply_chain import Supplier, SupplierComponent
from app.analytics.hhi import score_all_suppliers

router = APIRouter()


@router.get("/hhi-scores")
def get_hhi_scores(db: Session = Depends(get_db)):
    """Return HHI scores for all components."""
    return score_all_suppliers(db)


@router.get("/")
def list_suppliers(db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    return [
        {
            "id":          s.id,
            "name":        s.name,
            "country":     s.country,
            "tier":        s.tier,
            "hhi_score":   s.hhi_score,
            "max_share":   s.max_share_pct,
            "risk_score":  s.risk_score,
            "latitude":    s.latitude,
            "longitude":   s.longitude,
        }
        for s in suppliers
    ]


class SupplierCreate(BaseModel):
    name:      str
    country:   str
    city:      Optional[str] = None
    latitude:  Optional[float] = None
    longitude: Optional[float] = None
    tier:      int = 1


@router.post("/")
def create_supplier(req: SupplierCreate, db: Session = Depends(get_db)):
    s = Supplier(**req.dict())
    db.add(s); db.commit(); db.refresh(s)
    return {"id": s.id}


class ComponentCreate(BaseModel):
    component_name:   str
    supplier_id:      int
    share_pct:        float
    annual_spend_usd: float = 0
    lead_time_days:   int   = 30
    is_sole_source:   bool  = False


@router.post("/components")
def add_component(req: ComponentCreate, db: Session = Depends(get_db)):
    # Validate shares don't exceed 100% for this component
    existing_shares = db.query(SupplierComponent).filter(
        SupplierComponent.component_name == req.component_name
    ).all()
    total = sum(c.share_pct for c in existing_shares) + req.share_pct
    if total > 100.1:
        raise HTTPException(status_code=400, detail=f"Total share for '{req.component_name}' would be {total:.0f}% (max 100%)")

    comp = SupplierComponent(**req.dict())
    db.add(comp); db.commit(); db.refresh(comp)
    return {"id": comp.id}
