"""
Supplier HHI (Herfindahl-Hirschman Index) concentration scorer.
"""

import logging
from collections import defaultdict
from sqlalchemy.orm import Session
from app.models.supply_chain import Supplier, SupplierComponent, Alert, AlertRule

logger = logging.getLogger(__name__)


def calculate_hhi_for_component(shares: list[float]) -> float:
    """
    HHI = sum of squared market shares (as percentages).
    """
    return sum(s ** 2 for s in shares)


def score_all_suppliers(db: Session) -> dict:
    """
    Calculate HHI for every component and return a full report.
    """
    records = db.query(SupplierComponent).all()

    by_component: dict[str, list] = defaultdict(list)
    for rec in records:
        supplier = db.query(Supplier).filter(Supplier.id == rec.supplier_id).first()
        if supplier and supplier.is_active:
            by_component[rec.component_name].append({
                "supplier_id":   rec.supplier_id,
                "supplier_name": supplier.name,
                "country":       supplier.country or "Unknown",
                "share_pct":     rec.share_pct,
                "annual_spend":  rec.annual_spend_usd,
                "lead_time":     rec.lead_time_days,
                "is_sole_source": rec.is_sole_source,
            })

    component_results = []
    portfolio_hhis    = []
    high_risk_count   = 0
    alerts_fired      = 0

    for component_name, suppliers in by_component.items():
        shares = [s["share_pct"] for s in suppliers]
        hhi    = calculate_hhi_for_component(shares)
        portfolio_hhis.append(hhi)

        risk_level = "low" if hhi < 1500 else "medium" if hhi < 2500 else "high"
        if risk_level == "high":
            high_risk_count += 1

        dominant = max(suppliers, key=lambda s: s["share_pct"]) if suppliers else None

        if hhi > 2500 and dominant:
            recommendation = (
                f"Add 2–3 alternative suppliers for {component_name}. "
                f"Reduce {dominant['supplier_name']}'s share from {dominant['share_pct']:.0f}% "
                f"to below 40% to reach HHI < 2500."
            )
        elif hhi > 1500:
            recommendation = (
                f"Consider qualifying one additional supplier for {component_name} "
                f"to reduce concentration risk."
            )
        else:
            recommendation = "Well diversified. No action required."

        if dominant and dominant["share_pct"] > 60:
            alerts_fired += _create_concentration_alert(db, component_name, dominant)

        if dominant:
            sup = db.query(Supplier).filter(Supplier.id == dominant["supplier_id"]).first()
            if sup:
                sup.hhi_score    = hhi
                sup.max_share_pct = dominant["share_pct"]

        component_results.append({
            "component_name":     component_name,
            "hhi_score":          round(hhi, 0),
            "risk_level":         risk_level,
            "risk_color":         "#EF4444" if risk_level == "high" else "#F59E0B" if risk_level == "medium" else "#22C55E",
            "suppliers":          sorted(suppliers, key=lambda s: s["share_pct"], reverse=True),
            "dominant_supplier":  dominant["supplier_name"] if dominant else None,
            "dominant_share_pct": dominant["share_pct"] if dominant else 0,
            "supplier_count":     len(suppliers),
            "recommendation":     recommendation,
        })

    db.commit()

    portfolio_hhi = sum(portfolio_hhis) / len(portfolio_hhis) if portfolio_hhis else 0

    return {
        "components":        sorted(component_results, key=lambda x: x["hhi_score"], reverse=True),
        "portfolio_hhi":     round(portfolio_hhi, 0),
        "portfolio_risk":    "high" if portfolio_hhi > 2500 else "medium" if portfolio_hhi > 1500 else "low",
        "high_risk_count":   high_risk_count,
        "total_components":  len(component_results),
        "alerts_fired":      alerts_fired,
    }


def _create_concentration_alert(db: Session, component: str, dominant: dict) -> int:
    """Create a concentration alert if one doesn't already exist."""
    existing = db.query(Alert).filter(
        Alert.node_id  == f"supplier-{dominant['supplier_id']}",
        Alert.metric   == "concentration_pct",
        Alert.resolved == False,
    ).first()

    if existing:
        return 0

    alert = Alert(
        rule_id   = None,
        node_id   = f"supplier-{dominant['supplier_id']}",
        metric    = "concentration_pct",
        value     = dominant["share_pct"],
        threshold = 60.0,
        severity  = "warning",
        message   = (
            f"Supplier concentration risk: {dominant['supplier_name']} supplies "
            f"{dominant['share_pct']:.0f}% of {component} (threshold: 60%)"
        ),
    )
    db.add(alert)
    db.flush()
    logger.warning(f"⚠️  Concentration alert: {alert.message}")
    return 1
