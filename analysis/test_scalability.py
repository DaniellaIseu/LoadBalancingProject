import asyncio
import aiohttp
import requests
import matplotlib.pyplot as plt
import time
import os
import json
from collections import defaultdict

BASE_URL = "http://localhost:5050"
NUM_REQUESTS = 10000
RESULT_DIR = "analysis/results"
RAW_DIR = os.path.join(RESULT_DIR, "raw_logs")

# Create directories if they don't exist
os.makedirs(RAW_DIR, exist_ok=True)

# Store average load per server for line chart
avg_load_per_n = []

def wait_for_replicas(expected_n, timeout=20):
    print(f"[WAIT] Waiting for {expected_n} replicas to be alive...")
    for _ in range(timeout):
        try:
            r = requests.get(f"{BASE_URL}/rep")
            data = r.json()["message"]
            replicas = data["replicas"]
            if len(replicas) == expected_n:
                print(f"[OK] {expected_n} replicas ready: {replicas}")
                return True
            else:
                print(f"[WAIT] Found {len(replicas)} replicas: {replicas}, retrying...")
        except Exception as e:
            print(f"[ERROR] /rep failed: {e}, retrying...")
        time.sleep(1)
    print("[FAIL] Timeout waiting for replicas.")
    return False

def reset_to_n3():
    print("\n[RESET] Resetting to Server1, Server2, Server3 only...")
    try:
        requests.delete(f"{BASE_URL}/rm", json={"n": 100, "hostnames": []})
        requests.post(f"{BASE_URL}/add", json={
            "n": 3,
            "hostnames": ["Server1", "Server2", "Server3"]
        })
    except Exception as e:
        print(f"[WARN] Reset failed: {e}")

def scale_to_n(n):
    print(f"\n[SCALE] Scaling to N={n} servers...")
    if n > 3:
        extra = n - 3
        dynamic_names = [f"dyn{i+1}" for i in range(extra)]
        try:
            requests.post(f"{BASE_URL}/add", json={"n": extra, "hostnames": dynamic_names})
        except Exception as e:
            print(f"[WARN] POST failed to /add, retrying... {e}")
    elif n < 3:
        try:
            requests.delete(f"{BASE_URL}/rm", json={"n": 3 - n, "hostnames": []})
        except Exception as e:
            print(f"[WARN] DELETE failed to /rm: {e}")

async def send_request(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data["message"].split(":")[-1].strip()
    except:
        return "<Error> Request failed"
    return "<Error> Unknown"

async def run_requests():
    print(f"[RUN] Sending {NUM_REQUESTS} requests...")
    async with aiohttp.ClientSession() as session:
        tasks = [send_request(session, f"{BASE_URL}/home") for _ in range(NUM_REQUESTS)]
        return await asyncio.gather(*tasks)

def plot_distribution(server_counts, n):
    servers = list(server_counts.keys())
    counts = [server_counts[s] for s in servers]
    total = sum(counts)

    plt.figure(figsize=(8, 5))
    plt.bar(servers, counts, color="teal")
    plt.title(f"Load Distribution (N={n}) - {total} Requests")
    plt.xlabel("Server")
    plt.ylabel("Requests Handled")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    img_path = os.path.join(RESULT_DIR, f"load_distribution_N{n}.png")
    plt.savefig(img_path)
    print(f"[PLOT] Saved: {img_path}")

def plot_scalability_line_chart():
    if not avg_load_per_n:
        return

    ns = [item[0] for item in avg_load_per_n]
    avgs = [item[1] for item in avg_load_per_n]

    plt.figure(figsize=(8, 5))
    plt.plot(ns, avgs, marker='o', linestyle='-', color='blue')
    plt.title("Scalability Test: Avg Load vs Number of Servers")
    plt.xlabel("Number of Servers (N)")
    plt.ylabel("Average Load per Server")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()

    out_path = os.path.join(RESULT_DIR, "scalability_line_chart.png")
    plt.savefig(out_path)
    print(f"[LINE PLOT] Saved line chart to: {out_path}")

def save_raw_log(server_counts, n):
    path = os.path.join(RAW_DIR, f"raw_N{n}.json")
    with open(path, "w") as f:
        json.dump(server_counts, f, indent=2)
    print(f"[LOG] Saved raw data: {path}")

async def test_scalability():
    for n in [4, 6]:  # Test N = 4 and N = 6
        reset_to_n3()
        scale_to_n(n)

        if not wait_for_replicas(n):
            continue

        responses = await run_requests()
        counter = defaultdict(int)
        for resp in responses:
            counter[resp] += 1

        total = sum(counter.values())
        print("\n=== Distribution Summary ===")
        for k, v in sorted(counter.items(), key=lambda x: -x[1]):
            perc = (v / total) * 100
            print(f"{k}: {v} requests ({perc:.2f}%)")

        avg = total / len(counter)
        avg_load_per_n.append((n, avg))

        plot_distribution(counter, n)
        save_raw_log(counter, n)

    # After all N values tested
    plot_scalability_line_chart()

if __name__ == "__main__":
    asyncio.run(test_scalability())