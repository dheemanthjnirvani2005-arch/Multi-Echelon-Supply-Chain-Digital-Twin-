from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.supply_chain import NPSResponse

router = APIRouter()

class NPSSubmit(BaseModel):
    score:     int = Field(..., ge=0, le=10)
    comment:   Optional[str] = None
    user_role: Optional[str] = None

@router.post("/submit")
def submit_nps(req: NPSSubmit, db: Session = Depends(get_db)):
    db.add(NPSResponse(**req.dict()))
    db.commit()
    return {"message": "Thank you for your feedback!"}

@router.get("/results")
def nps_results(db: Session = Depends(get_db)):
    responses = db.query(NPSResponse).all()
    if not responses:
        return {"nps_score": None, "response_count": 0}
    promoters  = sum(1 for r in responses if r.score >= 9)
    detractors = sum(1 for r in responses if r.score <= 6)
    n = len(responses)
    nps = round(((promoters - detractors) / n) * 100)
    return {
        "nps_score":      nps,
        "response_count": n,
        "promoters_pct":  round(promoters / n * 100, 1),
        "passives_pct":   round((n - promoters - detractors) / n * 100, 1),
        "detractors_pct": round(detractors / n * 100, 1),
    }
