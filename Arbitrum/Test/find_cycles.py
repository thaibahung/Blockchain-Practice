import pandas as pd
import itertools

# === CONFIG ===
csv_path = "pools_sepolia_v2.csv"  # path to your CSV file
# ===============

# Load CSV
df = pd.read_csv(csv_path)

# Normalize column names for consistency
df.columns = [c.lower() for c in df.columns]

# Ensure token columns exist
if "token0" not in df.columns or "token1" not in df.columns:
    raise ValueError("CSV must contain 'token0' and 'token1' columns.")

# Extract edges (pairwise token connections)
edges = list(zip(df["token0"], df["token1"]))

# Build adjacency list (graph)
graph = {}
for a, b in edges:
    graph.setdefault(a, set()).add(b)
    graph.setdefault(b, set()).add(a)

# Find all 3-token cycles (A-B-C-A)
triangles = set()
tokens = list(graph.keys())

for a in tokens:
    for b, c in itertools.combinations(graph[a], 2):
        if b in graph and c in graph[b] and a in graph[c]:
            triangles.add(tuple(sorted([a, b, c])))

# Convert to list for viewing
triangles = list(triangles)

print(f"✅ Found {len(triangles)} unique 3-token cycles.\n")

if len(triangles) > 0:
    print("Sample cycles:")
    for t in triangles[:10]:
        print(" - ", " → ".join(t))
else:
    print("No 3-token cycles detected.")

# Optionally export results
if triangles:
    pd.DataFrame(triangles, columns=["TokenA", "TokenB", "TokenC"]).to_csv("triangular_cycles.csv", index=False)
    print("\n📁 Saved cycles to triangular_cycles.csv")
