import asyncio
import aiohttp
import requests
import time
import os
import json
import matplotlib.pyplot as plt
from collections import defaultdict

BASE_URL = "http://localhost:5050"
NUM_REQUESTS = 3000
FAIL_AT = 1500  # Kill a server after this many requests
SERVER_TO_KILL = "Server2"
RESULTS_DIR = "analysis/results"
RAW_LOG = os.path.join(RESULTS_DIR, "raw_logs", "failure_recovery.log")
PLOT_FILE = os.path.join(RESULTS_DIR, "failure_recovery.png")

os.makedirs(os.path.dirname(RAW_LOG), exist_ok=True)

async def send_request(session, i):
    try:
        async with session.get(f"{BASE_URL}/home", timeout=3) as resp:
            if resp.status == 200:
                data = await resp.json()
                server = data.get("message", "<no-response>").split(":")[-1].strip()
                return {"index": i, "status": "success", "server": server}
    except:
        return {"index": i, "status": "fail", "server": None}
    return {"index": i, "status": "fail", "server": None}

def kill_server(server_name):
    print(f"[FAILURE] Simulating crash of {server_name}...")
    try:
        response = requests.delete(f"{BASE_URL}/rm", json={"n": 1, "hostnames": [server_name]})
        if response.status_code == 200:
            print(f"[OK] {server_name} removed.")
        else:
            print(f"[WARN] Failed to remove {server_name}")
    except Exception as e:
        print(f"[ERROR] Could not contact load balancer: {e}")

async def run_test():
    print("[TEST] Starting failure recovery test...")
    results = []
    async with aiohttp.ClientSession() as session:
        for i in range(NUM_REQUESTS):
            if i == FAIL_AT:
                kill_server(SERVER_TO_KILL)
                time.sleep(2)  # Give time for removal to settle

            result = await send_request(session, i)
            results.append(result)

            # Optionally sleep slightly for more observable behavior
            # await asyncio.sleep(0.001)

    return results

def analyze_and_plot(results):
    # Save raw logs
    with open(RAW_LOG, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"[LOG] Saved to {RAW_LOG}")

    # Count total requests per server
    counts = defaultdict(int)
    for r in results:
        if r['status'] == 'success' and r['server']:
            counts[r['server']] += 1

    # Prepare data
    servers = sorted(counts.keys())  # For consistent order
    loads = [counts[s] for s in servers]

    # Plot as a line chart
    plt.figure(figsize=(10, 5))
    plt.plot(servers, loads, marker='o', linestyle='-', color='blue')
    plt.title("Final Load Distribution After Server Failure")
    plt.xlabel("Server")
    plt.ylabel("Total Requests Handled")
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig(PLOT_FILE)
    print(f"[PLOT] Saved to {PLOT_FILE}")

if __name__ == "__main__":
    results = asyncio.run(run_test())
    analyze_and_plot(results)
