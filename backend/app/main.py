# backend/app/main.py
"""
SupplyChain-Twin API — FastAPI entry point.
Phase 3: Real-Time & AI — MQTT, WebSocket, Monte Carlo, Alerts.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Existing Phase 1 & 2 routers
from app.api import network, simulations, scenarios, optimise, kpis, playbook

# Phase 3 routers
from app.api import monte_carlo_api, alerts_api, ws_route

# Services
from app.mqtt.listener import mqtt_listener
from app.websockets.manager import ws_manager
from app.db.session import engine, Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Startup / Shutdown lifecycle ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown."""
    # Create all database tables
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables ready")

    # Start MQTT listener in background
    mqtt_listener.start()
    logger.info("✅ MQTT listener started")

    yield  # App is now running and serving requests

    # Cleanup on shutdown
    mqtt_listener.stop()
    logger.info("🛑 MQTT listener stopped")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="SupplyChain-Twin API",
    version="2.0.0",
    description=(
        "Digital twin backend — Phase 3: Real-Time & AI. "
        "MQTT sensor integration, Monte Carlo simulation, "
        "AI playbooks (Claude), WebSocket live updates, and alerts."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Route registration ───────────────────────────────────────────────────────

# Phase 1 & 2 routes
app.include_router(network.router,     prefix="/api/v1/network",     tags=["Network"])
app.include_router(simulations.router, prefix="/api/v1/simulations", tags=["Simulations"])
app.include_router(scenarios.router,   prefix="/api/v1/scenarios",   tags=["Scenarios"])
app.include_router(optimise.router,    prefix="/api/v1/optimise",    tags=["Optimisation"])
app.include_router(kpis.router,        prefix="/api/v1/kpis",        tags=["KPIs"])
app.include_router(playbook.router,    prefix="/api/v1/playbook",    tags=["AI Playbook"])

# Phase 3 routes
app.include_router(monte_carlo_api.router, prefix="/api/v1/monte-carlo", tags=["Monte Carlo"])
app.include_router(alerts_api.router,      prefix="/api/v1/alerts",      tags=["Alerts"])

# Phase 4 routes
from app.api import resilience, carbon, suppliers, nps
app.include_router(resilience.router, prefix="/api/v1/resilience", tags=["Resilience"])
app.include_router(carbon.router,     prefix="/api/v1/carbon",     tags=["Carbon"])
app.include_router(suppliers.router,  prefix="/api/v1/suppliers",  tags=["Suppliers"])
app.include_router(nps.router,        prefix="/api/v1/nps",        tags=["NPS"])

# WebSocket (no /api prefix — different protocol)
app.include_router(ws_route.router, tags=["WebSocket"])


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    """Health check endpoint with service status."""
    return {
        "status": "ok",
        "version": "2.0.0",
        "mqtt_connected": mqtt_listener._connected,
        "ws_connections": ws_manager.connection_count,
    }
