import json
from pathlib import Path
import random


def generate_instance(num_parcels: int, num_nodes: int, seed: int = 42) -> dict:
    rng = random.Random(seed)
    nodes = ["HUB"] + [f"D{i}" for i in range(1, num_nodes)]
    adj = {node: [] for node in nodes}

    # Connect all nodes first so shortest paths exist
    for i in range(1, num_nodes):
        u = nodes[rng.randrange(0, i)]
        v = nodes[i]
        dist = rng.randint(2, 15)
        adj[u].append({"to": v, "cost": dist})
        adj[v].append({"to": u, "cost": dist})

    # Add extra roads for richer shortest-path choices
    extra_edges = num_nodes * 2
    for _ in range(extra_edges):
        u, v = rng.sample(nodes, 2)
        if not any(edge["to"] == v for edge in adj[u]):
            dist = rng.randint(2, 20)
            adj[u].append({"to": v, "cost": dist})
            adj[v].append({"to": u, "cost": dist})

    destinations = nodes[1:] if len(nodes) > 1 else nodes
    parcels = []
    for idx in range(num_parcels):
        weight = rng.randint(1, 10)
        value = rng.randint(15, 100)
        parcels.append({
            "id": f"P{idx + 1:02d}",
            "weight": weight,
            "value": value,
            "destination": rng.choice(destinations),
        })

    total_weight = sum(p["weight"] for p in parcels)
    bag_capacity = max(8, int(total_weight * 0.5))

    return {
        "depot": "HUB",
        "bag_capacity": bag_capacity,
        "parcels": parcels,
        "graph": adj,
    }


def main() -> None:
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    datasets = {
        "small.json": generate_instance(num_parcels=6, num_nodes=5, seed=101),
        "medium.json": generate_instance(num_parcels=20, num_nodes=12, seed=202),
        "large.json": generate_instance(num_parcels=50, num_nodes=25, seed=303),
    }

    for filename, payload in datasets.items():
        out_path = data_dir / filename
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {out_path} ({len(payload['parcels'])} parcels, {len(payload['graph'])} stops)")


if __name__ == "__main__":
    main()