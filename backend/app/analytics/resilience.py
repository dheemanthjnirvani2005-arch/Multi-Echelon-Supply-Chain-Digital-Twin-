"""
Calculates the six-axis resilience scores that power the radar chart.
Each score is 0.0 (terrible) to 1.0 (perfect), then inverted for "risk".
So a score of 0.8 on the radar means 80% risk = bad.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.supply_chain import (
    Node, Edge, AlertRule, Alert, SensorReading,
    SimulationRun, Supplier
)

logger = logging.getLogger(__name__)


def calculate_resilience_scores(db: Session, scenario_id: int = None) -> dict:
    """
    Calculate all six resilience axes.
    """
    scores = {}
    breakdown = {}

    # ── 1. SUPPLIER RISK — from HHI concentration scores ────────────────────
    suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    if suppliers:
        # Average HHI across all components (HHI is 0–10000, normalise to 0–1)
        avg_hhi = sum(s.hhi_score for s in suppliers) / len(suppliers)
        supplier_risk = min(1.0, avg_hhi / 6000)  # >6000 HHI = high concentration

        # Penalty for any supplier over 60% share
        high_conc = [s for s in suppliers if s.max_share_pct > 60]
        concentration_penalty = min(0.3, len(high_conc) * 0.1)

        scores["supplier_risk"] = min(1.0, supplier_risk + concentration_penalty)
        breakdown["supplier_risk"] = {
            "avg_hhi":              round(avg_hhi, 1),
            "high_concentration_count": len(high_conc),
            "total_suppliers":      len(suppliers),
        }
    else:
        scores["supplier_risk"] = 0.5   # unknown = medium risk
        breakdown["supplier_risk"] = {"note": "No supplier data"}

    # ── 2. LOGISTICS RISK — from Monte Carlo service level P10 ────────────────
    recent_run = db.query(SimulationRun).filter(
        SimulationRun.status == 'done'
    ).order_by(SimulationRun.created_at.desc()).first()

    if recent_run and recent_run.result:
        result = recent_run.result
        service_levels = [
            v.get("service_level", {}).get("p10", 1.0)
            for v in result.values()
            if isinstance(v, dict) and "service_level" in v
        ]
        if service_levels:
            worst_p10 = min(service_levels)
            scores["logistics_risk"] = round(1.0 - worst_p10, 3)
            breakdown["logistics_risk"] = {
                "worst_p10_service_level": round(worst_p10, 3),
                "nodes_analysed":         len(service_levels),
            }
        else:
            scores["logistics_risk"] = 0.5
    else:
        scores["logistics_risk"] = 0.5
        breakdown["logistics_risk"] = {"note": "No simulation data"}

    # ── 3. DEMAND RISK — coefficient of variation of demand ──────────────────
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    readings = db.query(SensorReading).filter(
        SensorReading.metric   == 'stock_level',
        SensorReading.timestamp >= cutoff,
    ).all()

    if readings:
        values = [r.value for r in readings]
        mean   = sum(values) / len(values)
        std    = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        cv     = std / mean if mean > 0 else 0
        scores["demand_risk"] = round(min(1.0, cv * 2), 3)   # CV > 0.5 = high risk
        breakdown["demand_risk"] = {
            "coefficient_of_variation": round(cv, 3),
            "readings_analysed":       len(readings),
        }
    else:
        scores["demand_risk"] = 0.4
        breakdown["demand_risk"] = {"note": "No sensor data"}

    # ── 4. FINANCIAL RISK — from unresolved critical alerts ──────────────────
    open_critical = db.query(Alert).filter(
        Alert.severity == 'critical',
        Alert.resolved == False,
    ).count()

    open_warning = db.query(Alert).filter(
        Alert.severity == 'warning',
        Alert.resolved == False,
    ).count()

    total_nodes = db.query(Node).count() or 1
    financial_risk = min(1.0, (open_critical * 0.15 + open_warning * 0.05) / total_nodes)
    scores["financial_risk"] = round(financial_risk, 3)
    breakdown["financial_risk"] = {
        "open_critical_alerts": open_critical,
        "open_warning_alerts":  open_warning,
        "total_nodes":          total_nodes,
    }

    # ── 5. REGULATORY RISK — static/user-configured (placeholder) ────────────
    scores["regulatory_risk"] = 0.25
    breakdown["regulatory_risk"] = {
        "note": "Manually configured. Connect a regulatory feed to automate.",
        "active_regulations": 3,
    }

    # ── 6. CLIMATE RISK — based on weather alerts at node locations ──────────
    weather_alerts = db.query(Alert).filter(
        Alert.metric.in_(['temperature_deviation', 'flood_risk', 'storm_warning']),
        Alert.resolved == False,
    ).count()

    scores["climate_risk"] = round(min(1.0, weather_alerts * 0.15), 3)
    breakdown["climate_risk"] = {
        "active_weather_alerts": weather_alerts,
        "note": "Integrate Open-Meteo API for real-time climate data",
    }

    # ── Overall score ─────────────────────────────────────────────────────────
    weights = {
        "supplier_risk":   0.25,
        "logistics_risk":  0.25,
        "demand_risk":     0.20,
        "financial_risk":  0.15,
        "regulatory_risk": 0.08,
        "climate_risk":    0.07,
    }
    weighted_risk = sum(scores[k] * w for k, w in weights.items())
    overall_score = round((1.0 - weighted_risk) * 100)   # higher = more resilient

    return {
        **scores,
        "overall_score": overall_score,
        "computed_at":   datetime.now(timezone.utc).isoformat(),
        "breakdown":     breakdown,
    }
