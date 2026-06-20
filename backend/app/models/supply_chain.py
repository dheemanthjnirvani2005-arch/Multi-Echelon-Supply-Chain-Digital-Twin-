# backend/app/models/supply_chain.py
"""
SQLAlchemy ORM models for the SupplyChain-Twin database.

Tables:
  - nodes:            Supply chain entities (factories, DCs, retail)
  - edges:            Network lanes between nodes
  - skus:             Product master data
  - demand_records:   Historical demand data
  - simulation_runs:  Simulation job tracking
  - scenarios:        What-if scenario definitions
  - kpi_snapshots:    Time-series KPI metrics
  - recommendations:  Optimiser output recommendations
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, JSON, Text,
    ForeignKey, DateTime, UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Node(Base):
    """Supply chain network node (factory, distribution centre, retail store)."""
    __tablename__ = "nodes"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(255), nullable=False)
    node_type     = Column(String(50))   # factory / dc / retail
    latitude      = Column(Float)
    longitude     = Column(Float)
    capacity      = Column(Float, default=1000)
    current_stock = Column(Float, default=0)
    country       = Column(String(100))
    city          = Column(String(100))
    service_level_target = Column(Float, default=0.95)
    created_at    = Column(DateTime, server_default=func.now())

    # Relationships
    outgoing_edges = relationship("Edge", foreign_keys="Edge.from_node_id", back_populates="from_node")
    incoming_edges = relationship("Edge", foreign_keys="Edge.to_node_id", back_populates="to_node")


class Edge(Base):
    """Directed link between two nodes (a shipping lane)."""
    __tablename__ = "edges"

    id                 = Column(Integer, primary_key=True, index=True)
    from_node_id       = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    to_node_id         = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    transit_days_mu    = Column(Float, default=5.0)    # mean lead time
    transit_days_sigma = Column(Float, default=1.0)    # std dev lead time
    cost_per_unit      = Column(Float, default=1.0)
    co2e_per_unit      = Column(Float, default=0.0)    # kg CO₂e per unit shipped
    transport_mode     = Column(String(50), default="truck")  # truck / rail / ocean / air
    active             = Column(Boolean, default=True)

    from_node = relationship("Node", foreign_keys=[from_node_id], back_populates="outgoing_edges")
    to_node   = relationship("Node", foreign_keys=[to_node_id], back_populates="incoming_edges")


class SKU(Base):
    """Product master data."""
    __tablename__ = "skus"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(255), nullable=False)
    holding_cost    = Column(Float, default=2.0)
    stockout_cost   = Column(Float, default=50.0)
    unit_cost       = Column(Float, default=10.0)
    shelf_life_days = Column(Integer, nullable=True)
    perishable      = Column(Boolean, default=False)


class DemandRecord(Base):
    """Historical demand per SKU per node per period."""
    __tablename__ = "demand_records"

    id       = Column(Integer, primary_key=True, index=True)
    sku_id   = Column(Integer, ForeignKey("skus.id"))
    node_id  = Column(Integer, ForeignKey("nodes.id"))
    period   = Column(String(20))   # e.g. "2026-Q1", "2026-W12"
    quantity = Column(Float)
    source   = Column(String(50), default="csv")  # csv / erp / forecast


class Scenario(Base):
    """What-if scenario definition (can branch from another scenario)."""
    __tablename__ = "scenarios"

    id                = Column(Integer, primary_key=True, index=True)
    name              = Column(String(255))
    base_scenario_id  = Column(Integer, ForeignKey("scenarios.id"), nullable=True)
    disruption_events = Column(JSON, default=list)
    description       = Column(Text, nullable=True)
    created_by        = Column(String(100))
    created_at        = Column(DateTime, server_default=func.now())

    simulation_runs = relationship("SimulationRun", back_populates="scenario")


class SimulationRun(Base):
    """Tracks a single simulation execution."""
    __tablename__ = "simulation_runs"

    id          = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    status      = Column(String(20), default="pending")  # pending / running / done / failed
    config      = Column(JSON)
    result      = Column(JSON)
    created_at  = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    scenario = relationship("Scenario", back_populates="simulation_runs")


class KpiSnapshot(Base):
    """Time-series KPI data (designed for TimescaleDB hypertable)."""
    __tablename__ = "kpi_snapshots"

    id                = Column(Integer, primary_key=True, index=True)
    simulation_run_id = Column(Integer, ForeignKey("simulation_runs.id"))
    metric_name       = Column(String(100))  # service_level, inventory_turns, fill_rate, etc.
    value             = Column(Float)
    timestamp         = Column(DateTime, server_default=func.now())


class Recommendation(Base):
    """Optimiser output — suggested reorder point and quantity per node/SKU."""
    __tablename__ = "recommendations"

    id            = Column(Integer, primary_key=True, index=True)
    node_id       = Column(Integer, ForeignKey("nodes.id"))
    sku_id        = Column(Integer, ForeignKey("skus.id"), nullable=True)
    reorder_point = Column(Float)
    order_qty     = Column(Float)
    safety_stock  = Column(Float, nullable=True)
    method        = Column(String(50), default="pulp")  # pulp / nsga2
    generated_at  = Column(DateTime, server_default=func.now())


# ── Phase 3: Real-Time & AI Models ──────────────────────────────────────────


class SensorReading(Base):
    """Stores every raw reading that arrives via MQTT."""
    __tablename__ = "sensor_readings"

    id         = Column(Integer, primary_key=True, index=True)
    node_id    = Column(String, nullable=False, index=True)
    metric     = Column(String, nullable=False)
    value      = Column(Float, nullable=False)
    unit       = Column(String, default="")
    timestamp  = Column(DateTime(timezone=True), nullable=False)
    raw_topic  = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AlertRule(Base):
    """Defines when an alert should fire (e.g. stock < 20% of capacity)."""
    __tablename__ = "alert_rules"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String, nullable=False)
    node_id      = Column(String, nullable=True)
    metric       = Column(String, nullable=False)
    condition    = Column(String, nullable=False)  # less_than / greater_than / equals
    threshold    = Column(Float, nullable=False)
    severity     = Column(String, default="warning")
    notify_email = Column(Boolean, default=True)
    notify_ws    = Column(Boolean, default=True)
    is_active    = Column(Boolean, default=True)


class Alert(Base):
    """An alert that was actually fired."""
    __tablename__ = "alerts"

    id          = Column(Integer, primary_key=True, index=True)
    rule_id     = Column(Integer, ForeignKey("alert_rules.id"), nullable=True)
    node_id     = Column(String, nullable=False)
    metric      = Column(String, nullable=False)
    value       = Column(Float, nullable=False)
    threshold   = Column(Float, nullable=False)
    severity    = Column(String, nullable=False)
    message     = Column(Text)
    resolved    = Column(Boolean, default=False)
    fired_at    = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class Playbook(Base):
    """Stores AI-generated response playbooks."""
    __tablename__ = "playbooks"

    id                  = Column(Integer, primary_key=True, index=True)
    disruption_type     = Column(String, nullable=False)
    disruption_location = Column(String)
    severity            = Column(String)
    content             = Column(JSON)
    simulation_run_id   = Column(Integer, ForeignKey("simulation_runs.id"), nullable=True)
    created_by          = Column(String, default="system")
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    is_active           = Column(Boolean, default=True)


class PlaybookAction(Base):
    """Individual actions within a playbook, tracked to completion."""
    __tablename__ = "playbook_actions"

    id           = Column(Integer, primary_key=True, index=True)
    playbook_id  = Column(Integer, ForeignKey("playbooks.id"))
    phase        = Column(String)
    action       = Column(Text)
    owner        = Column(String)
    priority     = Column(String)
    deadline     = Column(String)
    status       = Column(String, default="open")
    assigned_to  = Column(String, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


# ── Phase 4: Advanced UX Models ──────────────────────────────────────────

class Route(Base):
    """A transport lane with its carbon footprint data."""
    __tablename__ = 'routes'

    id              = Column(Integer, primary_key=True)
    from_node_id    = Column(Integer, ForeignKey('nodes.id'))
    to_node_id      = Column(Integer, ForeignKey('nodes.id'))
    transport_mode  = Column(String)   # sea / air / rail / road / multimodal
    distance_km     = Column(Float)
    emission_factor = Column(Float)    # kg CO2e per tonne-km
    avg_shipment_tonnes = Column(Float, default=20.0)
    monthly_shipments   = Column(Integer, default=4)
    is_active       = Column(Boolean, default=True)


class CarbonRecord(Base):
    """Monthly CO2e totals per route — feeds the trend chart."""
    __tablename__ = 'carbon_records'

    id            = Column(Integer, primary_key=True)
    route_id      = Column(Integer, ForeignKey('routes.id'))
    period_month  = Column(String)    # YYYY-MM
    co2e_tonnes   = Column(Float)
    shipments     = Column(Integer)
    recorded_at   = Column(DateTime(timezone=True), server_default=func.now())


class Supplier(Base):
    """A supplier in your supply chain."""
    __tablename__ = 'suppliers'

    id           = Column(Integer, primary_key=True)
    name         = Column(String, nullable=False)
    country      = Column(String)
    city         = Column(String)
    latitude     = Column(Float)
    longitude    = Column(Float)
    tier         = Column(Integer, default=1)   # 1 = direct, 2 = tier-2, 3 = tier-3
    is_active    = Column(Boolean, default=True)
    risk_score   = Column(Float, default=0.5)   # 0=low, 1=high
    hhi_score    = Column(Float, default=0.0)
    max_share_pct = Column(Float, default=0.0)


class SupplierComponent(Base):
    """A component that your business sources from a supplier."""
    __tablename__ = 'supplier_components'

    id              = Column(Integer, primary_key=True)
    sku_id          = Column(Integer, ForeignKey('skus.id'), nullable=True)
    component_name  = Column(String, nullable=False)    # e.g. "Lithium Battery Cells"
    supplier_id     = Column(Integer, ForeignKey('suppliers.id'))
    annual_spend_usd = Column(Float, default=0)
    share_pct       = Column(Float, default=0)          # % of this component sourced from this supplier
    lead_time_days  = Column(Integer, default=30)
    is_sole_source  = Column(Boolean, default=False)    # only supplier for this component


class NPSResponse(Base):
    """User feedback for NPS survey."""
    __tablename__ = 'nps_responses'
    id          = Column(Integer, primary_key=True)
    score       = Column(Integer, nullable=False)   # 0–10
    comment     = Column(String, nullable=True)
    user_role   = Column(String, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

