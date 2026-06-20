# backend/app/alerts/engine.py
"""
Alert engine — checks incoming sensor readings against alert rules
and fires notifications when thresholds are breached.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.supply_chain import AlertRule, Alert

logger = logging.getLogger(__name__)

CONDITION_CHECKS = {
    "less_than":    lambda value, threshold: value < threshold,
    "greater_than": lambda value, threshold: value > threshold,
    "equals":       lambda value, threshold: abs(value - threshold) < 0.001,
}


def check_and_fire_alerts(
    db: Session,
    node_id: str,
    metric: str,
    value: float,
) -> List[Alert]:
    """
    Check all active alert rules against this reading and fire any that match.
    Returns a list of Alert records that were fired.
    """
    fired = []

    rules = db.query(AlertRule).filter(
        AlertRule.is_active == True,
        AlertRule.metric == metric,
    ).all()

    # Filter to rules matching this node or global rules
    matching_rules = [
        r for r in rules
        if r.node_id is None or r.node_id == node_id
    ]

    for rule in matching_rules:
        check_fn = CONDITION_CHECKS.get(rule.condition)
        if not check_fn:
            logger.warning(f"Unknown condition '{rule.condition}' in rule #{rule.id}")
            continue

        if check_fn(value, rule.threshold):
            # Avoid duplicate active alerts
            recent = db.query(Alert).filter(
                Alert.rule_id == rule.id,
                Alert.node_id == node_id,
                Alert.resolved == False,
            ).first()

            if recent:
                continue

            message = (
                f"[{rule.severity.upper()}] {rule.name}: "
                f"Node '{node_id}', metric '{metric}' = {value:.2f} "
                f"(threshold: {rule.condition.replace('_', ' ')} {rule.threshold})"
            )

            alert = Alert(
                rule_id=rule.id,
                node_id=node_id,
                metric=metric,
                value=value,
                threshold=rule.threshold,
                severity=rule.severity,
                message=message,
            )
            db.add(alert)
            db.flush()
            fired.append(alert)
            logger.warning(f"🚨 ALERT FIRED: {message}")

            if rule.notify_email:
                _send_email_notification(alert)
            if rule.notify_ws:
                _send_ws_notification(alert)

    if fired:
        db.commit()

    return fired


def _send_email_notification(alert: Alert):
    """Send email asynchronously."""
    import threading
    thread = threading.Thread(target=_email_worker, args=(alert,), daemon=True)
    thread.start()


def _email_worker(alert: Alert):
    """Actually sends the email (runs in background thread)."""
    import asyncio
    try:
        from app.alerts.email_sender import send_alert_email
        loop = asyncio.new_event_loop()
        loop.run_until_complete(send_alert_email(alert))
        loop.close()
    except Exception as e:
        logger.exception(f"Email send failed for alert #{alert.id}: {e}")


def _send_ws_notification(alert: Alert):
    """Push the alert to all connected browser clients via WebSocket."""
    import asyncio
    import json
    from app.websockets.manager import ws_manager
    payload = json.dumps({
        "type": "alert",
        "alert_id": alert.id,
        "node_id": alert.node_id,
        "metric": alert.metric,
        "value": alert.value,
        "threshold": alert.threshold,
        "severity": alert.severity,
        "message": alert.message,
    })
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(ws_manager.broadcast(payload))
        loop.close()
    except Exception as e:
        logger.exception(f"WebSocket notification failed: {e}")


def resolve_alert(db: Session, alert_id: int) -> Optional[Alert]:
    """Mark an alert as resolved."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.resolved = True
        alert.resolved_at = datetime.now(timezone.utc)
        db.commit()
    return alert
