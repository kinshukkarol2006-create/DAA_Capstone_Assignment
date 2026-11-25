import unittest

from courier_planner import (
    dijkstra_shortest_paths,
    nearest_neighbor_tsp,
    reconstruct_path,
    solve_knapsack_dp,
    sort_parcels,
)


class TestCourierPlanner(unittest.TestCase):
    def setUp(self) -> None:
        self.parcels = [
            {"id": "P1", "weight": 4, "value": 40, "destination": "A"},
            {"id": "P2", "weight": 3, "value": 30, "destination": "B"},
            {"id": "P3", "weight": 5, "value": 50, "destination": "A"},
            {"id": "P4", "weight": 2, "value": 10, "destination": "C"},
        ]
        self.graph = {
            "HUB": [{"to": "A", "cost": 5}, {"to": "B", "cost": 2}],
            "A": [{"to": "HUB", "cost": 5}, {"to": "C", "cost": 4}],
            "B": [{"to": "HUB", "cost": 2}, {"to": "A", "cost": 2}, {"to": "C", "cost": 9}],
            "C": [{"to": "A", "cost": 4}, {"to": "B", "cost": 9}],
            "ISOLATED": [],
        }

    def test_sort_parcels_by_value_and_weight(self) -> None:
        by_val = sort_parcels(self.parcels, by="value", descending=True)
        self.assertEqual([p["id"] for p in by_val], ["P3", "P1", "P2", "P4"])

        by_wt = sort_parcels(self.parcels, by="weight", descending=False)
        self.assertEqual([p["id"] for p in by_wt], ["P4", "P2", "P1", "P3"])

    def test_knapsack_dp_optimal_and_capacity(self) -> None:
        res = solve_knapsack_dp(self.parcels, capacity=7)
        self.assertLessEqual(res["total_weight"], 7)
        # P2 (w=3, v=30) + P1 (w=4, v=40) = w=7, v=70 (or P2 + P3 = w=8 > 7)
        self.assertEqual(res["max_value"], 70)
        self.assertEqual(sorted(p["id"] for p in res["selected_parcels"]), ["P1", "P2"])

    def test_knapsack_zero_capacity_and_empty(self) -> None:
        zero_cap = solve_knapsack_dp(self.parcels, capacity=0)
        self.assertEqual(zero_cap["max_value"], 0)
        self.assertEqual(zero_cap["selected_parcels"], [])

        empty_res = solve_knapsack_dp([], capacity=10)
        self.assertEqual(empty_res["max_value"], 0)
        self.assertEqual(empty_res["selected_parcels"], [])

    def test_dijkstra_and_unreachable_node(self) -> None:
        dist, parent = dijkstra_shortest_paths(self.graph, "HUB")
        # HUB -> B (2) -> A (2) = cost 4 (cheaper than direct HUB -> A cost 5)
        self.assertEqual(dist["A"], 4.0)
        self.assertEqual(reconstruct_path(parent, "HUB", "A"), ["HUB", "B", "A"])
        self.assertEqual(dist["ISOLATED"], float("inf"))
        self.assertEqual(reconstruct_path(parent, "HUB", "ISOLATED"), [])

    def test_nearest_neighbor_tsp_route(self) -> None:
        route = nearest_neighbor_tsp(self.graph, "HUB", ["A", "B", "C"], return_to_depot=True)
        self.assertEqual(route["stop_order"][0], "HUB")
        self.assertEqual(route["stop_order"][-1], "HUB")
        self.assertEqual(sorted(set(route["stop_order"])), ["A", "B", "C", "HUB"])
        self.assertGreater(route["total_cost"], 0)


if __name__ == "__main__":
    unittest.main()