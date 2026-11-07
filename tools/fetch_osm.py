"""
Downloads the REAL Gulberg III street network from OpenStreetMap (run by a
GitHub Action, because OSM is reachable from GitHub's servers).
Saves:
  data/osm/gulberg_walk.graphml   - the walkable street network
  data/osm/geocodes.json          - real coordinates of a few landmarks
"""
import json
import os

import osmnx as ox

os.makedirs("data/osm", exist_ok=True)
ox.settings.use_cache = False

PLACES = {
    "Hafeez Centre": "Hafeez Centre, Lahore, Pakistan",
    "MM Alam Road": "M.M. Alam Road, Lahore, Pakistan",
    "Sir Syed Road": "Sir Syed Road, Gulberg, Lahore, Pakistan",
    "Noor Jahan Road": "Noor Jahan Road, Lahore, Pakistan",
    "Tipu Road": "Tipu Road, Lahore, Pakistan",
    "Main Boulevard Gulberg": "Main Boulevard Gulberg, Lahore, Pakistan",
    "Gulberg III": "Gulberg III, Lahore, Pakistan",
}
geocodes = {}
for name, query in PLACES.items():
    try:
        geocodes[name] = ox.geocode(query)
    except Exception as e:  # keep going if one lookup fails
        geocodes[name] = f"failed: {e}"
print(json.dumps(geocodes, indent=2))
with open("data/osm/geocodes.json", "w") as f:
    json.dump(geocodes, f, indent=2)

centre = geocodes["Hafeez Centre"] if isinstance(geocodes["Hafeez Centre"], tuple) else (31.5163, 74.3432)
# Hafeez Centre is on the west edge of our pilot area, so shift the centre east
centre = (centre[0] - 0.003, centre[1] + 0.0065)
G = ox.graph_from_point(centre, dist=1600, network_type="walk", simplify=True)
ox.save_graphml(G, "data/osm/gulberg_walk.graphml")
print(len(G.nodes), "nodes", len(G.edges), "edges")
