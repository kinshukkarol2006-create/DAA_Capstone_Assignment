from pathlib import Path
import subprocess
import sys

from courier_planner import load_dataset, plan_delivery
import make_data


def run_step(title: str, cmd: list[str]) -> None:
    print(f"\n=== {title} ===")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Step failed ({title}) with exit code {result.returncode}")


def main() -> None:
    data_dir = Path("data")
    if not (data_dir / "small.json").exists():
        print("=== Generating Datasets ===")
        make_data.main()

    for fname in ["small.json", "medium.json", "large.json"]:
        path = data_dir / fname
        if path.exists():
            ds = load_dataset(path)
            res = plan_delivery(ds, sort_by="ratio", return_to_depot=True)
            packing = res["packing"]
            route = res["route"]
            print(
                f"[{fname}] parcels={len(ds['parcels'])}, cap={ds['bag_capacity']} | "
                f"packed_wt={packing['total_weight']}, max_val={packing['max_value']} | "
                f"route_cost={route['total_cost']:.1f}, stops={len(route['stop_order'])} | "
                f"time={res['runtime_ms']:.3f} ms"
            )

    run_step("Running Unit Tests", [sys.executable, "-m", "unittest", "test_courier.py", "-v"])
    run_step("Generating Benchmarks & Diagrams", [sys.executable, "diagram.py"])
    print("\nAll capstone steps completed successfully.")


if __name__ == "__main__":
    main()