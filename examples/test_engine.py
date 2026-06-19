"""
Test the DeFi engine standalone (no CROO dependency).
"""

import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.defi_engine import DeFiEngine


async def main():
    engine = DeFiEngine()

    print("=== Top Yield Opportunities ===")
    result = await engine.scan_yields(limit=5)
    print(json.dumps(result, indent=2, default=str))

    print("\n=== Trending Protocols ===")
    trending = await engine.trending_protocols(limit=5)
    print(json.dumps(trending, indent=2, default=str))

    print("\n=== New Pools (7 days) ===")
    new = await engine.find_new_pools(max_age_days=7)
    print(f"Found {new['count']} new pools")


if __name__ == "__main__":
    asyncio.run(main())
