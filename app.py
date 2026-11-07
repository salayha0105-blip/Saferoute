"""
Safe Route Lahore - Step 6: the web app (what you show in the live demo)
========================================================================

Run on your laptop:   streamlit run app.py
Deploy:               push this folder to GitHub, then "New app" on
                      share.streamlit.io and pick app.py (free).

WHAT THE USER DOES:
  1. Picks where they start and where they're going (junction names).
  2. Picks the time (6, 9 or 11 PM) and a mode (fastest / balanced / safety-first).
  3. Sees the route on a map, coloured streets (green = safe, orange = be
     careful, red = risky), and a plain-English explanation.
"""

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from road_graph import build_graph
from routing import MODES, a_star, attach_risk, describe_route

st.set_page_config(page_title="Safe Route Lahore", page_icon="🛡️", layout="wide")

COLOURS = {"safe": "#2e9e4f", "be careful": "#f0a020", "risky": "#d63b3b"}
SLOT_NAMES = {"6 PM": "6pm", "9 PM": "9pm", "11 PM": "11pm"}


@st.cache_data
def load_risk():
    return pd.read_csv("segment_risk.csv")


# ---------------- sidebar: the user's choices ----------------
st.sidebar.title("🛡️ Safe Route Lahore")
st.sidebar.caption("Pilot area: Gulberg III. Prototype using SYNTHETIC data.")
nodes = sorted(build_graph().nodes)
start = st.sidebar.selectbox("From", nodes, index=nodes.index("Main Blvd / L8"))
goal = st.sidebar.selectbox("To", nodes, index=nodes.index("MM Alam middle"))
slot_label = st.sidebar.radio("Time of night", list(SLOT_NAMES), index=2, horizontal=True)
mode = st.sidebar.radio("Route preference", list(MODES), index=1)

segment_risk = load_risk()
G = attach_risk(build_graph(), segment_risk, SLOT_NAMES[slot_label])

# ---------------- compute routes ----------------
if start == goal:
    st.info("Pick two different places.")
    st.stop()
chosen_path, _ = a_star(G, start, goal, MODES[mode])
chosen = describe_route(G, chosen_path)
fastest_path, _ = a_star(G, start, goal, MODES["fastest"])
fastest = describe_route(G, fastest_path)

# ---------------- map ----------------
centre = G.nodes["Hafeez road bend"]["pos"]
fmap = folium.Map(location=centre, zoom_start=16, tiles="OpenStreetMap")
for u, v, d in G.edges(data=True):                       # every street, coloured by fuzzy word
    folium.PolyLine(d["shape"], color=COLOURS[d["fuzzy_word"]], weight=4, opacity=0.55,
                    tooltip=f"{d['segment_id']}: {d['fuzzy_word']} at {slot_label} "
                            f"({d['night_phrase']})").add_to(fmap)
if mode != "fastest" and fastest_path != chosen_path:    # fastest route as a dashed grey line
    for a, b in zip(fastest_path, fastest_path[1:]):
        folium.PolyLine(G[a][b]["shape"], color="#555", weight=3, dash_array="6 8",
                        tooltip="fastest route (for comparison)").add_to(fmap)
for a, b in zip(chosen_path, chosen_path[1:]):           # the chosen route, thick blue
    folium.PolyLine(G[a][b]["shape"], color="#1f5fd1", weight=8, opacity=0.9).add_to(fmap)
folium.Marker(G.nodes[start]["pos"], tooltip="Start", icon=folium.Icon(color="blue", icon="play")).add_to(fmap)
folium.Marker(G.nodes[goal]["pos"], tooltip="Destination", icon=folium.Icon(color="darkblue", icon="flag")).add_to(fmap)

left, right = st.columns([3, 2])
with left:
    st_folium(fmap, height=560, use_container_width=True, returned_objects=[])
    st.caption("Street positions are approximate (traced from our pilot map). "
               "Green = safe, orange = be careful, red = risky (fuzzy logic labels).")

# ---------------- explanation ----------------
with right:
    st.subheader(f"{mode.capitalize()} route at {slot_label}")
    c1, c2 = st.columns(2)
    c1.metric("Distance", f"{chosen['length_m']} m",
              f"+{chosen['length_m'] - fastest['length_m']} m vs fastest" if mode != "fastest" else None,
              delta_color="off")
    c2.metric("Average risk (0-1)", f"{chosen['avg_risk']:.2f}",
              f"{chosen['avg_risk'] - fastest['avg_risk']:+.2f} vs fastest" if mode != "fastest" else None,
              delta_color="inverse")
    st.write("**Streets:** " + " → ".join(chosen["segments"]))

    avoided = [s for s in fastest["segments"] if s not in chosen["segments"]]
    if mode != "fastest" and avoided:
        phrases = segment_risk.drop_duplicates("segment_id").set_index("segment_id")["night_phrase"]
        st.write("**Why this route?** It avoids " +
                 ", ".join(f"{s} ({phrases[s]})" for s in avoided) +
                 f", for {chosen['length_m'] - fastest['length_m']} m extra walking.")
    elif mode != "fastest":
        st.write("**Why this route?** The fastest route is already the safest one here.")
    worst_id, worst_risk, worst_phrase = chosen["worst_segment"]
    st.write(f"**Riskiest stretch on this route:** {worst_id}, {worst_phrase} (risk {worst_risk:.2f}).")

    with st.expander("How does this work?"):
        st.markdown(
            "- A **decision tree** predicts each street's safety from lighting, open shops, "
            "cameras, crowds and time of night.\n"
            "- **Fuzzy logic** turns the prediction into words like *risky after 9 PM*.\n"
            "- **A\\* search** finds the route with the lowest cost, where "
            "cost = length × (1 + weight × risk). Weight: fastest 0, balanced 3, safety-first 10.\n"
            "- ⚠️ The safety data is **synthetic** (generated by documented rules), approved for this "
            "course prototype. Do not use it for real travel decisions."
        )
