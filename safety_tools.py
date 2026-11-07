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


# ---------------------------------------------------------------------------
# 1. Panic button
# ---------------------------------------------------------------------------
@st.dialog("🆘 Panic button (demo)")
def _panic_dialog(location):
    st.error("In a real app, this would happen immediately:")
    for number, name in EMERGENCY_NUMBERS:
        st.markdown(f"📞 **{number}**: {name}")
    st.markdown(f"📍 Your last location **{_location_text(location)}** sent to: "
                + ", ".join(_contacts()))
    st.caption("Simulation only: nobody was actually called or messaged.")


def panic_button(location):
    if st.button("🆘 PANIC", type="primary", use_container_width=True):
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
        st.success("Hammy: Okay, glad you're fine! I'll keep an eye on your route. 💙")
        if st.button("Close", key="close_ok"):
            _reset_checkin()
            st.rerun()
        return

    st.warning("🐹 **Hammy:** You've gone off your route. **Are you okay?**")
    c1, c2 = st.columns(2)
    if c1.button("✅ I'm okay", key="ok"):
        state["answered"] = True
        st.rerun(scope="fragment")
    if c2.button("🆘 I need help", key="help"):
        state["started"] -= 2 * wait              # jump straight to the last step
        st.rerun(scope="fragment")

    if elapsed < wait:
        st.progress(elapsed / wait, text=f"Waiting for an answer: {int(wait - elapsed)} s left")
    if elapsed >= wait:
        st.error(f"⚠️ No answer. Trusted contacts ({', '.join(_contacts())}) alerted with your "
                 f"last known location: {_location_text(location)}")
    if wait <= elapsed < 2 * wait:
        st.progress((elapsed - wait) / wait,
                    text=f"Still no answer: alerting the Women Safety app in {int(2 * wait - elapsed)} s")
    if elapsed >= 2 * wait:
        st.error(f"🚨 PSCA Women Safety app alerted (Punjab Safe Cities) with your last known "
                 f"location: {_location_text(location)}")
        st.caption("Simulation only: no real alert was sent.")
        if st.button("End demo", key="end_checkin"):
            _reset_checkin()
            st.rerun()


def start_checkin(fast):
    st.session_state.checkin = {"started": time.time(), "wait": 10 if fast else 60}


# ---------------------------------------------------------------------------
# 3. Low-battery warnings
# ---------------------------------------------------------------------------
def battery_warning(battery, location):
    if battery <= 15:
        st.error(f"🔋 **{battery}%**: Your last location ({_location_text(location)}) was "
                 f"shared with {', '.join(_contacts())} automatically. Once your phone dies, "
                 "Safe Route **can't help you**. Please charge it or tell someone where you are.")
    elif battery <= 30:
        st.warning(f"🔋 **{battery}%**: Hammy says: please charge your phone soon. "
                   "If it dies, the app can't watch over your route.")
