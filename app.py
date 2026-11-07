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
  4. Streets underneath are coloured by safety at that time:
        green = safe, orange = be careful, red = risky (fuzzy logic labels)
"""

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from road_graph import build_graph
from routing import MODES, a_star, attach_risk, describe_route

st.set_page_config(page_title="Safe Route Lahore", page_icon="🛡️", layout="wide")

# Street safety colours (thin lines) and route colours (thick lines).
# Route colours are deliberately NOT green/orange/red, so they never get
# confused with the safety colours.
SAFETY_COLOURS = {"safe": "#2e9e4f", "be careful": "#f0a020", "risky": "#d63b3b"}
ROUTE_STYLE = {
    #  mode:          (colour,    emoji, line width, what it means)
    "fastest":       ("#222222", "⬛", 11, "shortest distance, ignores safety"),
    "balanced":      ("#1f5fd1", "🟦", 7, "avoids risky streets if the detour is reasonable"),
    "safety-first":  ("#8e3fd6", "🟪", 4, "avoids risky streets even for a long detour"),
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

st.sidebar.markdown("**Show routes** (tick one or more)")
selected = []
for mode, (colour, emoji, _, meaning) in ROUTE_STYLE.items():
    default = mode == "balanced"
    if st.sidebar.checkbox(f"{emoji} {mode.capitalize()}", value=default, help=meaning, key=mode):
        selected.append(mode)
    st.sidebar.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;{meaning}")

st.sidebar.markdown("**Street safety colours**")
st.sidebar.markdown("🟩 safe &nbsp; 🟧 be careful &nbsp; 🟥 risky")

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
centre = G.nodes["Hafeez road bend"]["pos"]
fmap = folium.Map(location=centre, zoom_start=16, tiles="OpenStreetMap")
for u, v, d in G.edges(data=True):               # every street, thin, coloured by safety
    folium.PolyLine(d["shape"], color=SAFETY_COLOURS[d["fuzzy_word"]], weight=4, opacity=0.6,
                    tooltip=f"{d['segment_id']}: {d['fuzzy_word']} at {slot_label} "
                            f"({d['night_phrase']})").add_to(fmap)

# Draw only the ticked routes. The widest goes first, so when two routes share
# a street you still see both colours (a thin line on top of a wider one).
for mode in sorted(selected, key=lambda m: -ROUTE_STYLE[m][2]):
    colour, _, width, _ = ROUTE_STYLE[mode]
    path, info = routes[mode]
    shape = []
    for a, b in zip(path, path[1:]):
        pts = list(G[a][b]["shape"])
        if pts and pts[0] != G.nodes[a]["pos"] and pts[-1] == G.nodes[a]["pos"]:
            pts = pts[::-1]                       # make the street run in walking direction
        shape += pts
    folium.PolyLine(shape, color=colour, weight=width, opacity=0.9,
                    tooltip=f"{mode}: {info['length_m']} m, average risk {info['avg_risk']:.2f}").add_to(fmap)
folium.Marker(G.nodes[start]["pos"], tooltip="Start", icon=folium.Icon(color="green", icon="play")).add_to(fmap)
folium.Marker(G.nodes[goal]["pos"], tooltip="Destination", icon=folium.Icon(color="red", icon="flag")).add_to(fmap)

left, right = st.columns([3, 2])
with left:
    st_folium(fmap, height=580, use_container_width=True, returned_objects=[])
    st.caption("Streets follow OpenStreetMap. Thin lines: 🟩 safe, 🟧 be careful, 🟥 risky. "
               "Thick lines: ⬛ fastest, 🟦 balanced, 🟪 safety-first.")

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
        st.success(f"{', '.join(s.capitalize() for s in same)} = fastest here: the shortest way "
                   "is already through safe streets, so there is no reason to detour.")
    phrases = segment_risk.drop_duplicates("segment_id").set_index("segment_id")["night_phrase"]
    for m in selected:
        info = routes[m][1]
        st.markdown(f"**{ROUTE_STYLE[m][1]} {m.capitalize()}:** " + " → ".join(info["segments"]))
        avoided = [s for s in fastest["segments"]          # only mention streets worth avoiding
                   if s not in info["segments"] and phrases[s] != "safe all evening"]
        if m != "fastest" and avoided:
            st.caption("Avoids " + ", ".join(f"{s} ({phrases[s]})" for s in avoided)
                       + f" for {info['length_m'] - fastest['length_m']} m extra walking.")
        worst_id, worst_risk, worst_phrase = info["worst_segment"]
        st.caption(f"Riskiest stretch: {worst_id}, {worst_phrase} (risk {worst_risk:.2f}).")

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
