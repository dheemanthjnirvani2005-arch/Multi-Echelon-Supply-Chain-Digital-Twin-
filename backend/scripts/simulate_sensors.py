# backend/scripts/simulate_sensors.py
"""
IoT Sensor Simulator — generates fake sensor data for testing.

Publishes realistic stock level readings to the MQTT broker
every few seconds, simulating warehouse IoT devices.

Usage:
  python backend/scripts/simulate_sensors.py

Keep this running in a separate terminal while testing.
"""

import json
import random
import time
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

BROKER_HOST = "localhost"
BROKER_PORT = 1883

NODES = [
    {"id": "warehouse-london-01", "capacity": 5000, "current_stock": 4200},
    {"id": "warehouse-berlin-01", "capacity": 3000, "current_stock": 2800},
    {"id": "warehouse-tokyo-01", "capacity": 4000, "current_stock": 1100},
    {"id": "factory-shanghai-01", "capacity": 8000, "current_stock": 6500},
    {"id": "dc-rotterdam-01", "capacity": 12000, "current_stock": 9800},
]


def simulate():
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        logger.error("paho-mqtt not installed. Run: pip install paho-mqtt")
        return

    logger.info("🚀 Sensor simulator starting...")

    client = mqtt.Client(client_id="sensor-simulator")
    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    except ConnectionRefusedError:
        logger.error(f"❌ Cannot connect to MQTT broker at {BROKER_HOST}:{BROKER_PORT}")
        logger.error("   Make sure Mosquitto is running: docker-compose up -d mosquitto")
        return

    client.loop_start()

    try:
        while True:
            for node in NODES:
                # Simulate stock draining
                drain = random.uniform(10, 80)
                node["current_stock"] = max(0, node["current_stock"] - drain)

                # Occasional demand spike
                if random.random() < 0.05:
                    spike = random.uniform(200, 600)
                    node["current_stock"] = max(0, node["current_stock"] - spike)
                    logger.warning(f"⚡ DEMAND SPIKE at {node['id']}: -{spike:.0f} units")

                # Occasional replenishment
                if node["current_stock"] < node["capacity"] * 0.25:
                    if random.random() < 0.3:
                        refill = random.uniform(500, 1500)
                        node["current_stock"] = min(node["capacity"], node["current_stock"] + refill)
                        logger.info(f"🔄 REPLENISHMENT at {node['id']}: +{refill:.0f} units")

                # Publish stock level
                topic = f"sensors/{node['id']}/stock_level"
                payload = json.dumps({
                    "value": round(node["current_stock"], 2),
                    "unit": "units",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "node_id": node["id"],
                })
                client.publish(topic, payload, qos=1)
                logger.info(f"📤 {node['id']}: {node['current_stock']:.0f} units")

                # Publish utilisation percentage
                util = node["current_stock"] / node["capacity"] * 100
                topic_util = f"sensors/{node['id']}/utilisation_pct"
                payload_util = json.dumps({
                    "value": round(util, 2),
                    "unit": "%",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "node_id": node["id"],
                })
                client.publish(topic_util, payload_util, qos=1)

            logger.info("--- Waiting 5 seconds ---")
            time.sleep(5)

    except KeyboardInterrupt:
        logger.info("🛑 Simulator stopped by user")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    simulate()
