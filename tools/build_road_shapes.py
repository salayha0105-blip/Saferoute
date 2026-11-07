"""
Safe Route Lahore - snap our 43 segments onto the REAL OpenStreetMap streets
============================================================================

WHY THIS EXISTS:
  The first version drew each street as straight lines between hand-traced
  junctions, so routes cut across houses on the map. This script fixes that.

WHAT IT DOES:
  1. Calibrates our map picture to real coordinates. 8 junctions whose real
     positions we know from OSM (e.g. Hafeez Centre = Main Boulevard x Ghalib
     Road) are used to fit an "affine transform" (a stretch + rotate + shift).
     Average error after fitting: about 20 m.
  2. Snaps each of our junctions to the nearest real OSM junction.
  3. For each segment, finds the shortest path along REAL streets between its
     two junctions, preferring the street with the right name (e.g. MM2 must
     follow "MM Alam Road"). That path's shape and length replace the old
     straight line.
  4. Saves data/road_shapes.json, which road_graph.py and the app read.
     (So the app itself doesn't need the heavy osmnx library.)

Run (needs: pip install osmnx):   python tools/build_road_shapes.py
Input: data/osm/gulberg_walk.graphml (downloaded by the GitHub Action
       .github/workflows/fetch-osm.yml, because OSM is blocked on some networks)
"""
import json
import math
import os
import sys

import networkx as nx
import numpy as np
import osmnx as ox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from road_graph import JUNCTIONS, SEGMENTS  # noqa: E402

# Step 1: calibration points: (pixel on our map) -> (real lat, lon from OSM)
CALIBRATION = [
    ((45, 1180), (31.5154, 74.3434)),    # Hafeez Centre: Main Blvd x Ghalib Rd
    ((210, 1180), (31.5146, 74.3451)),   # Sir Syed Rd x Ghalib Rd
    ((325, 1180), (31.5140, 74.3465)),   # Dopatta Gali x Ghalib Rd
    ((690, 1110), (31.5130, 74.3511)),   # MM Alam x Ghalib Rd (Tehzeeb)
    ((900, 1030), (31.51276, 74.35477)), # Tipu Rd x Ghalib Rd
    ((205, 1640), (31.50988, 74.34282)), # Sir Syed Rd x Noor Jahan Rd
    ((460, 1640), (31.50872, 74.34559)), # Dopatta Gali x Noor Jahan Rd
    ((810, 1580), (31.5074, 74.3497)),   # Hussain Chowk (MM Alam roundabout)
]
A = np.array([[x, y, 1] for (x, y), _ in CALIBRATION])
B = np.array([ll for _, ll in CALIBRATION])
AFFINE, *_ = np.linalg.lstsq(A, B, rcond=None)   # 3x2 matrix


def pixel_to_real(x, y):
    lat, lon = np.array([x, y, 1]) @ AFFINE
    return float(lat), float(lon)


# Which real street name each road code must follow ("Hafeez road" is called
# Ghalib Road in OSM). Codes not listed have no preferred name.
CODE_TO_OSM_NAME = {
    "MB": "Main Boulevard Gulberg", "SS": "Sir Syed Road", "DG": "Dopatta Gali",
    "MM": "MM Alam Road", "TP": "Tipu Road", "HT": "Ghalib Road",
    "NJ": "Noor Jahan Road",
}
MAJOR = {"primary", "secondary", "tertiary", "trunk"}


def names_of(d):
    n = d.get("name")
    return set(n) if isinstance(n, list) else {n}


def highway_of(d):
    h = d.get("highway")
    return set(h) if isinstance(h, list) else {h}


def preference_weight(seg_id):
    """Edge weight for the path search: real length, multiplied by a penalty
    when the street is not the kind this segment should follow."""
    code = seg_id[:2]
    wanted = CODE_TO_OSM_NAME.get(code)

    def weight(u, v, edges):
        best = math.inf
        for d in edges.values():
            w = d["length"]
            if wanted and wanted not in names_of(d):
                w *= 1.5                     # prefer staying on the named road
            if seg_id.startswith("L") and highway_of(d) & MAJOR:
                w *= 1.5                     # lanes should prefer small streets
            best = min(best, w)
        return best
    return weight


def edge_shape(G, a, b):
    """Real coordinates (lat, lon) along the OSM street from node a to node b."""
    d = min(G[a][b].values(), key=lambda e: e["length"])
    if "geometry" in d:
        pts = [(y, x) for x, y in d["geometry"].coords]
    else:
        pts = [(G.nodes[a]["y"], G.nodes[a]["x"]), (G.nodes[b]["y"], G.nodes[b]["x"])]
    start = (G.nodes[a]["y"], G.nodes[a]["x"])
    if math.dist(pts[0], start) > math.dist(pts[-1], start):
        pts = pts[::-1]                      # make sure it runs from a to b
    return pts, d["length"]


# Only our pilot area's main streets are bridged (generic names like
# "Street 1" repeat across blocks, and bridging them would cut through houses).
BRIDGE_NAMES = set(CODE_TO_OSM_NAME.values()) | {"ایم ایم عالم روڈ"}


def bridge_gaps(G):
    """OSM has small gaps: e.g. Ghalib Road is missing ~100 m where it crosses
    MM Alam's dual carriageway, so a walker would be sent 1.4 km around.
    Fix: join two nodes of the SAME named street with a straight edge when they are close in real life but far apart
    on the network (more than 3x the straight distance)."""
    by_name = {}
    for a, b, d in G.edges(data=True):
        for n in names_of(d):
            if n in BRIDGE_NAMES:
                by_name.setdefault(n, set()).update((a, b))
    pos = {n: (G.nodes[n]["y"] * 111000, G.nodes[n]["x"] * 94650) for n in G.nodes}
    U = nx.Graph()
    for a, b, d in G.edges(data=True):
        U.add_edge(a, b, length=min(U[a][b]["length"], d["length"]) if U.has_edge(a, b) else d["length"])
    pairs = []
    for name, group in by_name.items():
        group = list(group)
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if math.dist(pos[a], pos[b]) < 150:
                    pairs.append((a, b))
    added = 0
    for a, b in set(pairs):
        straight = math.dist(pos[a], pos[b])
        if straight < 1:
            continue
        try:
            net = nx.shortest_path_length(U, a, b, weight="length", )
        except nx.NetworkXNoPath:
            net = math.inf
        if net > 3 * straight:
            for x, y in ((a, b), (b, a)):
                G.add_edge(x, y, length=straight, highway="gap_bridge", name=None)
            U.add_edge(a, b, length=straight)
            added += 1
    print(f"Bridged {added} small gaps in the OSM network")
    return G


def main():
    G = bridge_gaps(ox.load_graphml("data/osm/gulberg_walk.graphml"))

    # Step 2: snap our junctions to real OSM junctions
    names = list(JUNCTIONS)
    # A junction must land on the real roads it belongs to. Example: "Tehzeeb
    # Bakers (MM Alam)" touches MM and HT segments, so it must snap to a node
    # that is on BOTH MM Alam Road and Ghalib Road (their real crossing).
    on_road = {}                                   # OSM street name -> its nodes
    for a, b, d in G.edges(data=True):
        for n in names_of(d):
            on_road.setdefault(n, set()).update((a, b))
    snapped = {}
    for name, pixel in JUNCTIONS.items():
        lat, lon = pixel_to_real(*pixel)
        roads = {CODE_TO_OSM_NAME[s[:2]] for s, u, v, _ in SEGMENTS
                 if name in (u, v) and s[:2] in CODE_TO_OSM_NAME}
        sets = [on_road.get(r, set()) for r in roads]
        candidates = set.intersection(*sets) if sets else set()
        if not candidates and sets:
            candidates = set.union(*sets)
        if not candidates:
            candidates = set(G.nodes)
        snapped[name] = min(candidates, key=lambda n: (G.nodes[n]["y"] - lat) ** 2
                            + ((G.nodes[n]["x"] - lon) * 0.853) ** 2)
    junctions = {n: (G.nodes[snapped[n]]["y"], G.nodes[snapped[n]]["x"]) for n in names}

    # Step 3: follow real streets for every segment
    out = []
    for seg_id, u, v, bends in SEGMENTS:
        stops = [snapped[u]]
        for bx, by in bends:                 # bend points guide lanes along the intended street
            lat, lon = pixel_to_real(bx, by)
            stops.append(ox.distance.nearest_nodes(G, lon, lat))
        stops.append(snapped[v])
        shape, length = [junctions[u]], 0.0
        for s, t in zip(stops, stops[1:]):
            if s == t:
                continue
            path = nx.shortest_path(G, s, t, weight=preference_weight(seg_id))
            straight = math.dist((G.nodes[s]["y"] * 111000, G.nodes[s]["x"] * 94650),
                                 (G.nodes[t]["y"] * 111000, G.nodes[t]["x"] * 94650))
            if nx.path_weight(G, path, "length") > 2 * straight + 50:
                # the name preference caused a long detour: just use the shortest real street path
                path = nx.shortest_path(G, s, t, weight="length")
            for a, b in zip(path, path[1:]):
                pts, l = edge_shape(G, a, b)
                shape += pts[1:]
                length += l
        if length == 0:                      # both ends snapped to the same spot
            length = 1.0
        out.append({"segment_id": seg_id, "u": u, "v": v, "length": round(length, 1),
                    "shape": [[round(a, 6), round(b, 6)] for a, b in shape]})

    with open("data/road_shapes.json", "w") as f:
        json.dump({"source": "OpenStreetMap contributors (ODbL), snapped by tools/build_road_shapes.py",
                   "junctions": junctions, "segments": out}, f)
    total = sum(s["length"] for s in out) / 1000
    print(f"Saved {len(out)} street pieces ({total:.2f} km of real streets) to data/road_shapes.json")


if __name__ == "__main__":
    main()
