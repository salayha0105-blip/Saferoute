"""
Safe Route Lahore - the smooth map (Python side)
================================================

WHY NOT FOLIUM ANY MORE?
  st_folium rebuilt the whole map every time From / To / time changed, so the
  map went black for a moment and the route just popped in. Now the map is a
  small custom Streamlit component (map_frontend/index.html, using Leaflet).
  The browser loads it ONCE; afterwards Python only sends it new data, and the
  page animates: pins slide, the camera glides, and the routes grow from the
  place you picked last.

WHAT PYTHON SENDS (one dict called `data`):
  routes      - for each mode: its line on the map, colour, width, length
  start, goal - names and positions
  grow_from   - "start" or "goal": which end the routes grow from
  places      - every junction, so you can click one to start or end there
  streets     - all street shapes, drawn only if the map pictures can't load
  walk_notes  - what Hammy says on each street during "Walk me home"

WHAT COMES BACK:
  When you click a dot on the map and press "Start here" / "Go here", the
  component returns {"action": "from" or "to", "place": name, "nonce": time}.
"""

import os

import streamlit.components.v1 as components

_FRONTEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map_frontend")
_map = components.declare_component("safer_map", path=_FRONTEND)

# Friendly street names for Hammy, from the segment code's letters.
STREET_NAMES = {
    "MB": "Main Boulevard", "SS": "Sir Syed Road", "DG": "Dopatta Gali", "MM": "MM Alam Road",
    "TP": "Tipu Road", "HT": "Hafeez Centre road", "NJ": "Noor Jahan Road", "TQ": "Tariq Road",
    "CR": "the north curve road", "L": "the side lane",
}


def street_name(segment_id):
    letters = segment_id.rstrip("0123456789")
    return STREET_NAMES.get(letters, segment_id)


def walk_notes(G, path, slot_label):
    """One short line from Hammy at the start of each new street on the route.
    Uses the same fuzzy safety ranges as the rest of the app."""
    notes, last = [], None
    for u, v in zip(path, path[1:]):
        d = G[u][v]
        name = street_name(d["segment_id"])
        if name == last:
            continue
        last = name
        name = name[0].upper() + name[1:]
        band = d["band"]
        if band == "Avoid":
            text = f"{name} is one to avoid at {slot_label} if you can. Walk briskly, stay where it's lit, I'm right here 💛"
        elif band == "Risky":
            text = f"{name} is risky at {slot_label}. Stay on the lit side and keep your phone handy 📱"
        elif band == "Be careful":
            text = f"{name}: be a little careful at {slot_label} 👀"
        else:
            text = f"{name} is one of the safer streets at {slot_label} ✨"
        notes.append({"pos": list(G.nodes[u]["pos"]), "text": text})
    return notes


def safer_map(data, key="safer_map", height=600):
    """Draw the map. Returns the last click from the map (or None)."""
    data = dict(data, height=height)
    return _map(data=data, key=key, default=None)
