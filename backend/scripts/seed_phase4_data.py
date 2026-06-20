"""
Seeds sample suppliers, components, and routes so Phase 4 features
have data to display immediately.

Usage: python backend/scripts/seed_phase4_data.py
"""

import sys
sys.path.append('backend')

from app.db.session import SessionLocal
from app.models.supply_chain import Supplier, SupplierComponent, Route, Node

db = SessionLocal()

# ── Suppliers ──
SUPPLIERS = [
    {"name": "CATL",           "country": "China",  "tier": 1, "latitude": 26.6, "longitude": 119.0},
    {"name": "Panasonic EV",   "country": "Japan",  "tier": 1, "latitude": 34.7, "longitude": 135.5},
    {"name": "Samsung SDI",    "country": "South Korea", "tier": 1, "latitude": 37.5, "longitude": 126.9},
    {"name": "SK Innovation",  "country": "South Korea", "tier": 1, "latitude": 37.5, "longitude": 127.0},
    {"name": "TSMC",           "country": "Taiwan", "tier": 1, "latitude": 24.8, "longitude": 120.9},
    {"name": "Intel Fab",      "country": "USA",    "tier": 1, "latitude": 45.5, "longitude": -122.7},
    {"name": "Foxconn",        "country": "China",  "tier": 2, "latitude": 22.5, "longitude": 114.1},
    {"name": "Flex Ltd",       "country": "Singapore", "tier": 2, "latitude": 1.3, "longitude": 103.8},
]

supplier_map = {}
for s_data in SUPPLIERS:
    existing = db.query(Supplier).filter(Supplier.name == s_data["name"]).first()
    if not existing:
        s = Supplier(**s_data)
        db.add(s); db.flush()
        supplier_map[s_data["name"]] = s.id
        print(f"✅ Supplier: {s_data['name']}")
    else:
        supplier_map[s_data["name"]] = existing.id

db.commit()

# ── Supplier Components ──
COMPONENTS = [
    # Battery cells — high concentration on CATL
    {"component_name": "Lithium Battery Cells",    "supplier": "CATL",          "share_pct": 65, "annual_spend_usd": 4200000},
    {"component_name": "Lithium Battery Cells",    "supplier": "Panasonic EV",  "share_pct": 25, "annual_spend_usd": 1600000},
    {"component_name": "Lithium Battery Cells",    "supplier": "Samsung SDI",   "share_pct": 10, "annual_spend_usd": 640000},
    # Semiconductors — very high concentration
    {"component_name": "Logic Chips (12nm)",       "supplier": "TSMC",          "share_pct": 90, "annual_spend_usd": 8900000, "is_sole_source": True},
    {"component_name": "Logic Chips (12nm)",       "supplier": "Intel Fab",     "share_pct": 10, "annual_spend_usd": 990000},
    # Enclosures — well diversified
    {"component_name": "Enclosures & Housings",    "supplier": "Foxconn",       "share_pct": 45, "annual_spend_usd": 800000},
    {"component_name": "Enclosures & Housings",    "supplier": "Flex Ltd",      "share_pct": 30, "annual_spend_usd": 530000},
    {"component_name": "Enclosures & Housings",    "supplier": "SK Innovation", "share_pct": 25, "annual_spend_usd": 440000},
]

for comp_data in COMPONENTS:
    sup_id = supplier_map.get(comp_data.pop("supplier"))
    if sup_id:
        existing = db.query(SupplierComponent).filter(
            SupplierComponent.component_name == comp_data["component_name"],
            SupplierComponent.supplier_id    == sup_id,
        ).first()
        if not existing:
            db.add(SupplierComponent(supplier_id=sup_id, **comp_data))
            print(f"✅ Component: {comp_data['component_name']} ({comp_data['share_pct']}%)")

db.commit()

# ── Routes (for Carbon module) ──
nodes = db.query(Node).all()
if len(nodes) >= 2:
    ROUTES = [
        {"from_node_id": nodes[0].id, "to_node_id": nodes[1].id, "transport_mode": "sea",  "distance_km": 18200, "avg_shipment_tonnes": 120, "monthly_shipments": 2},
        {"from_node_id": nodes[0].id, "to_node_id": nodes[1].id, "transport_mode": "air",  "distance_km": 9100,  "avg_shipment_tonnes": 8,   "monthly_shipments": 6},
        {"from_node_id": nodes[1].id, "to_node_id": nodes[-1].id, "transport_mode": "road", "distance_km": 800,   "avg_shipment_tonnes": 20,  "monthly_shipments": 8},
    ]
    from app.analytics.carbon import EMISSION_FACTORS
    for r_data in ROUTES:
        r_data["emission_factor"] = EMISSION_FACTORS[r_data["transport_mode"]]
        db.add(Route(**r_data))
        print(f"✅ Route: {r_data['transport_mode']} {r_data['distance_km']}km")

db.commit()
db.close()
print("\n✅ Phase 4 seed data complete.")
