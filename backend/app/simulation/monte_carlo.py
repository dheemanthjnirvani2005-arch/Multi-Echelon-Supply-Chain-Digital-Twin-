# backend/app/simulation/monte_carlo.py
"""
Enhanced Monte Carlo simulation engine with Celery task queue support.

Runs thousands of SimPy trials in parallel using ProcessPoolExecutor,
then computes percentile confidence bands (P10, P50, P90).
"""

import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List

import numpy as np

from app.simulation.engine import run_simulation

logger = logging.getLogger(__name__)

# ── Celery app (task queue) ────────────────────────────────────────────────────
try:
    from celery import Celery
    from app.core.config import settings
    celery_app = Celery(
        "supplychain_twin",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
    )
    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        task_track_started=True,
    )
    CELERY_AVAILABLE = True
except Exception:
    celery_app = None
    CELERY_AVAILABLE = False
    logger.warning("Celery not available — Monte Carlo tasks will run synchronously")


def _run_single_trial(args: tuple) -> dict:
    """
    Runs one complete SimPy simulation.
    Must be module-level for ProcessPoolExecutor pickling.
    """
    nodes_config, sim_days, seed = args
    np.random.seed(seed)

    result = run_simulation(nodes_config, sim_days, seed=seed)

    return {
        node_id: {
            "final_stock": data.get("avg_stock", 0),
            "stockouts": data.get("stockouts", 0),
            "service_level": data.get("service_level", 1.0),
        }
        for node_id, data in result.items()
    }


def run_monte_carlo_enhanced(
    nodes_config: list,
    sim_days: int = 90,
    n_trials: int = 1000,
    max_workers: int = None,
) -> dict:
    """
    Run Monte Carlo simulation with parallel execution.

    Returns per-node P10/P50/P90 bands for stock level and service level,
    plus stockout risk percentages.
    """
    if max_workers is None:
        max_workers = min(multiprocessing.cpu_count(), 8)

    logger.info(f"🎲 Starting Monte Carlo: {n_trials} trials × {sim_days} days on {max_workers} workers")

    tasks = [(nodes_config, sim_days, i * 42 + 7) for i in range(n_trials)]
    all_results: list = []

    # Use parallel processing for large trial counts
    if n_trials > 10:
        try:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(_run_single_trial, task): task for task in tasks}
                completed = 0
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=30)
                        all_results.append(result)
                        completed += 1
                        if completed % 100 == 0:
                            logger.info(f"  ✓ {completed}/{n_trials} trials done")
                    except Exception as e:
                        logger.warning(f"  ✗ Trial failed: {e}")
        except Exception as e:
            logger.warning(f"Parallel execution failed, falling back to sequential: {e}")
            all_results = [_run_single_trial(task) for task in tasks]
    else:
        all_results = [_run_single_trial(task) for task in tasks]

    logger.info(f"✅ Monte Carlo complete: {len(all_results)}/{n_trials} trials succeeded")
    return _aggregate_results(all_results, n_trials, sim_days)


def _aggregate_results(all_results: list, n_trials: int, sim_days: int) -> dict:
    """Convert raw trial outputs into P10/P50/P90 summary statistics."""
    if not all_results:
        return {"error": "All trials failed"}

    node_ids = list(all_results[0].keys())
    output = {}
    worst_node = None
    worst_service = 1.0

    for node_id in node_ids:
        stock_levels = [r[node_id]["final_stock"] for r in all_results if node_id in r]
        service_levels = [r[node_id]["service_level"] for r in all_results if node_id in r]
        stockout_counts = [r[node_id]["stockouts"] for r in all_results if node_id in r]

        if not stock_levels:
            continue

        p10_service = float(np.percentile(service_levels, 10))
        if p10_service < worst_service:
            worst_service = p10_service
            worst_node = node_id

        stockout_risk = sum(1 for s in stockout_counts if s > 0) / len(stockout_counts) * 100

        output[node_id] = {
            "stock_level": {
                "p10": round(float(np.percentile(stock_levels, 10)), 1),
                "p50": round(float(np.percentile(stock_levels, 50)), 1),
                "p90": round(float(np.percentile(stock_levels, 90)), 1),
                "mean": round(float(np.mean(stock_levels)), 1),
                "std": round(float(np.std(stock_levels)), 1),
            },
            "service_level": {
                "p10": round(p10_service, 4),
                "p50": round(float(np.percentile(service_levels, 50)), 4),
                "p90": round(float(np.percentile(service_levels, 90)), 4),
                "mean": round(float(np.mean(service_levels)), 4),
            },
            "stockout_risk_pct": round(stockout_risk, 1),
        }

    output["_summary"] = {
        "n_trials": n_trials,
        "n_succeeded": len(all_results),
        "sim_days": sim_days,
        "worst_node": worst_node,
    }

    return output


# ── Celery tasks ───────────────────────────────────────────────────────────────

if CELERY_AVAILABLE:
    @celery_app.task(bind=True, name="monte_carlo.run_full")
    def run_monte_carlo_task(self, simulation_run_id: int, nodes_config: list,
                             sim_days: int = 90, n_trials: int = 500):
        """Celery task: runs Monte Carlo in background and saves results to DB."""
        from app.db.session import SessionLocal
        from app.models.supply_chain import SimulationRun
        import asyncio
        import json

        db = SessionLocal()
        try:
            run = db.query(SimulationRun).filter(SimulationRun.id == simulation_run_id).first()
            if run:
                run.status = "running_monte_carlo"
                db.commit()

            result = run_monte_carlo_enhanced(nodes_config, sim_days, n_trials)

            if run:
                run.result = result
                run.status = "done"
                db.commit()

            # Notify browsers
            from app.websockets.manager import ws_manager
            try:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(ws_manager.broadcast(json.dumps({
                    "type": "monte_carlo_complete",
                    "run_id": simulation_run_id,
                    "summary": result.get("_summary", {}),
                })))
                loop.close()
            except Exception:
                pass

            logger.info(f"✅ Monte Carlo task done for run #{simulation_run_id}")
            return {"run_id": simulation_run_id, "status": "done"}

        except Exception as e:
            if run:
                run.status = "failed"
                run.result = {"error": str(e)}
                db.commit()
            raise
        finally:
            db.close()

    @celery_app.task(name="monte_carlo.trigger_for_node")
    def trigger_monte_carlo_for_node(node_id: str, n_trials: int = 200):
        """Quick re-simulation triggered when a node's stock drops."""
        from app.db.session import SessionLocal
        from app.models.supply_chain import Node

        db = SessionLocal()
        try:
            node = db.query(Node).filter(Node.name == node_id).first()
            if not node:
                return

            nodes_config = [{
                "id": node.name,
                "capacity": node.capacity or 1000,
                "initial_stock": node.current_stock or 0,
                "reorder_point": (node.capacity or 1000) * 0.2,
                "order_qty": (node.capacity or 1000) * 0.5,
                "lead_time_mu": 5,
                "lead_time_sigma": 1,
                "daily_demand_rate": 50,
            }]

            return run_monte_carlo_enhanced(nodes_config, sim_days=30, n_trials=n_trials)
        finally:
            db.close()
