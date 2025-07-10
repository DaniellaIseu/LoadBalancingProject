import asyncio
import aiohttp
import random 
from collections import defaultdict
import matplotlib.pyplot as plt
import json
import os

# Set a fixed seed for reproducibility
random.seed(42)

BASE_URL = "http://localhost:5050/home"
NUM_REQUESTS = 10000
OUTPUT_DIR = "analysis/results"
OUTPUT_PLOT = os.path.join(OUTPUT_DIR, "load_distribution_N3.png")
RAW_LOG_FILE = os.path.join(OUTPUT_DIR, "dist_N3_raw.json")

async def fetch(session):
    try:
        async with session.get(BASE_URL, timeout=5) as response:
            data = await response.json()
            server = data['message'].split(':')[-1].strip()
            return server
    except Exception:
        return None

async def run_test():
    results = defaultdict(int)
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session) for _ in range(NUM_REQUESTS)]
        responses = await asyncio.gather(*tasks)

    total_success = 0
    for server in responses:
        if server:
            results[server] += 1
            total_success += 1

    print("\n=== Load Distribution Summary ===")
    for srv, count in sorted(results.items()):
        percentage = (count / total_success) * 100 if total_success else 0
        print(f"{srv}: {count} requests ({percentage:.2f}%)")

    # Save raw results
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(RAW_LOG_FILE, "w") as f:
        json.dump(results, f, indent=2)

    # Plot
    servers = list(results.keys())
    counts = [results[srv] for srv in servers]

    plt.figure(figsize=(8, 5))
    plt.bar(servers, counts, color='steelblue')
    plt.title(f"Load Distribution Across Servers (N = 3)\nTotal: {total_success} requests")
    plt.xlabel("Server")
    plt.ylabel("Number of Requests")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT)
    print(f"\nBar chart saved to: {OUTPUT_PLOT}")

if __name__ == "__main__":
    asyncio.run(run_test())