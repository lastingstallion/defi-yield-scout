"""
Example: Run DeFi Yield Scout as a CROO provider agent.
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from croo import AgentClient, Config, EventType, DeliverableType, DeliverOrderRequest
from src.defi_engine import DeFiEngine


async def main():
    config = Config(
        base_url=os.environ["CROO_API_URL"],
        ws_url=os.environ["CROO_WS_URL"],
    )
    client = AgentClient(config, os.environ["CROO_SDK_KEY"])
    engine = DeFiEngine()

    print("🚀 DeFi Yield Scout — CROO Provider Agent")
    print(f"   Connecting to {config.base_url}...")

    stream = await client.connect_websocket()
    print("✅ Connected!")

    def on_negotiation(e):
        async def _():
            result = await client.accept_negotiation(e.negotiation_id)
            print(f"📝 Accepted: {result.order.order_id}")
        asyncio.create_task(_())

    def on_paid(e):
        async def _():
            print(f"💰 Order {e.order_id} paid — scanning...")
            result = await engine.full_report()
            await client.deliver_order(e.order_id, DeliverOrderRequest(
                deliverable_type=DeliverableType.TEXT,
                deliverable_text=json.dumps(result, indent=2, default=str),
            ))
            print(f"✅ Delivered: {e.order_id}")
        asyncio.create_task(_())

    stream.on(EventType.NEGOTIATION_CREATED, on_negotiation)
    stream.on(EventType.ORDER_PAID, on_paid)

    print("🎯 Listening for orders...")
    stop = asyncio.Event()
    await stop.wait()


if __name__ == "__main__":
    asyncio.run(main())
