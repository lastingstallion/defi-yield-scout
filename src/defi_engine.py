"""
DeFi Intelligence Engine
Scrapes DeFiLlama for yield opportunities, TVL data, and risk metrics.
"""

import httpx
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("defi-yield-scout")

DEFILLAMA_YIELDS = "https://yields.llama.fi/pools"
DEFILLAMA_TVL = "https://api.llama.fi/tvl"
DEFILLAMA_PROTOCOLS = "https://api.llama.fi/protocols"
DEFILLAMA_CHART = "https://api.llama.fi/protocol"

# Risk scoring weights
RISK_FACTORS = {
    "tvl_multiplier": 0.3,      # Higher TVL = safer
    "audit_score": 0.25,        # Audited protocols score higher
    "age_multiplier": 0.2,      # Older protocols = more battle-tested
    "apy_sustainability": 0.25, # Extremely high APY = suspicious
}


class DeFiEngine:
    """DeFi data aggregation and analysis engine."""

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30,
            headers={
                "User-Agent": "DeFiYieldScout/1.0 (CROO Agent)",
                "Accept-Encoding": "gzip, deflate",
            },
        )

    async def _fetch_pools(self) -> list:
        """Fetch all yield pools from DeFiLlama."""
        resp = await self.client.get(DEFILLAMA_YIELDS)
        resp.raise_for_status()
        return resp.json().get("data", [])

    async def _fetch_protocols(self) -> list:
        """Fetch protocol TVL data."""
        resp = await self.client.get(DEFILLAMA_PROTOCOLS)
        resp.raise_for_status()
        return resp.json()

    def _score_risk(self, pool: dict, protocol_data: dict = None) -> dict:
        """Calculate risk score for a pool (0-100, lower = safer)."""
        risk = 50  # baseline

        tvl = pool.get("tvlUsd", 0)
        apy = pool.get("apy", 0)
        apy_base = pool.get("apyBase", 0) or 0

        # TVL factor
        if tvl > 100_000_000:
            risk -= 20
        elif tvl > 10_000_000:
            risk -= 10
        elif tvl > 1_000_000:
            risk -= 5
        elif tvl < 100_000:
            risk += 15

        # APY sustainability
        if apy > 100:
            risk += 25
        elif apy > 50:
            risk += 15
        elif apy > 20:
            risk += 5

        # Reward vs base APY (reward tokens = higher risk)
        apy_reward = apy - apy_base
        if apy_reward > apy_base * 2:
            risk += 10

        # IL risk for LP positions
        if pool.get("ilRisk") == "yes":
            risk += 5

        risk = max(0, min(100, risk))

        if risk < 30:
            label = "🟢 LOW"
        elif risk < 60:
            label = "🟡 MEDIUM"
        else:
            label = "🔴 HIGH"

        return {"score": risk, "label": label}

    async def scan_yields(
        self,
        chain: Optional[str] = None,
        min_tvl: float = 100_000,
        limit: int = 20,
    ) -> dict:
        """Scan for top yield opportunities."""
        pools = await self._fetch_pools()
        now = datetime.now(timezone.utc)

        # Filter
        filtered = []
        for p in pools:
            if p.get("tvlUsd", 0) < min_tvl:
                continue
            if chain and p.get("chain", "").lower() != chain.lower():
                continue
            if p.get("apy", 0) <= 0:
                continue
            # Skip stablecoin-only if apy < 1%
            filtered.append(p)

        # Sort by APY
        filtered.sort(key=lambda x: x.get("apy", 0), reverse=True)
        top = filtered[:limit]

        results = []
        for p in top:
            risk = self._score_risk(p)
            results.append({
                "pool": p.get("pool"),
                "project": p.get("project"),
                "chain": p.get("chain"),
                "symbol": p.get("symbol"),
                "apy": round(p.get("apy", 0), 2),
                "apy_base": round(p.get("apyBase", 0) or 0, 2),
                "apy_reward": round(p.get("apyReward", 0) or 0, 2),
                "tvl_usd": round(p.get("tvlUsd", 0), 0),
                "risk": risk,
                "stable": p.get("stablecoin", False),
                "il_risk": p.get("ilRisk", "unknown"),
                "exposure": p.get("exposure", "unknown"),
            })

        return {
            "service": "yield-scan",
            "timestamp": now.isoformat(),
            "filters": {"chain": chain, "min_tvl": min_tvl},
            "count": len(results),
            "opportunities": results,
        }

    async def analyze_risk(
        self,
        protocol: str,
        chain: Optional[str] = None,
    ) -> dict:
        """Deep risk analysis of a specific protocol."""
        pools = await self._fetch_pools()
        protocols = await self._fetch_protocols()

        # Find matching pools
        matching = [
            p for p in pools
            if protocol.lower() in p.get("project", "").lower()
            and (not chain or p.get("chain", "").lower() == chain.lower())
        ]

        if not matching:
            return {"service": "risk-analysis", "error": f"No pools found for '{protocol}'"}

        # Find protocol TVL data
        proto_info = next(
            (p for p in protocols if protocol.lower() in p.get("name", "").lower()),
            None,
        )

        total_tvl = sum(p.get("tvlUsd", 0) for p in matching)
        avg_apy = sum(p.get("apy", 0) for p in matching) / len(matching) if matching else 0

        risks = [self._score_risk(p) for p in matching]
        avg_risk = sum(r["score"] for r in risks) / len(risks) if risks else 50

        return {
            "service": "risk-analysis",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "protocol": protocol,
            "total_tvl_usd": round(total_tvl, 0),
            "pool_count": len(matching),
            "average_apy": round(avg_apy, 2),
            "average_risk_score": round(avg_risk, 1),
            "risk_label": "🟢 LOW" if avg_risk < 30 else ("🟡 MEDIUM" if avg_risk < 60 else "🔴 HIGH"),
            "protocol_info": {
                "category": proto_info.get("category") if proto_info else "unknown",
                "chains": proto_info.get("chains", []) if proto_info else [],
                "audits": proto_info.get("audits", "unknown") if proto_info else "unknown",
                "listed_date": proto_info.get("listedAt") if proto_info else None,
            },
            "pools": [{
                "chain": p.get("chain"),
                "symbol": p.get("symbol"),
                "apy": round(p.get("apy", 0), 2),
                "tvl_usd": round(p.get("tvlUsd", 0), 0),
                "risk": self._score_risk(p),
            } for p in matching[:15]],
        }

    async def find_new_pools(
        self,
        max_age_days: int = 7,
        chain: Optional[str] = None,
    ) -> dict:
        """Find newly launched pools."""
        pools = await self._fetch_pools()
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)

        new_pools = []
        for p in pools:
            raw_meta = p.get("poolMeta")
            meta = raw_meta if isinstance(raw_meta, dict) else {}
            created = p.get("created_at") or meta.get("createdAt")
            if not created:
                continue
            try:
                if isinstance(created, str):
                    created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                else:
                    continue
                if created_dt < cutoff:
                    continue
            except (ValueError, TypeError):
                continue
            if chain and p.get("chain", "").lower() != chain.lower():
                continue
            if p.get("tvlUsd", 0) < 10_000:
                continue

            new_pools.append({
                "pool": p.get("pool"),
                "project": p.get("project"),
                "chain": p.get("chain"),
                "symbol": p.get("symbol"),
                "apy": round(p.get("apy", 0), 2),
                "tvl_usd": round(p.get("tvlUsd", 0), 0),
                "created_at": str(created),
                "risk": self._score_risk(p),
            })

        new_pools.sort(key=lambda x: x.get("apy", 0), reverse=True)

        return {
            "service": "new-pools",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "max_age_days": max_age_days,
            "count": len(new_pools),
            "pools": new_pools[:30],
        }

    async def trending_protocols(
        self,
        chain: Optional[str] = None,
        limit: int = 10,
    ) -> dict:
        """Identify trending protocols by TVL momentum."""
        protocols = await self._fetch_protocols()

        trending = []
        for p in protocols:
            if chain and chain not in p.get("chains", []):
                continue

            tvl = p.get("tvl") or 0
            change_1d = p.get("change_1d") or 0
            change_7d = p.get("change_7d") or 0

            if tvl < 1_000_000:
                continue

            # Momentum score: weighted 1d + 7d change
            momentum = change_1d * 0.6 + change_7d * 0.4

            trending.append({
                "name": p.get("name"),
                "category": p.get("category"),
                "chains": p.get("chains", []),
                "tvl_usd": round(tvl, 0),
                "change_1d": round(change_1d, 2),
                "change_7d": round(change_7d, 2),
                "momentum_score": round(momentum, 2),
            })

        trending.sort(key=lambda x: x["momentum_score"], reverse=True)

        return {
            "service": "trending",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": len(trending[:limit]),
            "protocols": trending[:limit],
        }

    async def full_report(
        self,
        chain: Optional[str] = None,
    ) -> dict:
        """Comprehensive DeFi intelligence report."""
        yields, trending, new = await asyncio.gather(
            self.scan_yields(chain=chain, limit=10),
            self.trending_protocols(chain=chain, limit=5),
            self.find_new_pools(chain=chain),
        )

        return {
            "service": "full-report",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "chain_filter": chain,
            "top_yields": yields.get("opportunities", []),
            "trending_protocols": trending.get("protocols", []),
            "new_pools": new.get("pools", [])[:10],
            "summary": {
                "total_opportunities": yields.get("count", 0),
                "new_pools_found": new.get("count", 0),
                "hottest_protocol": trending.get("protocols", [{}])[0].get("name", "N/A") if trending.get("protocols") else "N/A",
            },
        }
