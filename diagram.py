import json
from pathlib import Path
import time

from courier_planner import (
    dijkstra_shortest_paths,
    load_dataset,
    nearest_neighbor_tsp,
    solve_knapsack_dp,
    sort_parcels,
)
from make_data import generate_instance


def benchmark_dataset(name: str, dataset: dict, repeats: int = 5) -> dict:
    """Measure per-stage and total execution times across repeated runs."""
    parcels = dataset["parcels"]
    capacity = dataset["bag_capacity"]
    graph = dataset["graph"]
    depot = dataset["depot"]

    sort_times_ms = []
    dp_times_ms = []
    route_times_ms = []
    total_times_ms = []

    last_summary = {}

    for _ in range(repeats):
        t_start = time.perf_counter()

        t0 = time.perf_counter()
        ranked = sort_parcels(parcels, by="ratio", descending=True)
        sort_times_ms.append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        packing = solve_knapsack_dp(ranked, capacity)
        dp_times_ms.append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        targets = sorted({p["destination"] for p in packing["selected_parcels"]})
        if targets:
            dijkstra_shortest_paths(graph, depot)
        route = nearest_neighbor_tsp(graph, depot, targets, return_to_depot=True)
        route_times_ms.append((time.perf_counter() - t0) * 1000)

        total_times_ms.append((time.perf_counter() - t_start) * 1000)

        last_summary = {
            "num_parcels": len(parcels),
            "num_nodes": len(graph),
            "bag_capacity": capacity,
            "packed_weight": packing["total_weight"],
            "max_value": packing["max_value"],
            "route_cost": route["total_cost"],
        }

    avg_total = sum(total_times_ms) / repeats
    return {
        "dataset": name,
        "repeats": repeats,
        "avg_sort_ms": sum(sort_times_ms) / repeats,
        "avg_dp_ms": sum(dp_times_ms) / repeats,
        "avg_route_ms": sum(route_times_ms) / repeats,
        "avg_total_ms": avg_total,
        **last_summary,
    }


def render_bar(value_ms: float, max_ms: float, width: int = 24) -> str:
    if max_ms <= 0:
        return ""
    filled = max(1, int(round((value_ms / max_ms) * width)))
    return "#" * filled


def main() -> None:
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)

    instances = []
    for fname in ["small.json", "medium.json", "large.json"]:
        p = Path("data") / fname
        if p.exists():
            instances.append((fname.replace(".json", ""), load_dataset(p)))

    # Add an extra larger size to observe scaling clearly
    instances.append(("xlarge (100p, 40n)", generate_instance(num_parcels=100, num_nodes=40, seed=404)))

    results = [benchmark_dataset(name, ds, repeats=5) for name, ds in instances]
    max_total = max(r["avg_total_ms"] for r in results)

    pipeline_text = """\
MINI-COURIER PLANNER PIPELINE
==============================
[Input Dataset: parcels, bag_capacity, depot, graph]
       |
       v
1. Sorting (O(n log n)) ---------> Rank parcels by value/weight, value, or weight
       |
       v
2. 0/1 Knapsack DP (O(n * W)) ---> Optimal bag selection + DP table backtracking
       |
       v
3. Dijkstra + NN TSP ------------> Shortest paths + greedy delivery stop ordering
       |
       v
[Output: Selected Parcels, Ordered Route, Total Cost, Runtime Metrics]
"""
    (out_dir / "pipeline_diagram.txt").write_text(pipeline_text, encoding="utf-8")

    lines = [
        "# Mini-Courier Planner Runtime Benchmark",
        "",
        "| Dataset | Parcels | Stops | Bag Cap | Max Value | Route Cost | Sort (ms) | 0/1 DP (ms) | Routing (ms) | Avg Total (ms) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        lines.append(
            f"| {r['dataset']} | {r['num_parcels']} | {r['num_nodes']} | {r['bag_capacity']} | "
            f"{r['max_value']} | {r['route_cost']:.1f} | {r['avg_sort_ms']:.4f} | "
            f"{r['avg_dp_ms']:.4f} | {r['avg_route_ms']:.4f} | {r['avg_total_ms']:.4f} |"
        )

    lines.extend(["", "## Total Runtime Visual Comparison", "```text"])
    for r in results:
        bar = render_bar(r["avg_total_ms"], max_total)
        lines.append(f"{r['dataset']:20s} | {bar} {r['avg_total_ms']:.4f} ms")
    lines.append("```")

    report_md = "\n".join(lines) + "\n"
    (out_dir / "benchmark_report.md").write_text(report_md, encoding="utf-8")
    (out_dir / "benchmark_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(pipeline_text)
    print(report_md)


if __name__ == "__main__":
    main()