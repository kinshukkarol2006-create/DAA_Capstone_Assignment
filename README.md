# Mini-Courier Planner (ETCCDA302 Capstone)

**Name : Kinshuk karol**
**Roll Number: 2501730171**
**Submitted to: Dr Shweta Agarwal**
    

A Python prototype for the **Mini-Courier Planner** capstone assignment that ranks parcels, optimizes bag selection using Dynamic Programming, computes shortest paths with Dijkstra's algorithm, and orders delivery stops using a Nearest-Neighbor TSP heuristic.

## Project Structure

- `make_data.py` — Generates sample (`data/small.json`, `data/medium.json`, `data/large.json`) and scalable datasets.
- `courier_planner.py` — Core logic for parcel sorting, 0/1 Knapsack DP + backtracking, Dijkstra's shortest paths, and Nearest-Neighbor TSP routing.
- `test_courier.py` — Unit tests covering sorting, DP optimality/backtracking, edge cases, Dijkstra (including unreachable nodes), and routing.
- `diagram.py` — Benchmarks runtime across input sizes and generates outputs in `output/`.
- `run_all.py` — End-to-end runner executing data setup, planning, unit tests, and benchmarking.

## How to Run

```bash
python3 make_data.py
python3 courier_planner.py
python3 -m unittest test_courier.py -v
python3 diagram.py
python3 run_all.py