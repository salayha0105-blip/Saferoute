"""
Safe Route Lahore - Step 6: the web app (what you show in the live demo)
========================================================================

Run on your laptop:   streamlit run app.py
Live version:         deployed on share.streamlit.io from the GitHub repo.

WHAT THE USER DOES:
  1. Picks where they start and where they're going.
  2. Picks the time (6, 9 or 11 PM).
  3. Ticks one or more route options in the map's corner. Each has its own
     colour, and only ticked routes are shown:
        Fastest       (black)  - shortest distance, ignores safety
        Balanced      (blue)   - a less-safe street counts as up to 4x longer
        Safety-first  (purple) - a less-safe street counts as up to 11x longer

Ticking a route is handled by the map itself (a Leaflet layer control), so
it is instant. Only changing From / To / time recomputes the routes.
"""

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from road_graph import build_graph
from routing import MODES, a_star, attach_risk, describe_route
from safety_tools import battery_warning, checkin_panel, panic_button, start_checkin

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

segment_risk = load_risk()

if start == goal:
    st.info("Pick two different places.")
    st.stop()


# ---------------- compute every route ----------------
# Cached: the same From / To / time is only computed once.
@st.cache_data
def compute_routes(start, goal, slot):
    G = attach_risk(build_graph(), load_risk(), slot)
    out = {}
    for mode, weight in MODES.items():
        path, _ = a_star(G, start, goal, weight)
        info = describe_route(G, path)
        shape = []
        for a, b in zip(path, path[1:]):
            pts = list(G[a][b]["shape"])
            if pts and pts[0] != G.nodes[a]["pos"] and pts[-1] == G.nodes[a]["pos"]:
                pts = pts[::-1]                   # make the street run in walking direction
            shape += pts
        out[mode] = {"path": path, "info": info, "shape": shape}
    return out, G.nodes[start]["pos"], G.nodes[goal]["pos"], G.nodes["Hafeez road bend"]["pos"]


routes, start_pos, goal_pos, centre = compute_routes(start, goal, SLOT_NAMES[slot_label])

# ---------------- safety tools (simulated) ----------------
# "Last known location" for the demo: halfway along the balanced route.
balanced_shape = routes["balanced"]["shape"]
last_location = tuple(balanced_shape[len(balanced_shape) // 2])

st.sidebar.divider()
st.sidebar.markdown("**🛟 Safety tools (demo)**")
with st.sidebar:
    panic_button(last_location)
contacts_text = st.sidebar.text_input("Trusted contacts", "Ammi, Best friend")
st.session_state.contacts = [c.strip() for c in contacts_text.split(",") if c.strip()]
battery = st.sidebar.slider("Phone battery (simulated)", 0, 100, 80, format="%d%%")
fast = st.sidebar.toggle("Fast demo (10 s instead of 60 s)", value=True)
if st.sidebar.button("Simulate going off route"):
    start_checkin(fast)

battery_warning(battery, last_location)
checkin_panel(last_location)

# ---------------- map ----------------
# All three routes are drawn as separate layers. The tick boxes in the
# map's corner (a Leaflet "layer control") show or hide them INSIDE THE
# BROWSER, so ticking a box is instant: no reloading, no "running...".
fmap = folium.Map(location=centre, zoom_start=16, tiles=None)
folium.TileLayer("OpenStreetMap", control=False).add_to(fmap)   # base map, not a tick box
# Widest line first, so when routes share a street you still see every colour.
for mode in sorted(ROUTE_STYLE, key=lambda m: -ROUTE_STYLE[m][2]):
    colour, _, width = ROUTE_STYLE[mode]
    label = (f'<span style="color:{colour};font-size:18px">&#9632;</span> '
             f'{mode.capitalize()}')
    layer = folium.FeatureGroup(name=label, show=(mode == "balanced"))
    folium.PolyLine(routes[mode]["shape"], color=colour, weight=width, opacity=0.9,
                    tooltip=f"{mode}: {routes[mode]['info']['length_m']} m").add_to(layer)
    layer.add_to(fmap)
folium.Marker(start_pos, tooltip="Start", icon=folium.Icon(color="green", icon="play")).add_to(fmap)
folium.Marker(goal_pos, tooltip="Destination", icon=folium.Icon(color="red", icon="flag")).add_to(fmap)
folium.LayerControl(collapsed=False, position="topright").add_to(fmap)
all_points = [pt for r in routes.values() for pt in r["shape"]]
fmap.fit_bounds([[min(p[0] for p in all_points), min(p[1] for p in all_points)],
                 [max(p[0] for p in all_points), max(p[1] for p in all_points)]], padding=(30, 30))

left, right = st.columns([3, 2])
with left:
    st_folium(fmap, key="map", height=580, use_container_width=True, returned_objects=[])
    st.caption("Tick the boxes on the map to show or hide each route.")

# ---------------- explanation ----------------
with right:
    st.subheader(f"Routes at {slot_label}")
    selected = list(ROUTE_STYLE)
    fastest = routes["fastest"]["info"]
    table = pd.DataFrame([{
        "Route": f"{ROUTE_STYLE[m][1]} {m.capitalize()}",
        "Distance (m)": routes[m]["info"]["length_m"],
        "Extra vs fastest": f"+{routes[m]['info']['length_m'] - fastest['length_m']} m",
        "Average risk (0-1)": f"{routes[m]['info']['avg_risk']:.2f}",
    } for m in selected])
    st.dataframe(table, hide_index=True, use_container_width=True)

    same = [m for m in selected if m != "fastest" and routes[m]["path"] == routes["fastest"]["path"]]
    if same:
        st.success(f"{', '.join(x.capitalize() for x in same)} = fastest here.")
    for m in selected:
        st.markdown(f"**{ROUTE_STYLE[m][1]} {m.capitalize()}:** " + " → ".join(routes[m]["info"]["segments"]))

    with st.expander("How does this work?"):
        st.markdown(
            "- A **decision tree** predicts each street's safety from lighting, open shops, "
            "cameras, guards, police, main road vs gali, distance to police and hospital, other women around and time of night.\n"
            "- **Fuzzy logic** turns the prediction into words like *less safe after 9 PM*.\n"
            "- **A\\* search** finds the cheapest route, where "
            "cost = length × (1 + weight × risk). Weight: fastest 0, balanced 3, safety-first 10. "
            "A higher weight makes less-safe streets 'feel' longer, so the search goes around them.\n"
            "- ⚠️ The safety data is **synthetic** (generated by documented rules), approved for this "
            "course prototype. Do not use it for real travel decisions."
        )
