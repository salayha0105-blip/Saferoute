"""
Safe Route Lahore - SIMULATED survey of 50 women in Gulberg III
================================================================

!!! THIS IS NOT A REAL SURVEY. NO REAL PERSON ANSWERED IT. !!!

WHAT THIS FILE DOES:
  It makes up the answers that 50 women living or working in Gulberg III
  MIGHT give to our safety questionnaire (survey/questionnaire.md).
  Every row is marked data_source = "SIMULATED".

WHY:
  Dr. Sidra approved generated data for this course project (6 Nov 2026).
  We could not run the real survey in time, so we simulate one. Where public
  research gives a number, we aim close to it (see TARGETS below and
  survey/SIMULATED_SURVEY.md). Everything else is OUR ASSUMPTION and is
  labelled as such.

WHAT WE USE IT FOR:
  A sanity check of our design, NOT training data:
    1. Do the factors women (would) rate as most important match the
       factors our generator and fuzzy rules lean on (lighting, main road
       vs gali, open shops, police)?
    2. Does felt safety drop from 6 PM to 11 PM, and is a gali lower than a
       main road, like in our synthetic street data?

Run:      python simulated_survey.py
Creates:  survey/simulated_survey_responses.csv   (50 rows)
          results/survey_summary.json
          results/survey_factors.png
          results/survey_felt_safety.png
"""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SEED = 7
rng = np.random.default_rng(SEED)
N = 50

# ---------------------------------------------------------------------------
# TARGETS: where each number comes from
# ---------------------------------------------------------------------------
# "source"     = aimed close to a published figure (cited in SIMULATED_SURVEY.md)
# "assumption" = our own guess, no published figure used
TARGETS = {
    # Aurat Foundation, Lahore public-transport study (903 women):
    # 82% faced harassment at stops -> we aim near 80% for "harassed in a
    # public place in the last 12 months".
    "harassed_last_12m": (0.80, "source: Aurat Foundation Lahore study (82% at stops)"),
    # Same study: 98% did not know of any helpline -> few know 1043.
    "knows_1043": (0.05, "source: Aurat Foundation Lahore study (98% unaware of helplines)"),
    # No published figure found for the PSCA Women Safety app.
    "knows_psca_app": (0.15, "assumption"),
}

# Felt safety, 1 (very unsafe) to 5 (very safe), average we aim for.
# CERP: about 30% of Lahore women call walking in their own neighbourhood
# "very unsafe" -> a gali at 9 PM gets roughly 30% "1" answers.
# The other averages are our assumption: lower later, lower in a gali.
FELT_SAFETY_MEAN = {
    ("main_road", "6pm"): 3.9, ("main_road", "9pm"): 3.3, ("main_road", "11pm"): 2.5,
    ("gali", "6pm"): 2.9,      ("gali", "9pm"): 2.1,      ("gali", "11pm"): 1.5,
}

# "How much does this make you feel safer?" 1 (not at all) to 5 (a lot).
# Our assumption, informed by Safetipin's audit parameters (lighting,
# openness, visibility, security, walk path) and the order in which
# women's-safety audits usually report concerns (lighting first).
FACTOR_MEAN = {
    "Good street lighting": 4.6,
    "Main road (not a gali)": 4.3,
    "Shops open": 4.1,
    "Police nearby": 4.0,
    "Safe City camera": 3.8,
    "Security guards": 3.6,
    "Footpath": 3.4,
    "Private CCTV": 3.2,
    "Hospital nearby": 2.9,
}


def likert(mean, offset, sd=0.8):
    """One 1-5 answer: the target mean, plus this person's own outlook
    (offset), plus a little noise, rounded and kept inside 1..5."""
    return int(np.clip(round(mean + offset + rng.normal(0, sd)), 1, 5))


def make_respondent(i):
    row = {
        "respondent_id": f"S{i:02d}",
        "data_source": "SIMULATED",
        "age_group": rng.choice(["18-24", "25-34", "35-44", "45+"], p=[0.40, 0.30, 0.18, 0.12]),
        "occupation": rng.choice(["student", "working", "homemaker", "other"], p=[0.40, 0.35, 0.20, 0.05]),
        "walks_after_dark": rng.choice(["never", "sometimes", "often"], p=[0.25, 0.55, 0.20]),
    }
    worry = rng.normal(0, 0.5)          # some people feel safer in general, some less
    for (place, slot), mean in FELT_SAFETY_MEAN.items():
        row[f"felt_{place}_{slot}"] = likert(mean, -worry)
    for factor, mean in FACTOR_MEAN.items():
        row[f"factor: {factor}"] = likert(mean, 0.3 * worry, sd=0.7)
    row["harassed_last_12m"] = int(rng.random() < TARGETS["harassed_last_12m"][0])
    row["knows_1043"] = int(rng.random() < TARGETS["knows_1043"][0])
    row["knows_psca_app"] = int(rng.random() < TARGETS["knows_psca_app"][0])
    row["would_use_app_1to5"] = likert(4.1, 0.2 * worry, sd=0.7)
    return row


def main():
    os.makedirs("survey", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    data = pd.DataFrame([make_respondent(i) for i in range(1, N + 1)])
    data.to_csv("survey/simulated_survey_responses.csv", index=False)

    factor_cols = [c for c in data.columns if c.startswith("factor: ")]
    factors = data[factor_cols].mean().sort_values(ascending=False)
    factors.index = [c.replace("factor: ", "") for c in factors.index]
    felt = {f"{p} {s}": round(float(data[f"felt_{p}_{s}"].mean()), 2) for p, s in FELT_SAFETY_MEAN}

    summary = {
        "WARNING": "SIMULATED survey. No real person answered. For a design sanity check only.",
        "respondents": N,
        "factor_mean_1to5": factors.round(2).to_dict(),
        "felt_safety_mean_1to5": felt,
        "gali_9pm_very_unsafe_share": round(float((data["felt_gali_9pm"] == 1).mean()), 2),
        "harassed_last_12m_share": round(float(data["harassed_last_12m"].mean()), 2),
        "knows_1043_share": round(float(data["knows_1043"].mean()), 2),
        "knows_psca_app_share": round(float(data["knows_psca_app"].mean()), 2),
        "would_use_app_mean_1to5": round(float(data["would_use_app_1to5"].mean()), 2),
        "targets": {k: {"aim": v[0], "basis": v[1]} for k, v in TARGETS.items()},
    }
    with open("results/survey_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Chart 1: what makes women feel safer
    plt.figure(figsize=(7, 4.2))
    factors[::-1].plot.barh(color="#9b4dff")
    plt.xlim(1, 5)
    plt.xlabel("average answer (1 = not at all, 5 = a lot)")
    plt.title("What makes you feel safer? (SIMULATED survey, n = 50)")
    plt.tight_layout()
    plt.savefig("results/survey_factors.png", dpi=130)
    plt.close()

    # Chart 2: felt safety by time, main road vs gali
    plt.figure(figsize=(6, 4))
    for place, colour in [("main_road", "#2e8bff"), ("gali", "#e0567a")]:
        ys = [data[f"felt_{place}_{s}"].mean() for s in ["6pm", "9pm", "11pm"]]
        plt.plot(["6 PM", "9 PM", "11 PM"], ys, marker="o", color=colour,
                 label="main road" if place == "main_road" else "gali")
    plt.ylim(1, 5)
    plt.ylabel("felt safety (1 = very unsafe, 5 = very safe)")
    plt.title("Walking alone (SIMULATED survey, n = 50)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("results/survey_felt_safety.png", dpi=130)
    plt.close()

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
