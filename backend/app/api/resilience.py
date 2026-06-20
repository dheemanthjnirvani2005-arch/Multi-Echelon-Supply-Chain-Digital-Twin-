from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.resilience import calculate_resilience_scores

router = APIRouter()

@router.get("/scores")
def get_resilience_scores(db: Session = Depends(get_db)):
    """Returns the six-axis resilience scores for the radar chart."""
    return calculate_resilience_scores(db)
