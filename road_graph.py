"""
Safe Route Lahore - Step 3: the road map as a graph
====================================================

WHAT THIS FILE DOES:
  Turns our Gulberg III pilot map into a GRAPH, the data structure that
  search algorithms like A* work on:
    - a NODE is a junction (where roads meet)
    - an EDGE is a street segment between two junctions (MB1, MM2, L5 ...)
  Each edge stores its length in metres and its segment_id, so we can look
  up its predicted risk later.

WHERE THE COORDINATES COME FROM (be honest about this in the report):
  OpenStreetMap could not be downloaded from our build environment, so the
  junctions were traced by hand from our segment map
  (pilot-map-segments.png). Pixel positions were converted to latitude and
  longitude using Hafeez Centre as the anchor point and a scale of about
  1.2 metres per pixel. Positions are APPROXIMATE (roughly +/- 50 m).
  Future work: replace with the real OSM network using the osmnx library.
"""

import math

import networkx as nx

# ---------------------------------------------------------------------------
# Converting map pixels to real-world latitude / longitude
# ---------------------------------------------------------------------------
ANCHOR_PIXEL = (45, 1180)              # Hafeez Centre on our map image
ANCHOR_LATLON = (31.5163, 74.3432)     # Hafeez Centre in real life (approx.)
METRES_PER_PIXEL = 1.2
METRES_PER_DEG_LAT = 111_000
METRES_PER_DEG_LON = 111_000 * math.cos(math.radians(31.5))   # ~94,650 in Lahore


def pixel_to_latlon(x, y):
    """Move right on the map = east (longitude up); move down = south (latitude down)."""
    dx_m = (x - ANCHOR_PIXEL[0]) * METRES_PER_PIXEL
    dy_m = (y - ANCHOR_PIXEL[1]) * METRES_PER_PIXEL
    lat = ANCHOR_LATLON[0] - dy_m / METRES_PER_DEG_LAT
    lon = ANCHOR_LATLON[1] + dx_m / METRES_PER_DEG_LON
    return lat, lon


# ---------------------------------------------------------------------------
# Junctions (nodes): name -> (pixel x, pixel y) on our map
# ---------------------------------------------------------------------------
JUNCTIONS = {
    "Main Blvd / North curve": (55, 640),
    "Main Blvd / L8": (48, 1035),
    "Hafeez Centre": (45, 1180),
    "Main Blvd / L9": (45, 1280),
    "Main Blvd / Noor Jahan": (40, 1640),
    "Sir Syed / North curve": (215, 600),
    "Sir Syed / first side road": (212, 790),
    "Sir Syed / L8": (208, 1035),
    "Sir Syed / Hafeez road": (210, 1180),
    "Sir Syed / L9": (207, 1290),
    "Sir Syed south end": (205, 1420),
    "Crumble (MM Alam)": (420, 560),
    "Junaid Jamshed (MM Alam)": (500, 680),
    "MM Alam middle": (600, 860),
    "Tehzeeb Bakers (MM Alam)": (690, 1110),
    "MM Alam / Tariq Road": (740, 1340),
    "MM Alam roundabout": (810, 1580),
    "Tipu Road north": (760, 560),
    "Tipu Road middle": (860, 800),
    "Tipu Road south": (900, 1030),
    "Dopatta Gali top": (345, 880),
    "Dopatta Gali / L11": (330, 1080),
    "Dopatta Gali / Hafeez road": (325, 1180),
    "Dopatta Gali / L10": (330, 1270),
    "Parking loop": (335, 1420),
    "Hafeez road bend": (520, 1170),
    "Lane junction (L10/L12)": (545, 1290),
    "Tariq Road bend": (545, 1415),
    "Noor Jahan first junction": (205, 1640),
    "Dopatta Gali / Noor Jahan": (460, 1640),
    "Noor Jahan / L14": (590, 1640),
}

# ---------------------------------------------------------------------------
# Street segments (edges): (segment_id, from junction, to junction, bend points)
# A segment that passes through a junction is split into two edges with the
# same segment_id (e.g. MB1), so both halves share one risk value.
# ---------------------------------------------------------------------------
SEGMENTS = [
    ("MB1", "Main Blvd / North curve", "Main Blvd / L8", []),
    ("MB1", "Main Blvd / L8", "Hafeez Centre", []),
    ("MB2", "Hafeez Centre", "Main Blvd / L9", []),
    ("MB2", "Main Blvd / L9", "Main Blvd / Noor Jahan", []),
    ("SS1", "Sir Syed / North curve", "Sir Syed / first side road", []),
    ("SS2", "Sir Syed / first side road", "Sir Syed / L8", []),
    ("SS2", "Sir Syed / L8", "Sir Syed / Hafeez road", []),
    ("SS3", "Sir Syed / Hafeez road", "Sir Syed / L9", []),
    ("SS3", "Sir Syed / L9", "Sir Syed south end", []),
    ("CR1", "Main Blvd / North curve", "Sir Syed / North curve", []),
    ("CR2", "Sir Syed / North curve", "Crumble (MM Alam)", [(320, 580)]),
    ("CR3", "Junaid Jamshed (MM Alam)", "Tipu Road north", [(630, 630)]),
    ("MM1", "Crumble (MM Alam)", "Junaid Jamshed (MM Alam)", []),
    ("MM2", "Junaid Jamshed (MM Alam)", "MM Alam middle", []),
    ("MM2", "MM Alam middle", "Tehzeeb Bakers (MM Alam)", []),
    ("MM3", "Tehzeeb Bakers (MM Alam)", "MM Alam / Tariq Road", []),
    ("MM4", "MM Alam / Tariq Road", "MM Alam roundabout", []),
    ("TP1", "Tipu Road north", "Tipu Road middle", []),
    ("TP2", "Tipu Road middle", "Tipu Road south", []),
    ("HT1", "Hafeez Centre", "Sir Syed / Hafeez road", []),
    ("HT2", "Sir Syed / Hafeez road", "Dopatta Gali / Hafeez road", []),
    ("HT3", "Dopatta Gali / Hafeez road", "Hafeez road bend", []),
    ("HT4", "Hafeez road bend", "Tehzeeb Bakers (MM Alam)", []),
    ("HT5", "Tehzeeb Bakers (MM Alam)", "Tipu Road south", [(800, 1060)]),
    ("DG1", "Dopatta Gali top", "Dopatta Gali / L11", []),
    ("DG2", "Dopatta Gali / L11", "Dopatta Gali / Hafeez road", []),
    ("DG3", "Dopatta Gali / Hafeez road", "Dopatta Gali / L10", []),
    ("DG3", "Dopatta Gali / L10", "Parking loop", []),
    ("DG4", "Parking loop", "Dopatta Gali / Noor Jahan", [(440, 1470)]),
    ("TQ1", "Parking loop", "Tariq Road bend", [(440, 1440)]),
    ("TQ2", "Tariq Road bend", "MM Alam / Tariq Road", []),
    ("NJ1", "Main Blvd / Noor Jahan", "Noor Jahan first junction", []),
    ("NJ2", "Noor Jahan first junction", "Dopatta Gali / Noor Jahan", []),
    ("NJ3", "Dopatta Gali / Noor Jahan", "Noor Jahan / L14", []),
    ("NJ3", "Noor Jahan / L14", "MM Alam roundabout", []),
    # residential lanes (approximate shapes)
    ("L1", "Sir Syed / first side road", "Dopatta Gali top", [(300, 790)]),
    ("L2", "Dopatta Gali top", "MM Alam middle", [(490, 830)]),
    ("L3", "Sir Syed / North curve", "Junaid Jamshed (MM Alam)", [(300, 665), (420, 700)]),
    ("L4", "Dopatta Gali top", "Junaid Jamshed (MM Alam)", [(425, 758)]),
    ("L5", "Junaid Jamshed (MM Alam)", "Tipu Road middle", [(670, 760)]),
    ("L6", "MM Alam middle", "Tipu Road middle", [(758, 840)]),
    ("L7", "MM Alam middle", "Tipu Road south", [(735, 980)]),
    ("L8", "Main Blvd / L8", "Sir Syed / L8", []),
    ("L9", "Main Blvd / L9", "Sir Syed / L9", []),
    ("L10", "Dopatta Gali / L10", "Lane junction (L10/L12)", [(380, 1270)]),
    ("L11", "Dopatta Gali / L11", "Tehzeeb Bakers (MM Alam)", [(400, 1087), (520, 1090)]),
    ("L12", "Lane junction (L10/L12)", "Tariq Road bend", []),
    ("L13", "Sir Syed south end", "Parking loop", [(330, 1437)]),
    ("L14", "Tariq Road bend", "Noor Jahan / L14", [(585, 1552)]),
    ("L15", "Tipu Road south", "MM Alam roundabout", [(900, 1200), (860, 1430)]),
]


def distance_m(a, b):
    """Straight-line distance in metres between two (lat, lon) points.
    At this tiny scale (about 1 km) a flat-earth formula is accurate enough."""
    dy = (a[0] - b[0]) * METRES_PER_DEG_LAT
    dx = (a[1] - b[1]) * METRES_PER_DEG_LON
    return math.hypot(dx, dy)


def build_graph():
    """Create the networkx graph. Streets are two-way for pedestrians, so the
    graph is undirected."""
    G = nx.Graph()
    for name, (x, y) in JUNCTIONS.items():
        G.add_node(name, pos=pixel_to_latlon(x, y))
    for seg_id, u, v, bends in SEGMENTS:
        # the full shape of the street: start, bend points, end
        points = [G.nodes[u]["pos"]] + [pixel_to_latlon(*p) for p in bends] + [G.nodes[v]["pos"]]
        length = sum(distance_m(points[i], points[i + 1]) for i in range(len(points) - 1))
        G.add_edge(u, v, segment_id=seg_id, length=round(length, 1), shape=points)
    return G


if __name__ == "__main__":
    G = build_graph()
    print(f"{G.number_of_nodes()} junctions, {G.number_of_edges()} street pieces, "
          f"{len({d['segment_id'] for *_, d in G.edges(data=True)})} unique segments")
    print("Connected (can reach every junction from every other)?", nx.is_connected(G))
    total = sum(d["length"] for *_, d in G.edges(data=True))
    print(f"Total street length: {total/1000:.2f} km")
