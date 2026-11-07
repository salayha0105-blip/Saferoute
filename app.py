"""
Safe Route Lahore - Step 6: the web app (what you show in the live demo)
========================================================================

Run on your laptop:   streamlit run app.py
Live version:         deployed on share.streamlit.io from the GitHub repo.

WHAT THE USER DOES:
  1. Picks where they start and where they're going.
  2. Picks the time (6, 9 or 11 PM).
  3. Ticks one or more route options. Each option has its own colour, and
     ONLY the ticked routes are drawn on the map:
        Fastest       (black)  - shortest distance, ignores safety
        Balanced      (blue)   - a risky street counts as up to 4x longer
        Safety-first  (purple) - a risky street counts as up to 11x longer

The map is drawn ONCE. When the user ticks or unticks a route, only the
route lines are added or removed (st_folium's feature_group_to_add), so the
map does not reload or jump.
"""

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from road_graph import build_graph
from routing import MODES, a_star, attach_risk, describe_route

st.set_page_config(page_title="Safe Route Lahore", page_icon="🛡️", layout="wide")

# Each route option has its own colour and line width.
ROUTE_STYLE = {
    #  mode:          (colour,    emoji, line width)
    "fastest":       ("#222222", "⬛", 11),
    "balanced":      ("#1f5fd1", "🟦", 7),
    "safety-first":  ("#8e3fd6", "🟪", 4),
}
SLOT_NAMES = {"6 PM": "6pm", "9 PM": "9pm", "11 PM": "11pm"}


@st.cache_data
def load_risk():
    return pd.read_csv("segment_risk.csv")


# ---------------- sidebar: the user's choices ----------------
st.sidebar.title("🛡️ Safe Route Lahore")
st.sidebar.caption("Pilot area: Gulberg III. Prototype using SYNTHETIC data.")
nodes = sorted(build_graph().nodes)
start = st.sidebar.selectbox("From", nodes, index=nodes.index("Hafeez Centre"))
goal = st.sidebar.selectbox("To", nodes, index=nodes.index("Tipu Road north"))
slot_label = st.sidebar.radio("Time of night", list(SLOT_NAMES), index=2, horizontal=True)

st.sidebar.markdown("**Show routes**")
selected = [mode for mode, (_, emoji, _) in ROUTE_STYLE.items()
            if st.sidebar.checkbox(f"{emoji} {mode.capitalize()}", value=(mode == "balanced"), key=mode)]

segment_risk = load_risk()
G = attach_risk(build_graph(), segment_risk, SLOT_NAMES[slot_label])

if start == goal:
    st.info("Pick two different places.")
    st.stop()

# ---------------- compute every route (cheap: the map is small) ----------------
routes = {}
for mode, weight in MODES.items():
    path, _ = a_star(G, start, goal, weight)
    routes[mode] = (path, describe_route(G, path))

# ---------------- map ----------------
# The base map never changes, so Streamlit keeps it on screen. Routes and
# markers go in a FeatureGroup that is swapped in and out on each click.
@st.cache_resource
def base_map():
    return folium.Map(location=MAP_CENTRE, zoom_start=16, tiles="OpenStreetMap")


MAP_CENTRE = tuple(G.nodes["Hafeez road bend"]["pos"])
layer = folium.FeatureGroup(name="routes")
# Widest line first, so when routes share a street you still see every colour.
for mode in sorted(selected, key=lambda m: -ROUTE_STYLE[m][2]):
    colour, _, width = ROUTE_STYLE[mode]
    path, info = routes[mode]
    shape = []
    for a, b in zip(path, path[1:]):
        pts = list(G[a][b]["shape"])
        if pts and pts[0] != G.nodes[a]["pos"] and pts[-1] == G.nodes[a]["pos"]:
            pts = pts[::-1]                       # make the street run in walking direction
        shape += pts
    folium.PolyLine(shape, color=colour, weight=width, opacity=0.9,
                    tooltip=f"{mode}: {info['length_m']} m").add_to(layer)
folium.Marker(G.nodes[start]["pos"], tooltip="Start", icon=folium.Icon(color="green", icon="play")).add_to(layer)
folium.Marker(G.nodes[goal]["pos"], tooltip="Destination", icon=folium.Icon(color="red", icon="flag")).add_to(layer)

left, right = st.columns([3, 2])
with left:
    st_folium(base_map(), key="map", feature_group_to_add=layer, center=MAP_CENTRE, zoom=16,
              height=580, use_container_width=True, returned_objects=[])

# ---------------- explanation ----------------
with right:
    if not selected:
        st.info("Tick at least one route option in the sidebar to see a route.")
        st.stop()
    st.subheader(f"Routes at {slot_label}")
    fastest = routes["fastest"][1]
    table = pd.DataFrame([{
        "Route": f"{ROUTE_STYLE[m][1]} {m.capitalize()}",
        "Distance (m)": routes[m][1]["length_m"],
        "Extra vs fastest": f"+{routes[m][1]['length_m'] - fastest['length_m']} m",
        "Average risk (0-1)": f"{routes[m][1]['avg_risk']:.2f}",
    } for m in selected])
    st.dataframe(table, hide_index=True, use_container_width=True)

    same = [m for m in selected if m != "fastest" and routes[m][0] == routes["fastest"][0]]
    if same:
        st.success(f"{', '.join(x.capitalize() for x in same)} = fastest here.")
    for m in selected:
        st.markdown(f"**{ROUTE_STYLE[m][1]} {m.capitalize()}:** " + " → ".join(routes[m][1]["segments"]))

    with st.expander("How does this work?"):
        st.markdown(
            "- A **decision tree** predicts each street's safety from lighting, open shops, "
            "cameras, crowds and time of night.\n"
            "- **Fuzzy logic** turns the prediction into words like *risky after 9 PM*.\n"
            "- **A\\* search** finds the cheapest route, where "
            "cost = length × (1 + weight × risk). Weight: fastest 0, balanced 3, safety-first 10. "
            "A higher weight makes risky streets 'feel' longer, so the search goes around them.\n"
            "- ⚠️ The safety data is **synthetic** (generated by documented rules), approved for this "
            "course prototype. Do not use it for real travel decisions."
        )
