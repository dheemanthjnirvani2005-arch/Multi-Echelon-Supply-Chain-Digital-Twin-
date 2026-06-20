# backend/app/ai/playbook.py
"""
AI-powered disruption response playbook generator using Claude API.

Given a disruption event and simulation results, produces a structured
operational response with immediate, short-term, and long-term actions.
"""
import json
from typing import Dict, Any

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


SYSTEM_PROMPT = """You are a senior supply chain resilience expert with 20 years of experience.
Given a disruption event and simulation results, produce a structured operational response
playbook in JSON format with exactly these three keys:
  - immediate_actions  (0-48 hours)
  - short_term_mitigations  (1-4 weeks)
  - long_term_fixes  (1-6 months)

Each key maps to an array of objects with these fields:
  { "action": string, "owner": string, "priority": "high"|"medium"|"low", "deadline": string }

Return ONLY valid JSON with no markdown fencing, preamble, or commentary."""


def generate_playbook(disruption_event: Dict[str, Any], sim_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate an AI-powered response playbook for a supply chain disruption.

    Args:
        disruption_event: e.g. {"type": "port_closure", "location": "Rotterdam", "duration_days": 14}
        sim_results: KPI impact summary from the simulation engine

    Returns:
        Parsed playbook dict with immediate_actions, short_term_mitigations, long_term_fixes
    """
    if not ANTHROPIC_AVAILABLE:
        return _fallback_playbook(disruption_event)

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment

    prompt = f"""
Disruption event:
{json.dumps(disruption_event, indent=2)}

Simulation KPI impact:
{json.dumps(sim_results, indent=2)}

Generate the complete operational response playbook.
"""
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text
    return json.loads(raw)


def _fallback_playbook(disruption_event: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback when Anthropic API is not available."""
    event_type = disruption_event.get("type", "unknown")
    location = disruption_event.get("location", "Unknown Location")

    return {
        "immediate_actions": [
            {
                "action": f"Assess immediate impact of {event_type} at {location}",
                "owner": "Supply Chain Manager",
                "priority": "high",
                "deadline": "Within 4 hours",
            },
            {
                "action": "Activate emergency communication protocol with affected suppliers",
                "owner": "Procurement Lead",
                "priority": "high",
                "deadline": "Within 8 hours",
            },
            {
                "action": "Review current inventory levels at all downstream nodes",
                "owner": "Inventory Analyst",
                "priority": "high",
                "deadline": "Within 12 hours",
            },
        ],
        "short_term_mitigations": [
            {
                "action": "Identify and qualify alternative suppliers for critical components",
                "owner": "Procurement Lead",
                "priority": "high",
                "deadline": "Within 1 week",
            },
            {
                "action": "Reroute shipments through alternative logistics corridors",
                "owner": "Logistics Manager",
                "priority": "medium",
                "deadline": "Within 2 weeks",
            },
            {
                "action": "Increase safety stock levels at critical distribution centres",
                "owner": "Inventory Analyst",
                "priority": "medium",
                "deadline": "Within 3 weeks",
            },
        ],
        "long_term_fixes": [
            {
                "action": "Diversify supplier base to reduce single-point-of-failure risk",
                "owner": "VP Supply Chain",
                "priority": "high",
                "deadline": "Within 3 months",
            },
            {
                "action": "Implement multi-modal transport strategy for resilience",
                "owner": "Logistics Director",
                "priority": "medium",
                "deadline": "Within 6 months",
            },
            {
                "action": "Deploy IoT sensors for real-time disruption early warning",
                "owner": "IT/Data Engineering",
                "priority": "low",
                "deadline": "Within 6 months",
            },
        ],
    }
