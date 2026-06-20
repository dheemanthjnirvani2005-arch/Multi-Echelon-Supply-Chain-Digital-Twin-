# backend/app/api/alerts_api.py
"""Alerts API — list, create rules, resolve alerts."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.db.session import SessionLocal
from app.models.supply_chain import Alert, AlertRule
from app.alerts.engine import resolve_alert

router = APIRouter()


class AlertRuleCreate(BaseModel):
    name: str
    node_id: Optional[str] = None
    metric: str
    condition: str  # less_than / greater_than / equals
    threshold: float
    severity: str = "warning"
    notify_email: bool = True
    notify_ws: bool = True


@router.get("/")
def list_alerts(resolved: bool = False, severity: Optional[str] = None, limit: int = 50):
    """List recent alerts. By default shows only unresolved ones."""
    db = SessionLocal()
    try:
        query = db.query(Alert).filter(Alert.resolved == resolved)
        if severity:
            query = query.filter(Alert.severity == severity)
        alerts = query.order_by(Alert.fired_at.desc()).limit(limit).all()
        return [
            {
                "id": a.id, "node_id": a.node_id, "metric": a.metric,
                "value": a.value, "threshold": a.threshold, "severity": a.severity,
                "message": a.message, "resolved": a.resolved, "fired_at": str(a.fired_at),
            }
            for a in alerts
        ]
    finally:
        db.close()


@router.patch("/{alert_id}/resolve")
def resolve(alert_id: int):
    db = SessionLocal()
    try:
        alert = resolve_alert(db, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"id": alert_id, "resolved": True}
    finally:
        db.close()


@router.get("/rules")
def list_rules():
    db = SessionLocal()
    try:
        rules = db.query(AlertRule).filter(AlertRule.is_active == True).all()
        return [
            {
                "id": r.id, "name": r.name, "node_id": r.node_id,
                "metric": r.metric, "condition": r.condition, "threshold": r.threshold,
                "severity": r.severity, "is_active": r.is_active,
            }
            for r in rules
        ]
    finally:
        db.close()


@router.post("/rules")
def create_rule(req: AlertRuleCreate):
    """Create a new alert rule."""
    if req.condition not in ("less_than", "greater_than", "equals"):
        raise HTTPException(status_code=400, detail="condition must be: less_than, greater_than, or equals")
    db = SessionLocal()
    try:
        rule = AlertRule(**req.dict())
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return {"id": rule.id, "message": f"Alert rule '{req.name}' created"}
    finally:
        db.close()


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int):
    db = SessionLocal()
    try:
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        rule.is_active = False
        db.commit()
        return {"message": "Rule deactivated"}
    finally:
        db.close()
