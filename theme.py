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
