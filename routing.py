"""
Safe Route Lahore - Step 5: A* search for the safest sensible route (course Week III)
=====================================================================================

WHAT THIS FILE DOES:
  Finds a route between two junctions that balances DISTANCE and SAFETY.

THE KEY IDEA - "cost" of walking a street:
      cost = length_in_metres * (1 + safety_weight * risk)
  - risk comes from the decision tree (0 = safe, 1 = risky) for that time slot.
  - safety_weight decides how much the user cares about safety:
        fastest      weight 0   -> cost is just distance (normal shortest path)
        balanced     weight 3   -> a fully risky street "feels" 4x as long
        safety-first weight 10  -> a fully risky street "feels" 11x as long
  So a risky lane is not forbidden, it just looks "longer" to the search,
  and the search takes it only if the detour around it is very long.

A* SEARCH IN ONE PARAGRAPH:
  A* always expands the junction with the smallest  f = g + h, where
     g = cost of the path so far, and
     h = a guess of the remaining cost (the "heuristic").
  Our h is the straight-line distance to the goal. Because every street's
  cost is at least its length, and its length is at least the straight-line
  distance, h never OVER-estimates. That makes h "admissible", which
  guarantees A* finds the cheapest route. It is faster than Dijkstra
  because h steers the search toward the goal.

WHY A* AND NOT A GENETIC ALGORITHM:
  Our map is small (31 junctions), and A* is guaranteed to find the best
  route for a given weight, instantly. A GA gives "good" but not guaranteed
  routes and needs tuning. We kept the 3 safety weights idea from the GA plan.
"""

import heapq
from itertools import combinations

import networkx as nx
import pandas as pd

from road_graph import build_graph, distance_m

MODES = {"fastest": 0, "balanced": 3, "safety-first": 10}


def attach_risk(G, segment_risk, slot):
    """Copy each segment's predicted risk (for the chosen time slot) onto the
    graph edges, so the search can read it."""
    risk = segment_risk[segment_risk["slot"] == slot].set_index("segment_id")
    for u, v, data in G.edges(data=True):
        row = risk.loc[data["segment_id"]]
        data["risk"] = float(row["risk"])
        data["night_phrase"] = row["night_phrase"]
        data["fuzzy_word"] = row["fuzzy_word"]
    return G


def edge_cost(data, weight):
    return data["length"] * (1 + weight * data["risk"])


def a_star(G, start, goal, weight):
    """A* written out step by step (so we can show it, not just call a library).
    Returns (path as a list of junctions, number of junctions expanded)."""
    goal_pos = G.nodes[goal]["pos"]

    def h(node):                                   # the heuristic: straight-line metres
        return distance_m(G.nodes[node]["pos"], goal_pos)

    open_list = [(h(start), 0.0, start)]           # priority queue of (f, g, node)
    best_g = {start: 0.0}                          # cheapest known cost to each node
    came_from = {}                                 # to rebuild the path at the end
    expanded = 0

    while open_list:
        f, g, node = heapq.heappop(open_list)      # junction with the smallest f
        if g > best_g.get(node, float("inf")):     # an old, worse copy: skip it
            continue
        expanded += 1
        if node == goal:                           # reached the goal: rebuild path
            path = [node]
            while node in came_from:
                node = came_from[node]
                path.append(node)
            return path[::-1], expanded
        for neighbour, data in G[node].items():
            new_g = g + edge_cost(data, weight)
            if new_g < best_g.get(neighbour, float("inf")):
                best_g[neighbour] = new_g
                came_from[neighbour] = node
                heapq.heappush(open_list, (new_g + h(neighbour), new_g, neighbour))
    return None, expanded


def describe_route(G, path):
    """Total length, average risk the walker is exposed to, and the riskiest
    street on the route, all in plain words for the app."""
    length, risk_metres, steps, worst = 0.0, 0.0, [], None
    for u, v in zip(path, path[1:]):
        d = G[u][v]
        length += d["length"]
        risk_metres += d["length"] * d["risk"]
        steps.append(d["segment_id"])
        if worst is None or d["risk"] > worst[1]:
            worst = (d["segment_id"], d["risk"], d["night_phrase"])
    # merge repeated ids (a segment split in two halves shows once)
    segments = [s for i, s in enumerate(steps) if i == 0 or s != steps[i - 1]]
    return {
        "segments": segments,
        "length_m": round(length),
        "avg_risk": round(risk_metres / length, 3) if length else 0.0,
        "worst_segment": worst,
    }


def evaluate(segment_risk, slot="11pm"):
    """Run every start/goal pair through all 3 modes and compare.
    This is our routing evaluation for the report."""
    G = attach_risk(build_graph(), segment_risk, slot)
    rows = []
    for start, goal in combinations(G.nodes, 2):
        result = {}
        for mode, w in MODES.items():
            path, expanded = a_star(G, start, goal, w)
            info = describe_route(G, path)
            result[mode] = (info, expanded)
        # sanity check: our A* must match networkx's Dijkstra exactly
        for mode, w in MODES.items():
            ref = nx.dijkstra_path_length(G, start, goal, weight=lambda u, v, d, w=w: edge_cost(d, w))
            path, _ = a_star(G, start, goal, w)
            ours = sum(edge_cost(G[a][b], w) for a, b in zip(path, path[1:]))
            assert abs(ours - ref) < 1e-6, "A* disagrees with Dijkstra!"
        base_len = result["fastest"][0]["length_m"]
        for mode in MODES:
            info, expanded = result[mode]
            rows.append({
                "start": start, "goal": goal, "mode": mode,
                "length_m": info["length_m"],
                "extra_distance_pct": round(100 * (info["length_m"] - base_len) / base_len, 1),
                "avg_risk": info["avg_risk"],
                "worst_risk": round(info["worst_segment"][1], 3),
                "junctions_expanded": expanded,
            })
    table = pd.DataFrame(rows)
    # Dijkstra comparison for search efficiency (A* with h = 0 IS Dijkstra)
    dijkstra_expanded = []
    for start, goal in combinations(G.nodes, 2):
        dijkstra_expanded.append(_dijkstra_expanded(G, start, goal, MODES["balanced"]))
    summary = table.groupby("mode")[["length_m", "extra_distance_pct", "avg_risk",
                                     "worst_risk", "junctions_expanded"]].mean().round(3)
    summary = summary.loc[list(MODES)]
    return table, summary, sum(dijkstra_expanded) / len(dijkstra_expanded)


def _dijkstra_expanded(G, start, goal, weight):
    """Same search with h = 0 (that is exactly Dijkstra), to count expansions."""
    open_list, best_g, expanded = [(0.0, start)], {start: 0.0}, 0
    while open_list:
        g, node = heapq.heappop(open_list)
        if g > best_g.get(node, float("inf")):
            continue
        expanded += 1
        if node == goal:
            return expanded
        for nb, d in G[node].items():
            ng = g + edge_cost(d, weight)
            if ng < best_g.get(nb, float("inf")):
                best_g[nb] = ng
                heapq.heappush(open_list, (ng, nb))
    return expanded


if __name__ == "__main__":
    import json
    import os
    os.makedirs("results", exist_ok=True)
    seg_risk = pd.read_csv("segment_risk.csv")
    all_summaries = {}
    for slot in ["6pm", "9pm", "11pm"]:
        table, summary, dij = evaluate(seg_risk, slot)
        table.to_csv(f"results/routing_eval_{slot}.csv", index=False)
        print(f"\n=== {slot}: average over all {len(table)//3} start/goal pairs ===")
        print(summary.to_string())
        print(f"Dijkstra (balanced) expands {dij:.1f} junctions on average vs "
              f"A* {summary.loc['balanced', 'junctions_expanded']:.1f}")
        all_summaries[slot] = {"by_mode": summary.to_dict(orient="index"),
                               "dijkstra_expanded_balanced": round(dij, 2)}
    with open("results/routing_summary.json", "w") as f:
        json.dump(all_summaries, f, indent=2)

    # one worked example for the report / presentation
    G = attach_risk(build_graph(), seg_risk, "11pm")
    print("\nExample at 11 PM: Main Blvd / L8 -> MM Alam middle")
    for mode, w in MODES.items():
        path, _ = a_star(G, "Main Blvd / L8", "MM Alam middle", w)
        info = describe_route(G, path)
        print(f"  {mode:13s} {info['length_m']:5d} m  avg risk {info['avg_risk']:.2f}  via {' > '.join(info['segments'])}")
