"""
Safe Route Lahore - Step 7: safety tools (ALL SIMULATED, for the demo)
======================================================================

Nothing here calls anyone, sends any SMS or contacts the police. Every
"alert" is a pop-up on the screen that shows WHAT a real app would do.

Three tools:
  1. Panic button: shows the emergency numbers a real app would dial:
       15   Police (Pakistan)
       1122 Rescue / ambulance (Punjab)
       1043 Punjab Women's Helpline
     and "shares" the user's last known location with trusted contacts.

  2. "Are you okay?" check-in, for when the user goes off her route:
       step 1  Hammy asks "Are you okay?"     (she has 60 seconds to answer)
       step 2  no answer -> alert her trusted contacts with her last location
       step 3  still no answer -> alert the PSCA Women Safety app (Punjab
               Safe Cities) with her last known location
     We send it to the Women Safety app instead of regular police on purpose:
     it is built for women's emergencies.

  3. Low-battery warnings: a dead phone means the app can't help her, so:
       30% or less -> gentle reminder to charge
       15% or less -> automatically share her last location with trusted contacts

HOW THE TIMER WORKS (for Dr. Sidra):
  Streamlit normally re-runs the whole page on every click. The countdown is
  inside an @st.fragment that re-runs ONLY ITSELF every second, so the map
  doesn't reload while the clock ticks.
"""

import time

import streamlit as st

EMERGENCY_NUMBERS = [
    ("15", "Police"),
    ("1122", "Rescue / ambulance"),
    ("1043", "Punjab Women's Helpline"),
]


def _contacts():
    """The trusted contacts typed into the sidebar (demo only, never saved)."""
    return st.session_state.get("contacts") or ["Ammi", "Best friend"]


def _location_text(location):
    lat, lon = location
    return f"{lat:.5f}, {lon:.5f} (Gulberg III)"


def alert_card(level, icon, title, body, foot=""):
    """A calm, serious alert card. level: 'calm' (teal), 'caution' (amber) or 'urgent' (red).
    Safety messages use this instead of the playful style, so they read as reliable."""
    foot_html = f'<div class="al-foot">{foot}</div>' if foot else ""
    st.markdown(f'<div class="alert {level}"><div class="al-icon">{icon}</div>'
                f'<div class="al-text"><div class="al-title">{title}</div>'
                f'<div class="al-body">{body}</div>{foot_html}</div></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 1. Panic button
# ---------------------------------------------------------------------------
@st.dialog("Emergency alert", width="small")
def _panic_dialog(location):
    alert_card("urgent", "🆘", "Help is being alerted",
               "In the real app, all of this happens the moment you press the button.")
    steps = "".join(f'<li><span class="num">{number}</span> {name} <span class="ok">calling…</span></li>'
                    for number, name in EMERGENCY_NUMBERS)
    st.markdown(f'<ul class="steps">{steps}<li><span class="num">📍</span> Live location sent to '
                f'<b>{", ".join(_contacts())}</b><br><small>{_location_text(location)}</small></li></ul>',
                unsafe_allow_html=True)
    st.markdown('<div class="calm-note">Stay where it is lit and people are around. '
                'Keep the call open. Help knows where you are.</div>', unsafe_allow_html=True)
    st.caption("Simulation only: nobody was actually called or messaged.")


def panic_button(location):
    if st.button("🆘  PANIC: get help now", type="primary", use_container_width=True, key="panic"):
        _panic_dialog(location)


# ---------------------------------------------------------------------------
# 2. "Are you okay?" check-in
# ---------------------------------------------------------------------------
def _reset_checkin():
    st.session_state.checkin = None


@st.fragment(run_every=1)
def checkin_panel(location):
    """Shows the check-in conversation and its countdown. Re-runs every second."""
    state = st.session_state.get("checkin")
    if state is None:
        return
    wait = state["wait"]                          # seconds to answer each step
    elapsed = time.time() - state["started"]

    if state.get("answered"):
        alert_card("calm", "✓", "Glad you're okay",
                   "Hammy keeps watching your route. Nobody was alerted.")
        if st.button("Close", key="close_ok"):
            _reset_checkin()
            st.rerun()
        return

    if elapsed < wait:
        alert_card("caution", "!", "You've left your route. Are you okay?",
                   f"If you don't answer in <b>{int(wait - elapsed)} s</b>, your trusted contacts "
                   f"({', '.join(_contacts())}) get your last location.")
        st.progress(elapsed / wait)
    elif elapsed < 2 * wait:
        alert_card("urgent", "📍", "No answer: trusted contacts alerted",
                   f"{', '.join(_contacts())} received your last known location: {_location_text(location)}. "
                   f"The PSCA Women Safety app is alerted in <b>{int(2 * wait - elapsed)} s</b>.")
        st.progress((elapsed - wait) / wait)
    else:
        alert_card("urgent", "🚨", "PSCA Women Safety app alerted",
                   f"Punjab Safe Cities has your last known location: {_location_text(location)}.",
                   "Simulation only: no real alert was sent.")
    c1, c2, c3 = st.columns([1, 1, 1])
    if elapsed < 2 * wait:
        if c1.button("✓ I'm okay", key="ok", use_container_width=True):
            state["answered"] = True
            st.rerun(scope="fragment")
        if c2.button("🆘 I need help", key="help", type="primary", use_container_width=True):
            state["started"] -= 2 * wait              # jump straight to the last step
            st.rerun(scope="fragment")
    elif c1.button("End demo", key="end_checkin", use_container_width=True):
        _reset_checkin()
        st.rerun()


def start_checkin(fast):
    st.session_state.checkin = {"started": time.time(), "wait": 10 if fast else 60}


# ---------------------------------------------------------------------------
# 3. Low-battery warnings
# ---------------------------------------------------------------------------
def battery_warning(battery, location):
    if battery <= 15:
        alert_card("urgent", "🔋", f"Battery {battery}%: location shared",
                   f"Your last location ({_location_text(location)}) was shared with "
                   f"{', '.join(_contacts())} automatically. Once your phone dies, Safe Route can't help, "
                   "so please charge it or tell someone where you are.")
    elif battery <= 30:
        alert_card("caution", "🔋", f"Battery {battery}%: please charge soon",
                   "If your phone dies, the app can't watch over your route or alert anyone.")
