"""
Safe Route Lahore - Step 6: the web app (what you show in the live demo)
========================================================================

Run on your laptop:   streamlit run app.py
Live version:         deployed on share.streamlit.io from the GitHub repo.

WHAT THE USER DOES:
  1. Picks where they start and where they're going.
  2. Picks the time (6, 9 or 11 PM).
     (or clicks any dot on the map and presses "Start here" / "Go here").
  3. Taps the route pills in the map's corner to show or hide each option:
        Fastest       (grey)   - shortest distance, ignores safety
        Balanced      (blue)   - a less-safe street counts as up to 4x longer
        Safety-first  (purple) - a less-safe street counts as up to 11x longer

The map is a custom component (map_component.py + map_frontend/) that stays
loaded the whole time: changing From / To / time only sends it new data, and
the routes GROW from the place picked last. No black flash, no reload.
"""

import pandas as pd
import streamlit as st

from road_graph import build_graph
from routing import MODES, a_star, attach_risk, describe_route
from hammy_widget import hammy_widget
from map_component import safer_map, walk_notes
from safety_tools import battery_warning, checkin_panel, panic_button, start_checkin
from theme import apply_theme, sky_banner

st.set_page_config(page_title="Safe Route Lahore", page_icon="🛡️", layout="wide")
apply_theme()

# Each route option has its own colour and line width.
ROUTE_STYLE = {
    #  mode:          (colour,    emoji, line width)
    "fastest":       ("#8a8fa3", "⬜", 9),
    "balanced":      ("#2e8bff", "🟦", 6),
    "safety-first":  ("#9b4dff", "🟪", 4),
}
SLOT_NAMES = {"6 PM": "6pm", "9 PM": "9pm", "11 PM": "11pm"}


@st.cache_data
def load_risk():
    return pd.read_csv("segment_risk.csv")


# ---------------- sidebar: the user's choices ----------------
nodes = sorted(build_graph().nodes)
st.session_state.setdefault("from_sel", "Sir Syed / first side road")
st.session_state.setdefault("to_sel", "Tehzeeb Bakers (MM Alam)")

# A click on the map ("Start here" / "Go here") arrives as the map's value.
# Apply it BEFORE the dropdowns are drawn, so they show the new place.
click = st.session_state.get("safer_map")
if click and click.get("nonce") != st.session_state.get("last_click"):
    st.session_state.last_click = click["nonce"]
    st.session_state["from_sel" if click["action"] == "from" else "to_sel"] = click["place"]


def swap_places():
    st.session_state.from_sel, st.session_state.to_sel = st.session_state.to_sel, st.session_state.from_sel


st.sidebar.title("🛡️ Safe Route Lahore")
st.sidebar.caption("Pilot area: Gulberg III. Prototype using SYNTHETIC data. "
                   "Tip: you can also click any dot on the map.")
start = st.sidebar.selectbox("🚶‍♀️ From", nodes, key="from_sel")
st.sidebar.button("⇅ Swap", on_click=swap_places)
goal = st.sidebar.selectbox("🏠 To", nodes, key="to_sel")
slot_label = st.sidebar.radio("🌙 Time of night", list(SLOT_NAMES), index=2, horizontal=True)

# Which end should the routes grow from? The one the user changed last.
prev = st.session_state.get("prev_pair")
if prev and goal != prev[1] and start == prev[0]:
    st.session_state.grow_from = "goal"
elif prev and start != prev[0]:
    st.session_state.grow_from = "start"
st.session_state.prev_pair = (start, goal)
grow_from = st.session_state.get("grow_from", "start")

segment_risk = load_risk()
sky_banner(slot_label)


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
            # Make the street run in walking direction: the end nearest to junction
            # `a` goes first. (Comparing exact points failed because of rounding,
            # which drew streets backwards and made the line double back on itself.)
            ax, ay = G.nodes[a]["pos"]
            near = lambda p: (p[0] - ax) ** 2 + (p[1] - ay) ** 2
            if near(pts[-1]) < near(pts[0]):
                pts = pts[::-1]
            if shape and pts and near(pts[0]) < 1e-9 and shape[-1] == pts[0]:
                pts = pts[1:]                         # don't repeat the shared junction point
            shape += [tuple(p) for p in pts]
        # Remove "spurs" (A -> B -> back to A): OSM sometimes has a tiny dead-end
        # bit, which would look like a doubled line on the map.
        clean = []
        for pt in shape:
            if len(clean) >= 2 and clean[-2] == pt:
                clean.pop()
            else:
                clean.append(pt)
        out[mode] = {"path": path, "info": info, "shape": clean}
    notes = walk_notes(G, out["safety-first"]["path"], slot.upper().replace("PM", " PM"))
    return out, notes


@st.cache_data
def map_basics():
    """Things the map needs once: every junction and every street shape."""
    G = build_graph()
    places = [{"name": n, "pos": list(G.nodes[n]["pos"])} for n in sorted(G.nodes)]
    streets = [[list(p) for p in d["shape"]] for *_, d in G.edges(data=True)]
    return places, streets, list(G.nodes["Hafeez road bend"]["pos"])


places, streets, centre = map_basics()
pos = {p["name"]: p["pos"] for p in places}
same_place = start == goal
if same_place:
    routes, notes = {m: {"path": [start], "info": {"length_m": 0, "avg_risk": 0.0, "segments": []},
                         "shape": []} for m in MODES}, []
else:
    routes, notes = compute_routes(start, goal, SLOT_NAMES[slot_label])

# ---------------- safety tools (simulated) ----------------
# "Last known location" for the demo: halfway along the balanced route.
balanced_shape = routes["balanced"]["shape"]
last_location = tuple(balanced_shape[len(balanced_shape) // 2]) if balanced_shape else tuple(pos[start])

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

# Alerts live in one fixed box, so showing or hiding one never moves (or
# reloads) the map below it.
with st.container():
    battery_warning(battery, last_location)
    checkin_panel(last_location)

# ---------------- map ----------------
map_data = {
    "routes": [{"mode": m, "label": m.capitalize(), "colour": ROUTE_STYLE[m][0], "width": ROUTE_STYLE[m][2],
                "length_m": routes[m]["info"]["length_m"], "avg_risk": routes[m]["info"]["avg_risk"], "shape": [list(p) for p in routes[m]["shape"]]}
               for m in MODES],
    "start": {"name": start, "pos": pos[start]},
    "goal": {"name": goal, "pos": pos[goal]},
    "grow_from": grow_from,
    "slot": slot_label,
    "centre": centre,
    "places": places,
    "streets": streets,
    "walk_notes": notes,
    "contacts": st.session_state.contacts,
    "message": "Pick two different places 🙂" if same_place else "",
}

# Two tabs: the map with Hammy beside it, and the route details on their own.
map_tab, details_tab = st.tabs(["🗺️ Map & Hammy", "📋 Route details"])

with map_tab:
    left, right = st.columns([3, 2])
    with left:
        safer_map(map_data, height=600)
        st.caption("Tap the coloured pills to show or hide routes. Press 🌙 **Walk me home** for a little surprise.")
    with right:
        hammy_widget()

# ---------------- route details ----------------
with details_tab:
    st.subheader(f"Routes at {slot_label}")
    if same_place:
        st.info("Pick two different places.")
    selected = list(ROUTE_STYLE)
    fastest = routes["fastest"]["info"]
    table = pd.DataFrame([{
        "Route": f"{ROUTE_STYLE[m][1]} {m.capitalize()}",
        "Distance (m)": routes[m]["info"]["length_m"],
        "Extra vs fastest": f"+{routes[m]['info']['length_m'] - fastest['length_m']} m",
        "Average risk (0-1)": f"{routes[m]['info']['avg_risk']:.2f}",
    } for m in selected])
    st.dataframe(table, hide_index=True, use_container_width=True)

    # Two options can pick the SAME route. That is expected, not a bug: if the
    # balanced route already avoids the less-safe streets, a bigger safety
    # weight has no safer detour left to choose (true for 88% of pairs at 11 PM).
    for i, m in enumerate(selected):
        for earlier in selected[:i]:
            if routes[m]["path"] == routes[earlier]["path"]:
                st.info(f"{m.capitalize()} picks the same route as {earlier.capitalize()} here: "
                        "there is no safer detour nearby.")
                break
    for m in selected:
        st.markdown(f"**{ROUTE_STYLE[m][1]} {m.capitalize()}:** " + " → ".join(routes[m]["info"]["segments"]))

    with st.expander("How does this work?", expanded=True):
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
