import heapq
import json
from pathlib import Path
import time
from typing import Dict, List, Optional, Tuple, Union


def load_dataset(path: Union[str, Path]) -> dict:
    """Load a JSON dataset containing depot, bag_capacity, parcels, and graph."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sort_parcels(parcels: List[dict], by: str = "ratio", descending: bool = True) -> List[dict]:
    """Sort parcels by 'ratio' (value/weight), 'value', or 'weight' with tie-breaking."""
    key_funcs = {
        "ratio": lambda p: (p["value"] / p["weight"]) if p["weight"] > 0 else 0.0,
        "value": lambda p: p["value"],
        "weight": lambda p: p["weight"],
    }
    if by not in key_funcs:
        raise ValueError(f"Unsupported sort key: {by}")

    return sorted(
        parcels,
        key=lambda p: (key_funcs[by](p), p["id"]),
        reverse=descending,
    )


def solve_knapsack_dp(parcels: List[dict], capacity: int) -> dict:
    """Solve 0/1 Knapsack via bottom-up DP and backtrack for selected parcels."""
    n = len(parcels)
    if capacity <= 0 or n == 0:
        return {
            "max_value": 0,
            "total_weight": 0,
            "selected_parcels": [],
            "dp_table": [],
        }

    # dp[i][w] = max value using first i parcels with capacity w
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        wt = parcels[i - 1]["weight"]
        val = parcels[i - 1]["value"]
        for w in range(capacity + 1):
            dp[i][w] = dp[i - 1][w]
            if wt <= w:
                candidate = dp[i - 1][w - wt] + val
                if candidate > dp[i][w]:
                    dp[i][w] = candidate

    # Backtrack from bottom-right to recover exact packed items
    selected = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            item = parcels[i - 1]
            selected.append(item)
            w -= item["weight"]

    selected.reverse()
    total_weight = sum(p["weight"] for p in selected)

    return {
        "max_value": dp[n][capacity],
        "total_weight": total_weight,
        "selected_parcels": selected,
        "dp_table": dp,
    }


def dijkstra_shortest_paths(
    graph: Dict[str, List[dict]], source: str
) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """Compute shortest distances and parent pointers from source using a min-heap."""
    distances: Dict[str, float] = {node: float("inf") for node in graph}
    parent: Dict[str, Optional[str]] = {node: None for node in graph}

    if source not in graph:
        return distances, parent

    distances[source] = 0.0
    pq: List[Tuple[float, str]] = [(0.0, source)]

    while pq:
        curr_dist, u = heapq.heappop(pq)
        if curr_dist > distances[u]:
            continue

        for edge in graph.get(u, []):
            v = edge["to"]
            cost = edge["cost"]
            if v not in distances:
                continue
            new_dist = curr_dist + cost
            if new_dist < distances[v]:
                distances[v] = new_dist
                parent[v] = u
                heapq.heappush(pq, (new_dist, v))

    return distances, parent


def reconstruct_path(parent: Dict[str, Optional[str]], source: str, target: str) -> List[str]:
    """Reconstruct node-by-node shortest path from source to target."""
    if source == target:
        return [source]
    path: List[str] = []
    curr: Optional[str] = target
    while curr is not None:
        path.append(curr)
        if curr == source:
            break
        curr = parent.get(curr)
    if not path or path[-1] != source:
        return []
    path.reverse()
    return path


def nearest_neighbor_tsp(
    graph: Dict[str, List[dict]],
    depot: str,
    targets: List[str],
    return_to_depot: bool = True,
) -> dict:
    """Order target stops greedily by shortest-path distance (Nearest-Neighbor TSP heuristic)."""
    unvisited = set(targets)
    unvisited.discard(depot)

    current = depot
    stop_order = [depot]
    legs = []
    total_cost = 0.0

    while unvisited:
        distances, parent = dijkstra_shortest_paths(graph, current)
        reachable = [
            (distances[stop], stop, parent)
            for stop in unvisited
            if stop in distances and distances[stop] < float("inf")
        ]
        if not reachable:
            break

        # Pick nearest stop (tie-break alphabetically by stop name for determinism)
        reachable.sort(key=lambda item: (item[0], item[1]))
        leg_cost, next_stop, parent = reachable[0]
        path = reconstruct_path(parent, current, next_stop)

        legs.append({
            "from": current,
            "to": next_stop,
            "cost": leg_cost,
            "path": path,
        })
        total_cost += leg_cost
        stop_order.append(next_stop)
        unvisited.remove(next_stop)
        current = next_stop

    if return_to_depot and current != depot:
        distances, parent = dijkstra_shortest_paths(graph, current)
        if depot in distances and distances[depot] < float("inf"):
            leg_cost = distances[depot]
            path = reconstruct_path(parent, current, depot)
            legs.append({
                "from": current,
                "to": depot,
                "cost": leg_cost,
                "path": path,
            })
            total_cost += leg_cost
            stop_order.append(depot)

    return {
        "stop_order": stop_order,
        "legs": legs,
        "total_cost": total_cost,
        "unvisited_targets": sorted(unvisited),
    }


def plan_delivery(dataset: dict, sort_by: str = "ratio", return_to_depot: bool = True) -> dict:
    """Run full Mini-Courier Planner pipeline on a dataset and measure runtime."""
    t0 = time.perf_counter()

    ranked_parcels = sort_parcels(dataset["parcels"], by=sort_by, descending=True)
    packing = solve_knapsack_dp(ranked_parcels, dataset["bag_capacity"])

    target_stops = sorted({p["destination"] for p in packing["selected_parcels"]})
    route = nearest_neighbor_tsp(
        graph=dataset["graph"],
        depot=dataset["depot"],
        targets=target_stops,
        return_to_depot=return_to_depot,
    )

    elapsed_ms = (time.perf_counter() - t0) * 1000
    return {
        "ranked_parcels": ranked_parcels,
        "packing": packing,
        "route": route,
        "runtime_ms": elapsed_ms,
    }


if __name__ == "__main__":
    sample_path = Path("data/small.json")
    if not sample_path.exists():
        raise FileNotFoundError("Run make_data.py first to generate data/small.json")

    data = load_dataset(sample_path)
    result = plan_delivery(data, sort_by="ratio", return_to_depot=True)

    print(f"Depot: {data['depot']} | Bag Capacity: {data['bag_capacity']}")
    print("\n--- Step 1: Ranked Parcels (by value/weight) ---")
    for p in result["ranked_parcels"]:
        ratio = (p["value"] / p["weight"]) if p["weight"] > 0 else 0.0
        print(f"  {p['id']} -> dest={p['destination']}, w={p['weight']}, v={p['value']}, ratio={ratio:.2f}")

    packing = result["packing"]
    print("\n--- Step 2: 0/1 Knapsack Selection ---")
    for p in packing["selected_parcels"]:
        print(f"  {p['id']} -> dest={p['destination']}, w={p['weight']}, v={p['value']}")
    print(f"Packed Weight: {packing['total_weight']}/{data['bag_capacity']} | Max Value: {packing['max_value']}")

    route = result["route"]
    print("\n--- Step 3: Delivery Route (Dijkstra + Nearest-Neighbor TSP) ---")
    print("  Stop Sequence:", " -> ".join(route["stop_order"]))
    for leg in route["legs"]:
        print(f"  Leg {leg['from']} => {leg['to']} (cost={leg['cost']}): {' -> '.join(leg['path'])}")
    print(f"Total Route Cost: {route['total_cost']}")
    print(f"\nTotal Pipeline Runtime: {result['runtime_ms']:.3f} ms")