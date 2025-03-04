import requests
import csv

# Define the Uniswap V2 Subgraph API endpoint
url = "https://gateway.thegraph.com/api/0cf89bd9a28f215c30b82bf66f2df0f2/subgraphs/id/EYCKATKGBKLWvSfwvBjzfCBmGwYNdVkduYXVivCsLRFu"

# GraphQL query to fetch top 3 pools
query = """
{
  pairs(first: 200, orderBy: volumeUSD, orderDirection: desc) {
    id
    token0 {
      id
      symbol
    }
    token1 {
      id
      symbol
    }
  }  
}
"""

# Send request to The Graph
response = requests.post(url, json={'query': query})

# Check if response is successful
if response.status_code == 200:
    data = response.json()
    
    # Extract relevant data
    extracted_data = [
        {
            "pair_id": pair["id"],
            "token0_symbol": pair["token0"]["symbol"],
            "token0_id": pair["token0"]["id"],
            "token1_symbol": pair["token1"]["symbol"],
            "token1_id": pair["token1"]["id"],
        }
        for pair in data.get("data", {}).get("pairs", [])
    ]

print(extracted_data)

    