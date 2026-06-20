# backend/app/mqtt/listener.py
"""
MQTT Listener — runs as a background thread alongside FastAPI.

Connects to Mosquitto broker, subscribes to sensor topics,
processes incoming readings, updates DB, checks alerts,
and pushes live updates to browser clients via WebSocket.
"""

import json
import logging
import threading
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger(__name__)

TOPIC_SUBSCRIBE = "sensors/#"

# Track whether paho-mqtt is available
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logger.warning("paho-mqtt not installed — MQTT listener disabled")


class MQTTListener:
    """Manages the MQTT connection and message processing."""

    def __init__(self):
        self._connected = False
        self.client = None

        if MQTT_AVAILABLE:
            try:
                self.client = mqtt.Client(client_id="supplychain-twin-backend", protocol=mqtt.MQTTv5)
                self.client.on_connect = self._on_connect
                self.client.on_message = self._on_message
                self.client.on_disconnect = self._on_disconnect
            except Exception:
                # MQTTv5 not supported in some versions
                self.client = mqtt.Client(client_id="supplychain-twin-backend")
                self.client.on_connect = self._on_connect_v3
                self.client.on_message = self._on_message
                self.client.on_disconnect = self._on_disconnect_v3

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("✅ MQTT connected to broker")
            self._connected = True
            client.subscribe(TOPIC_SUBSCRIBE, qos=1)
            logger.info(f"📡 Subscribed to topic: {TOPIC_SUBSCRIBE}")
        else:
            logger.error(f"❌ MQTT connection failed. Code: {rc}")

    def _on_connect_v3(self, client, userdata, flags, rc):
        self._on_connect(client, userdata, flags, rc)

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self._connected = False
        logger.warning(f"⚠️ MQTT disconnected (code {rc}). Will auto-reconnect.")

    def _on_disconnect_v3(self, client, userdata, rc):
        self._on_disconnect(client, userdata, rc)

    def _on_message(self, client, userdata, msg):
        """Called every time a sensor publishes a message."""
        try:
            parts = msg.topic.split("/")
            if len(parts) < 3:
                logger.warning(f"Unexpected topic format: {msg.topic}")
                return

            node_id = parts[1]
            metric = parts[2]

            payload = json.loads(msg.payload.decode("utf-8"))
            value = payload.get("value")
            unit = payload.get("unit", "")
            ts_str = payload.get("timestamp", datetime.now(timezone.utc).isoformat())

            if value is None:
                return

            logger.debug(f"📨 {msg.topic} → {value} {unit}")

            thread = threading.Thread(
                target=self._process_reading,
                args=(node_id, metric, float(value), unit, ts_str),
                daemon=True,
            )
            thread.start()

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from {msg.topic}: {msg.payload}")
        except Exception as e:
            logger.exception(f"Error processing message from {msg.topic}: {e}")

    def _process_reading(self, node_id, metric, value, unit, timestamp):
        """Save reading, update node, check alerts, push to WebSocket."""
        from app.db.session import SessionLocal
        from app.models.supply_chain import Node, SensorReading
        from app.alerts.engine import check_and_fire_alerts

        db = SessionLocal()
        try:
            # 1. Save raw sensor reading
            reading = SensorReading(
                node_id=node_id,
                metric=metric,
                value=value,
                unit=unit,
                timestamp=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
                raw_topic=f"sensors/{node_id}/{metric}",
            )
            db.add(reading)

            # 2. Update node state if stock_level
            node = db.query(Node).filter(Node.name == node_id).first()
            if node and metric == "stock_level":
                old_stock = node.current_stock
                node.current_stock = value
                logger.info(f"🏭 Node '{node_id}' stock: {old_stock} → {value}")

            db.commit()

            # 3. Check alert rules
            alerts_fired = check_and_fire_alerts(db, node_id, metric, value)

            # 4. Push to WebSocket
            import asyncio
            from app.websockets.manager import ws_manager
            update_payload = {
                "type": "sensor_update",
                "node_id": node_id,
                "metric": metric,
                "value": value,
                "unit": unit,
                "timestamp": timestamp,
                "alerts": [a.id for a in alerts_fired],
            }
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(ws_manager.broadcast(json.dumps(update_payload)))
                loop.close()
            except Exception:
                pass  # WebSocket broadcast is best-effort

        except Exception as e:
            db.rollback()
            logger.exception(f"Error in _process_reading for {node_id}/{metric}: {e}")
        finally:
            db.close()

    def start(self):
        """Connect to broker and start the MQTT loop in a background thread."""
        if not MQTT_AVAILABLE or not self.client:
            logger.warning("⚠️ MQTT listener disabled (paho-mqtt not installed)")
            return
        try:
            self.client.connect(
                host=settings.MQTT_BROKER_HOST,
                port=settings.MQTT_BROKER_PORT,
                keepalive=60,
            )
            self.client.loop_start()
            logger.info(f"🚀 MQTT listener started — {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
        except ConnectionRefusedError:
            logger.warning("⚠️ MQTT broker not reachable. Listener will be inactive.")
        except Exception as e:
            logger.warning(f"⚠️ MQTT start failed: {e}. Listener inactive.")

    def stop(self):
        """Gracefully disconnect."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("🛑 MQTT listener stopped")


# Global singleton
mqtt_listener = MQTTListener()
