"""
Safe Route Lahore - colours, fonts and the sky banner
=====================================================

The look: warm cream background, rose-pink and violet accents, a rounded
friendly heading font (Fredoka) and an easy-to-read body font (Nunito).

The banner at the top shows the sky at the chosen time of night:
  6 PM  -> sunset (orange and pink)
  9 PM  -> dusk (pink and violet, first stars)
  11 PM -> night (deep blue, moon and twinkling stars)
"""

import random

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Nunito:wght@500;700;800&display=swap');

html, body, .stApp, .stMarkdown, p, label, li, input, textarea { font-family: "Nunito", system-ui, sans-serif; }
h1, h2, h3, h4, h5, [data-testid="stHeading"] *, .stTabs button p { font-family: "Fredoka", "Nunito", sans-serif !important; }
.stApp { background:
  radial-gradient(1200px 500px at 110% -10%, #ffe1ec 0%, transparent 60%),
  radial-gradient(900px 500px at -10% 110%, #e9e3ff 0%, transparent 60%), #fff8f1; }

/* Nothing fades or goes grey while the app thinks. */
[data-stale="true"], .stale-element { opacity: 1 !important; transition: none !important; }

/* sidebar */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #fff1ea 0%, #f6edff 100%); border-right: none; }
[data-testid="stSidebar"] [data-testid="stHeading"] h1 { font-size: 1.55rem; }
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
[data-testid="stSidebar"] .stTextInput input { border-radius: 14px; border: 2px solid #f3d7e3; background: #fff; }

/* buttons: rounded and bouncy */
.stButton > button { border-radius: 999px; font-weight: 800; border: 2px solid #f3d7e3; transition: transform .12s; }
.stButton > button:hover { transform: translateY(-1px); }
.stButton > button[kind="primary"] { background: linear-gradient(135deg, #ff4f7b, #ff7a59); border: none;
  box-shadow: 0 8px 18px rgba(255, 79, 123, .35); }

/* tabs as soft pills */
.stTabs [role="tablist"] { gap: 10px; border-bottom: none !important; box-shadow: none !important; }
.stTabs [role="tab"] { background: #fff; border-radius: 999px !important; padding: 8px 20px !important; height: auto !important;
  box-shadow: 0 2px 10px rgba(124, 92, 255, .12); border: none !important; }
.stTabs [role="tab"] p { font-size: 1rem !important; font-family: "Fredoka", sans-serif !important; }
.stTabs [role="tab"][aria-selected="true"] { background: linear-gradient(135deg, #7c5cff, #ff4f7b); }
.stTabs [role="tab"][aria-selected="true"] p { color: #fff !important; }
.stTabs [role="tab"]::after, .stTabs [role="tab"]::before { display: none !important; }

/* cards for alerts and tables */
[data-testid="stAlert"], [data-testid="stDataFrame"], [data-testid="stExpander"] { border-radius: 16px; }
/* Everything fits on one screen: small top gap, no header bar, no page scroll. */
.block-container { padding-top: 0.8rem !important; padding-bottom: 0 !important; }
[data-testid="stHeader"] { display: none; }
.stTabs [role="tabpanel"] { padding-top: 0.6rem; }
[data-testid="stMainBlockContainer"] > div { gap: 0.6rem; }

/* the sky banner */
.sky { position: relative; overflow: hidden; border-radius: 22px; padding: 12px 22px; margin-bottom: 4px; color: #fff;
       display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
       box-shadow: 0 14px 34px rgba(124, 92, 255, .25); }
.sky h1 { font-family: "Fredoka", sans-serif !important; margin: 0; padding: 0; font-size: 1.55rem; color: #fff; line-height: 1.15; white-space: nowrap; }
.sky p { margin: 0; font-size: .95rem; opacity: .95; flex: 1; min-width: 200px; }
.sky .chip { display: inline-block; margin-right: 44px; background: rgba(255,255,255,.22); border-radius: 999px;
             padding: 4px 12px; font-weight: 800; font-size: .85rem; backdrop-filter: blur(4px); }
.sky .moon { position: absolute; right: 18px; top: 50%; transform: translateY(-50%); font-size: 32px; filter: drop-shadow(0 0 18px rgba(255,236,170,.9)); }
.sky .star { position: absolute; width: 3px; height: 3px; border-radius: 50%; background: #fff;
             animation: twinkle 2.4s ease-in-out infinite alternate; }
@keyframes twinkle { from { opacity: .15; transform: scale(.6); } to { opacity: 1; transform: scale(1.2); } }
.sky.s6pm  { background: linear-gradient(120deg, #ff9a5a 0%, #ff6f91 55%, #c86bfa 100%); }
.sky.s9pm  { background: linear-gradient(120deg, #ff6f91 0%, #a35cff 55%, #5b5bf0 100%); }
.sky.s11pm { background: linear-gradient(120deg, #3b3aa8 0%, #5b3fd6 50%, #b04fd8 100%); }
@media (max-width: 640px) { .sky h1 { font-size: 1.6rem; } .sky .moon { font-size: 26px; right: 12px; } .sky .chip { display: none; } }

/* ---------- serious, trustworthy safety UI ---------- */
:root { --navy: #1f2550; --navy-soft: #4a4f7a; --line: #ece4f3; --sos: #d92d4b; --teal: #0f9d8a; --amber: #c97a00; }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top: 1rem; }
[data-testid="stSidebarHeader"] { display: none; }
[data-testid="stSidebar"] { min-width: 330px !important; max-width: 330px !important; }
[class*="st-key-card_"] [data-testid="stMarkdownContainer"] p { margin-bottom: 0; }
[class*="st-key-card_"] .stElementContainer:has(.card-h) { margin-bottom: 2px; }
.brand { display: flex; align-items: center; gap: 10px; margin: 0 0 12px; }
.brand .logo { width: 46px; height: 46px; border-radius: 14px; flex: none; box-shadow: 0 6px 16px rgba(255, 79, 123, .35); }
.brand .name { font: 700 1.25rem "Fredoka", sans-serif; color: var(--navy); line-height: 1.1; }
.brand .tag { font-size: .78rem; color: var(--navy-soft); font-weight: 700; }

[class*="st-key-card_"] { background: #fff; border: 1px solid var(--line); border-radius: 18px; padding: 14px 16px 12px;
  box-shadow: 0 4px 14px rgba(31, 37, 80, .06); gap: .55rem; }
.card-h { font: 600 1.02rem "Fredoka", sans-serif; color: var(--navy); margin-bottom: 8px; }
.card-p { font-size: .82rem; color: var(--navy-soft); line-height: 1.4; padding-bottom: 6px; }
[class*="st-key-card_"] label p { font-weight: 800 !important; color: var(--navy) !important; font-size: .85rem !important; }
.st-key-card_sos { border: 1.5px solid #f4c3cd; background: linear-gradient(180deg, #fff 0%, #fff6f7 100%); }
.card-h.sos { color: var(--sos); display: flex; align-items: center; gap: 8px; letter-spacing: .02em; }
.card-h.sos::before { content: ""; width: 10px; height: 10px; border-radius: 50%; background: var(--sos);
  box-shadow: 0 0 0 4px rgba(217, 45, 75, .18); }
.st-key-panic button { background: var(--sos) !important; border: none !important; border-radius: 14px !important;
  padding: .7rem 0 !important; box-shadow: 0 8px 18px rgba(217, 45, 75, .35) !important; }
.st-key-panic button p { font-weight: 800 !important; font-size: 1rem !important; letter-spacing: .02em; }
.hotlines { display: flex; flex-wrap: wrap; gap: 6px; }
.hotlines span { background: #fff; border: 1px solid #f4c3cd; border-radius: 10px; padding: 3px 8px; font-size: .78rem; color: var(--navy); }
.hotlines b { color: var(--sos); }
.side-foot { font-size: .75rem; color: var(--navy-soft); margin-top: 10px; line-height: 1.4; }

/* alert cards: calm, clear and serious */
.alert { display: flex; gap: 12px; align-items: flex-start; background: #fff; border-radius: 16px; padding: 12px 16px;
  border: 1px solid var(--line); border-left: 6px solid var(--teal); box-shadow: 0 4px 14px rgba(31, 37, 80, .07); margin-bottom: 4px; }
.alert .al-icon { flex: none; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-weight: 800; color: #fff; background: var(--teal); font-size: 16px; }
.alert .al-title { font: 600 1rem "Fredoka", sans-serif; color: var(--navy); }
.alert .al-body { font-size: .88rem; color: var(--navy-soft); line-height: 1.45; }
.alert .al-foot { font-size: .75rem; color: #8a86a3; margin-top: 4px; }
.alert.caution { border-left-color: var(--amber); } .alert.caution .al-icon { background: #f5a524; }
.alert.urgent { border-left-color: var(--sos); background: #fff8f9; } .alert.urgent .al-icon { background: var(--sos); }
.steps { list-style: none; padding: 0; margin: 6px 0; }
.steps li { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--line); color: var(--navy); font-size: .92rem; flex-wrap: wrap; }
.steps .num { min-width: 46px; text-align: center; font-weight: 800; color: #fff; background: var(--sos); border-radius: 8px; padding: 2px 6px; }
.steps .ok { margin-left: auto; color: var(--teal); font-weight: 800; font-size: .8rem; }
.calm-note { background: #eefaf7; color: #0b6b5e; border-radius: 12px; padding: 10px 12px; font-size: .88rem; font-weight: 700; }

.st-key-alerts { position: fixed; top: 14px; right: 22px; width: min(470px, calc(100vw - 32px)); z-index: 999990; gap: .5rem; }
.st-key-alerts:has(.alert) { background: #fff; border-radius: 20px; padding: 10px 12px 12px;
  box-shadow: 0 18px 44px rgba(31, 37, 80, .25); border: 1px solid var(--line); }
.st-key-alerts .alert { box-shadow: none; border-top: none; border-right: none; border-bottom: none; margin: 0; }
.st-key-alerts button[kind="primary"] { background: var(--sos) !important; box-shadow: 0 8px 18px rgba(217, 45, 75, .3) !important; }
.st-key-alerts button[kind="secondary"] { background: #fff; }
.st-key-alerts [data-testid="stProgress"] div[role="progressbar"] > div > div { background: var(--sos); }

/* route summary strip above the map */
.strip { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 2px; }
.stat { display: flex; gap: 10px; align-items: center; background: #fff; border: 1px solid var(--line); border-radius: 16px;
  padding: 9px 12px; box-shadow: 0 4px 14px rgba(31, 37, 80, .05); min-width: 0; }
.stat .ic { flex: none; width: 36px; height: 36px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
.stat .k { font-size: .72rem; font-weight: 800; color: var(--navy-soft); text-transform: uppercase; letter-spacing: .04em; }
.stat .v { font: 600 1.02rem "Fredoka", sans-serif; color: var(--navy); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stat .s { font-size: .74rem; color: var(--navy-soft); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stat > div:last-child { min-width: 0; }
@media (max-width: 900px) { .strip { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
"""

SKY = {
    "6 PM": ("s6pm", "🌇", 0, "Sunset in Gulberg. Shops are open and streets are busy."),
    "9 PM": ("s9pm", "🌆", 10, "Dusk. Some lanes get quieter, the main roads stay bright."),
    "11 PM": ("s11pm", "🌙", 26, "Late night. This is when the safer route matters most."),
}


def apply_theme():
    st.markdown(CSS, unsafe_allow_html=True)


def sky_banner(slot_label):
    cls, icon, n_stars, line = SKY[slot_label]
    rng = random.Random(7)                      # same stars every time (no jumping around)
    stars = "".join(
        f'<span class="star" style="left:{rng.uniform(2, 92):.1f}%;top:{rng.uniform(6, 90):.1f}%;'
        f'animation-delay:{rng.uniform(0, 2.4):.2f}s"></span>'
        for _ in range(n_stars))
    st.markdown(
        f'<div class="sky {cls}">{stars}<div class="moon">{icon}</div>'
        f'<h1>Safe Route Lahore</h1>'
        f'<p>Find the <b>safer</b> way home, apa. 💛 {line}</p>'
        f'<span class="chip">📍 Gulberg III pilot · {slot_label} · synthetic data</span></div>',
        unsafe_allow_html=True)


def _icon_uri():
    """The app icon (an "S" drawn as a road on pink) as an inline image."""
    import base64
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.svg")
    with open(path, "rb") as f:
        return "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode()


def sidebar_brand():
    st.markdown(f'<div class="brand"><img class="logo" src="{_icon_uri()}" alt="Safe Route logo"><div>'
                '<div class="name">Safe Route Lahore</div>'
                '<div class="tag">Your companion for safer night walks</div></div></div>', unsafe_allow_html=True)


def summary_strip(routes, same_place, slot_label, contacts, battery, worst=None):
    """Four small cards above the map: the key facts about tonight's walk."""
    if same_place:
        cards = [("🧭", "#efeaff", "Plan your walk", "Pick two places", "From and To are the same")]
    else:
        safe, fast = routes["safety-first"]["info"], routes["fastest"]["info"]
        extra = safe["length_m"] - fast["length_m"]
        cards = [
            ("🛡️", "#efeaff", "Safety-first route", f"{safe['length_m'] / 1000:.2f} km",
             f"+{extra} m vs fastest" if extra > 0 else "Same as the fastest way"),
            ("📉", "#e6f7f3", f"Risk at {slot_label}", f"{safe['avg_risk']:.2f} average",
             f"Fastest way: {fast['avg_risk']:.2f} (lower is safer)"),
            ("⚠️", "#fff3dc", "Take care on", (worst[0][0].upper() + worst[0][1:]) if worst else "-", worst[1] if worst else ""),
        ]
    who = ", ".join(contacts) if contacts else "No contacts yet"
    cards.append(("👥", "#ffe8ee", "Watching over you", who, f"Phone battery {battery}%"))
    html = "".join(f'<div class="stat"><div class="ic" style="background:{bg}">{ic}</div><div>'
                   f'<div class="k">{k}</div><div class="v">{v}</div><div class="s">{sub}</div></div></div>'
                   for ic, bg, k, v, sub in cards)
    st.markdown(f'<div class="strip">{html}</div>', unsafe_allow_html=True)
