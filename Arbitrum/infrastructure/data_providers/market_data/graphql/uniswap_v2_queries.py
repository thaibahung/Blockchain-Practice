"""
GraphQL queries for Uniswap V2 using TheGraph API.
"""

GET_TOP_PAIRS = """
query GetTopPairs($first: Int!, $minLiquidityUSD: BigDecimal!, $lastTransactionTimestamp: BigInt!) {
  pairs(
    first: $first,
    orderBy: volumeUSD,
    orderDirection: desc,
    where: { 
      reserveUSD_gt: $minLiquidityUSD, 
      token0_: {derivedETH_gt: "0"}, 
      token1_: {derivedETH_gt: "0"}, 
      swaps_: {timestamp_gt:  $lastTransactionTimestamp} 
    }
  ) {
    id
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
    txCount
    createdAtTimestamp
  }
  _meta {
    block {
      number
    }
  }
}
"""