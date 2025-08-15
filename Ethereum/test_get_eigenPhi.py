import requests
import pandas as pd

# Define GraphQL query
query = """
query ArbitrageTxList($chain: String!, $page: Int!, $pageSize: Int!) {
  arbitrageTxList(chain: $chain, page: $page, pageSize: $pageSize) {
    list {
      txHash
      profitTokenSymbol
      profitAmount
      dexList
      tokenInSymbol
      tokenOutSymbol
    }
  }
}
"""

# Variables
variables = {
    "chain": "ethereum",  # or bsc, arbitrum, etc.
    "page": 1,
    "pageSize": 50
}

# Headers (mimic browser)
headers = {
    "Content-Type": "application/json",
    "Origin": "https://eigenphi.io",
    "Referer": "https://eigenphi.io/",
    "User-Agent": "Mozilla/5.0"
}

# Endpoint (unofficial)
url = "https://api.eigenphi.io/ar/api/arbitrage/graphql"

# Send request
response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)

# Parse response
resp_json = response.json()
print("Full response:", resp_json)  # Debug: print the full response

if 'data' in resp_json and 'arbitrageTxList' in resp_json['data']:
    data = resp_json['data']['arbitrageTxList']['list']
    df = pd.DataFrame(data)

    # Count most used DEXs
    from collections import Counter
    dex_counter = Counter()

    for row in df['dexList']:
        if row:
            for dex in row:
                dex_counter[dex] += 1

    # Display top arbitraged DEXs
    top_dexs = dex_counter.most_common()
    for dex, count in top_dexs:
        print(f"{dex}: {count} times involved in arbitrage")
else:
    print("Error in response:")
    print(resp_json)
