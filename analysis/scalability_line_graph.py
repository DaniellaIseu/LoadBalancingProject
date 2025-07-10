import os
import json
import matplotlib.pyplot as plt

RAW_LOG_DIR = "analysis/results/raw_logs"
OUTPUT_PLOT = "analysis/results/scalability_line_chart.png"

def load_data():
    """Load all raw_N*.json files and extract total request counts."""
    data = {}

    for filename in sorted(os.listdir(RAW_LOG_DIR)):
        if filename.startswith("raw_N") and filename.endswith(".json"):
            path = os.path.join(RAW_LOG_DIR, filename)
            with open(path, "r") as f:
                counts = json.load(f)
            
            n = int(filename.split("_N")[1].split(".")[0])
            total_requests = sum(counts.values())
            data[n] = total_requests

    return data

def plot_line_graph(data):
    """Plot scalability line chart from request totals."""
    ns = sorted(data.keys())
    totals = [data[n] for n in ns]

    plt.figure(figsize=(8, 5))
    plt.plot(ns, totals, marker="o", linestyle="-", color="royalblue")
    plt.title("Load Balancer Scalability\nTotal Requests Successfully Routed")
    plt.xlabel("Number of Servers (N)")
    plt.ylabel("Total Successful Requests")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.xticks(ns)
    plt.tight_layout()

    os.makedirs(os.path.dirname(OUTPUT_PLOT), exist_ok=True)
    plt.savefig(OUTPUT_PLOT)
    print(f"[LINE PLOT] Saved line chart to: {OUTPUT_PLOT}")

if __name__ == "__main__":
    data = load_data()
    if data:
        plot_line_graph(data)
    else:
        print("[WARN] No raw_N*.json files found in raw_logs/")
