#!/usr/bin/env python3
import asyncio, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.defi_engine import DeFiEngine

async def main():
    engine = DeFiEngine()
    
    r = await engine.scan_yields(limit=5)
    print(f'✅ scan_yields OK — {len(r["opportunities"])} results')
    
    t = await engine.trending_protocols(limit=5)
    print(f'✅ trending OK — {len(t["protocols"])} results')
    
    n = await engine.find_new_pools(max_age_days=30)
    print(f'✅ new_pools OK — {n["count"]} results')
    
    report = await engine.full_report()
    print(f'✅ full_report OK')
    print(f'   Opportunities: {report["summary"]["total_opportunities"]}')
    print(f'   Trending: {len(report["trending_protocols"])}')
    print(f'   New pools: {report["summary"]["new_pools_found"]}')
    print(f'   Hottest: {report["summary"]["hottest_protocol"]}')
    print()
    print('🎉 ALL ENGINE TESTS PASSED')

asyncio.run(main())
