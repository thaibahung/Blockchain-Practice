import asyncio
from datetime import datetime, timedelta, timezone
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

# ─── CONFIG ──────────────────────────────────────────────────────────────────────

# Replace this with whatever V2 subgraph endpoint you’re targeting
GRAPH_URL = "https://gateway.thegraph.com/api/53b8386571487df55de93e545a902af7/subgraphs/id/3AMhp8Ck6ZScMibA8jfLhWFA9fKH6Zi8fMPHtb74Vsxv"

# How many top pools to print
TOP_N = 100

# Minimum USD liquidity to consider (set to 0 to ignore)
MIN_LIQUIDITY_USD = 0

# ─── GRAPHQL QUERY ──────────────────────────────────────────────────────────────

GET_PAIRS_WITH_HOUR_DATA = """
query GetPairsWithHourData($first: Int!, $minLiquidityUSD: BigDecimal!, $threeMonthsAgo: Int!) {
  pairs(
    first: $first,
    where: { 
    token0_: {derivedETH_gt: "0"}, 
    token1_: {derivedETH_gt: "0"}, 
    reserveUSD_gt: $minLiquidityUSD 
    }
  ) {
    id
    reserveUSD
    pairHourData(
      where: { hourStartUnix_gt: $threeMonthsAgo },
      orderBy: hourStartUnix,
      orderDirection: asc
    ) {
      hourStartUnix
      hourlyTxns
    }
    token0 {
      id
      symbol
      decimals
      derivedETH
    }
    token1 {
      id
      symbol
      decimals
      derivedETH
    }
    token0Price
    token1Price
    reserve0
    reserve1
    reserveUSD
    volumeUSD
  }
  _meta {
    block {
      number
    }
  }
}
"""

# ─── FETCH & PROCESS ────────────────────────────────────────────────────────────

async def main():
    # Calculate timestamp for “3 months ago” (≈90 days)
    three_months_ago_ts = int((datetime.now(timezone.utc) - timedelta(days=90)).timestamp())

    transport = AIOHTTPTransport(url=GRAPH_URL, timeout=120, ssl=True)
    client = Client(transport=transport, fetch_schema_from_transport=True, execute_timeout=120)

    variables = {
        "first": 1000,                    # fetch up to 1000 pools
        "minLiquidityUSD": MIN_LIQUIDITY_USD,
        "threeMonthsAgo": three_months_ago_ts
    }

    async with client as session:
        result = await session.execute(
            gql(GET_PAIRS_WITH_HOUR_DATA),
            variable_values=variables
        )

    pools = []
    for pool in result["pairs"]:
        # Sum the last-90-day dailyTxns
        txs_last_90d = sum(int(day["hourlyTxns"]) for day in pool["pairHourData"])
        pools.append({
            "id": pool["id"],
            "reserveUSD": float(pool["reserveUSD"]),
            "txs_90d": txs_last_90d
        })

    # Sort by total txs in the last 90 days, descending
    pools.sort(key=lambda x: x["txs_90d"], reverse=True)

    # Print top N
    print(f"Top {TOP_N} Uniswap V2 pools by swaps in the last 3 months:\n")
    for i, p in enumerate(pools[:TOP_N], start=1):
        print(f"{i:2d}. Pool: {p['id']}  ──  TVL: ${p['reserveUSD']:.1f}  ──  90d swaps: {p['txs_90d']}")

if __name__ == "__main__":
    asyncio.run(main())
