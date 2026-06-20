# backend/scripts/seed_alert_rules.py
"""
Run once to create default alert rules in the database.
Usage: python backend/scripts/seed_alert_rules.py
"""
import sys
sys.path.insert(0, ".")

from app.db.session import SessionLocal
from app.models.supply_chain import AlertRule

DEFAULT_RULES = [
    {
        "name": "Critical Low Stock",
        "metric": "utilisation_pct",
        "condition": "less_than",
        "threshold": 20.0,
        "severity": "critical",
    },
    {
        "name": "Warning Low Stock",
        "metric": "utilisation_pct",
        "condition": "less_than",
        "threshold": 35.0,
        "severity": "warning",
    },
    {
        "name": "Overstock Warning",
        "metric": "utilisation_pct",
        "condition": "greater_than",
        "threshold": 95.0,
        "severity": "warning",
    },
    {
        "name": "Zero Stock — Stockout",
        "metric": "stock_level",
        "condition": "less_than",
        "threshold": 1.0,
        "severity": "critical",
    },
]

if __name__ == "__main__":
    db = SessionLocal()
    for rule_data in DEFAULT_RULES:
        existing = db.query(AlertRule).filter(AlertRule.name == rule_data["name"]).first()
        if not existing:
            db.add(AlertRule(**rule_data))
            print(f"✅ Created rule: {rule_data['name']}")
        else:
            print(f"⏭  Already exists: {rule_data['name']}")
    db.commit()
    db.close()
    print("Done.")
