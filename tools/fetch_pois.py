"""
Downloads REAL police stations and hospitals around Gulberg III from
OpenStreetMap (run by a GitHub Action, like fetch_osm.py).
Saves data/osm/pois.json: [{"kind": "police"|"hospital", "name": ..., "lat": ..., "lon": ...}]
"""
import json
import os

import osmnx as ox

os.makedirs("data/osm", exist_ok=True)
CENTRE = (31.5131, 74.3497)          # middle of our pilot area
TAGS = {"amenity": ["police", "hospital", "clinic"], "healthcare": ["hospital"]}

gdf = ox.features_from_point(CENTRE, tags=TAGS, dist=3000)
pois = []
for _, row in gdf.iterrows():
    kind = "police" if row.get("amenity") == "police" else "hospital"
    point = row.geometry.centroid
    name = row.get("name")
    pois.append({"kind": kind, "name": name if isinstance(name, str) else None,
                 "lat": round(point.y, 6), "lon": round(point.x, 6)})
with open("data/osm/pois.json", "w") as f:
    json.dump(pois, f, indent=1, ensure_ascii=False)
print(len(pois), "places:", sum(p["kind"] == "police" for p in pois), "police,",
      sum(p["kind"] == "hospital" for p in pois), "hospitals/clinics")
