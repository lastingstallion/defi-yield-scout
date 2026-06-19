"""
DeFi Yield Scout — CROO Agent
Monitors DeFi yield farming opportunities across 20+ chains.
"""

import asyncio
import json
import os
import logging
from datetime import datetime, timezone

from croo import (
    AgentClient,
    Config,
    EventType,
    DeliverableType,
    DeliverOrderRequest,
    ListOptions,
    APIError,
)

from defi_engine import DeFiEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("defi-yield-scout")

# --- Configuration ---
config = Config(
    base_url=os.environ["CROO_API_URL"],
    ws_url=os.environ["CROO_WS_URL"],
)

client = AgentClient(config, os.environ["CROO_SDK_KEY"])
engine = DeFiEngine()


async def handle_negotiation(event):
    """Accept incoming service requests."""
    try:
        result = await client.accept_negotiation(event.negotiation_id)
        logger.info(f"Accepted negotiation {event.negotiation_id} → Order {result.order.order_id}")
    except APIError as e:
        logger.error(f"Failed to accept negotiation: {e}")


async def handle_payment(event):
    """Process paid orders — run analysis and deliver results."""
    order_id = event.order_id
    logger.info(f"Order {order_id} paid — running analysis...")

    try:
        order = await client.get_order(order_id)
        requirements = json.loads(order.requirements) if order.requirements else {}
        service_id = requirements.get("service_id", "yield-scan")

        # Route to the right analysis
        if service_id == "yield-scan":
            result = await engine.scan_yields(
                chain=requirements.get("chain"),
                min_tvl=requirements.get("min_tvl", 100000),
                limit=requirements.get("limit", 20),
            )
        elif service_id == "risk-analysis":
            result = await engine.analyze_risk(
                protocol=requirements.get("protocol", ""),
                chain=requirements.get("chain"),
            )
        elif service_id == "new-pools":
            result = await engine.find_new_pools(
                max_age_days=requirements.get("max_age_days", 7),
                chain=requirements.get("chain"),
            )
        elif service_id == "trending":
            result = await engine.trending_protocols(
                chain=requirements.get("chain"),
                limit=requirements.get("limit", 10),
            )
        elif service_id == "full-report":
            result = await engine.full_report(
                chain=requirements.get("chain"),
            )
        else:
            result = {"error": f"Unknown service: {service_id}"}

        # Deliver the result
        await client.deliver_order(order_id, DeliverOrderRequest(
            deliverable_type=DeliverableType.TEXT,
            deliverable_text=json.dumps(result, indent=2, default=str),
        ))
        logger.info(f"Order {order_id} delivered successfully")

    except Exception as e:
        logger.error(f"Failed to process order {order_id}: {e}")
        try:
            await client.deliver_order(order_id, DeliverOrderRequest(
                deliverable_type=DeliverableType.TEXT,
                deliverable_text=json.dumps({"error": str(e)}),
            ))
        except Exception:
            pass


async def main():
    """Start the agent and listen for events."""
    logger.info("🚀 DeFi Yield Scout starting...")
    logger.info(f"   API: {config.base_url}")

    stream = await client.connect_websocket()
    logger.info("✅ WebSocket connected")

    stream.on(EventType.NEGOTIATION_CREATED, lambda e: asyncio.create_task(handle_negotiation(e)))
    stream.on(EventType.ORDER_PAID, lambda e: asyncio.create_task(handle_payment(e)))

    logger.info("🎯 Listening for orders... (Ctrl+C to stop)")

    stop = asyncio.Event()
    try:
        await stop.wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
    finally:
        await stream.close()


if __name__ == "__main__":
    asyncio.run(main())
