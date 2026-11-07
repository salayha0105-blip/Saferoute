"""
Safe Route Lahore - synthetic data generator
============================================

WHAT THIS FILE DOES (in one sentence):
  It invents realistic night-time safety data for our 43 Gulberg III street
  segments, so we can train a model even though we could not survey real people.

WHY IT IS ALLOWED:
  Dr. Sidra approved generated data on 6 Nov 2026. We must say clearly in the
  README and report that this data is SYNTHETIC (made up by rules).

HOW IT WORKS (5 steps, each one is a function below):
  1. Give every segment a street type (main road, commercial, secondary, lane).
  2. Give every segment its FIXED features (things that don't change at night,
     like "is there a footpath?").
  3. For each night and each time slot, make the CHANGING features
     (lighting, shops open, how busy it is, how many women are around).
  4. Turn those features into a hidden "safety score", then pretend 5 women
     rated the street (each a little differently) and average their ratings.
  5. Turn the average rating into a label: risky / moderate / safe.

Run it with:   python generate_data.py
It creates:    safe_route_synthetic.csv   (43 segments x 3 slots x 10 nights = 1,290 rows)
"""

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------
# A "seed" makes the random numbers come out the same every time we run the
# file. That way anyone (Dr. Sidra too) gets exactly the same dataset.
SEED = 42
rng = np.random.default_rng(SEED)

NIGHTS = 10                    # how many nights we "pretend" to observe
WEEKEND_NIGHTS = {5, 6, 9}     # 3 of the 10 nights are weekends (busier)
SLOTS = ["6pm", "9pm", "11pm"] # the three time slots from our audit sheet
RATERS = 5                     # pretend 5 women rate each street
RATER_NOISE = 0.6              # how much raters disagree with each other

AUDIT_SHEET = "audit-sheet.csv"          # our real list of 43 segments
OUTPUT_FILE = "safe_route_synthetic.csv"


# ---------------------------------------------------------------------------
# STEP 1: street type for every segment
# ---------------------------------------------------------------------------
# The segment_id starts with a road code (MB = Main Boulevard, MM = MM Alam...).
# We use that code to decide the street type. Lanes start with "L".
ROAD_CODE_TO_TYPE = {
    "MB": "main_road",   # Main Boulevard
    "TP": "main_road",   # Tipu Road
    "MM": "commercial",  # MM Alam Road (restaurants, shops)
    "DG": "commercial",  # Dopatta Gali (market)
    "HT": "commercial",  # Hafeez Centre road
    "SS": "secondary",   # Sir Syed Road
    "NJ": "secondary",   # Noor Jahan Road
    "TQ": "secondary",   # Tariq Road
    "CR": "secondary",   # North curved road
}

def get_street_type(segment_id):
    """Look at the letters at the start of the id and return the street type."""
    if segment_id.startswith("L"):        # L1, L2 ... L15 are residential lanes
        return "lane"
    code = segment_id[:2]                 # first two letters, e.g. "MM"
    return ROAD_CODE_TO_TYPE[code]


# ---------------------------------------------------------------------------
# STEP 2: fixed features (same every night)
# ---------------------------------------------------------------------------
# Each number is a CHANCE (probability) that the answer is "yes" (1).
# Example: a lane has a 0.2 chance (20%) of having a footpath.
YES_CHANCE = {
    #                     main   commercial secondary  lane
    "footpath_yn":         (0.90, 0.80,      0.60,      0.20),
    "safe_city_camera_yn": (0.90, 0.70,      0.40,      0.10),
    "police_yn":           (0.40, 0.20,      0.10,      0.02),
    "guards_yn":           (0.50, 0.80,      0.40,      0.50),
    "dead_frontage_yn":    (0.10, 0.05,      0.30,      0.50),
    "isolated_spot_yn":    (0.05, 0.05,      0.20,      0.40),
    "ride_stand_yn":       (0.60, 0.50,      0.20,      0.05),
}
TYPE_ORDER = ["main_road", "commercial", "secondary", "lane"]

# Private CCTV is a COUNT, so we give a (lowest, highest) range instead.
CCTV_RANGE = {
    "main_road": (2, 6),
    "commercial": (4, 10),
    "secondary": (1, 4),
    "lane": (0, 3),
}

def make_fixed_features(street_type):
    """Flip a weighted coin for each yes/no feature, and pick a CCTV count."""
    column = TYPE_ORDER.index(street_type)       # which column of the table to use
    features = {}
    for name, chances in YES_CHANCE.items():
        chance = chances[column]
        # rng.random() gives a number between 0 and 1.
        # If it is below the chance, the answer is yes (1), otherwise no (0).
        features[name] = int(rng.random() < chance)
    low, high = CCTV_RANGE[street_type]
    features["private_cctv_count"] = int(rng.integers(low, high + 1))
    return features


# ---------------------------------------------------------------------------
# STEP 3: changing features (different every slot and every night)
# ---------------------------------------------------------------------------
# These are AVERAGE values. Real nights wiggle around the average, so we add
# randomness using a "Poisson" distribution, which is the standard way to
# make random counts (whole numbers that can't go below 0).

# Average lighting (0 = dark, 1 = dim, 2 = bright). Lighting doesn't really
# change between 6 and 11 PM, so one number per street type.
AVG_LIGHTING = {"main_road": 2.0, "commercial": 2.0, "secondary": 1.5, "lane": 1.0}

#                     6pm   9pm   11pm
AVG_SHOPS_OPEN = {
    "main_road":     (8,    6,    3),
    "commercial":    (15,   14,   8),
    "secondary":     (4,    2,    1),
    "lane":          (0.5,  0.2,  0.05),
}
AVG_PEOPLE_PER_MIN = {   # people + vehicles passing in one minute
    "main_road":     (60,   45,   25),
    "commercial":    (45,   50,   30),
    "secondary":     (20,   12,   5),
    "lane":          (4,    2,    1),
}
AVG_WOMEN_PER_MIN = {
    "main_road":     (6,    3,    1),
    "commercial":    (8,    6,    2),
    "secondary":     (2,    1,    0.3),
    "lane":          (0.5,  0.2,  0.05),
}

def make_changing_features(street_type, slot, is_weekend):
    """Make lighting, shops, crowd and women counts for one slot on one night."""
    s = SLOTS.index(slot)   # 0 for 6pm, 1 for 9pm, 2 for 11pm

    # Weekends: commercial streets are about 20% busier.
    boost = 1.2 if (is_weekend and street_type == "commercial") else 1.0

    # Lighting: start from the average, add a small random wobble, round it,
    # and keep it inside 0..2 (np.clip cuts off anything outside the range).
    lighting = AVG_LIGHTING[street_type] + rng.normal(0, 0.4)
    lighting = int(np.clip(round(lighting), 0, 2))

    shops = rng.poisson(AVG_SHOPS_OPEN[street_type][s] * boost)
    people = rng.poisson(AVG_PEOPLE_PER_MIN[street_type][s] * boost)
    women = rng.poisson(AVG_WOMEN_PER_MIN[street_type][s] * boost)
    women = min(women, people)   # can't have more women than total people

    return {
        "lighting_0to2": lighting,
        "shops_open": int(shops),
        "per_minute": int(people),
        "women_per_minute": int(women),
    }


# ---------------------------------------------------------------------------
# STEP 4: hidden safety score and simulated ratings
# ---------------------------------------------------------------------------
# This formula is our ASSUMPTION about what makes women feel safe. The
# ingredients follow Safetipin's audit parameters (lighting, openness,
# visibility, people, security, walk path, transport, gender usage).
# Plus signs = makes a street feel safer, minus signs = less safe.

def hidden_safety_score(row):
    s = 1.4                                              # starting point
    s += 0.5 * row["lighting_0to2"]                      # light helps a lot
    s += 0.08 * min(row["shops_open"], 10)               # open shops = "eyes on the street"
    s += 0.3 * row["safe_city_camera_yn"]
    s += 0.05 * min(row["private_cctv_count"], 6)
    s += 0.4 * row["police_yn"] + 0.2 * row["guards_yn"] # security presence
    s += 0.2 * row["footpath_yn"] + 0.15 * row["ride_stand_yn"]
    s += 0.25 * min(row["per_minute"] / 40, 1)           # busy streets (capped)
    s += 0.6 * min(row["women_per_minute"] / 5, 1)       # other women around = big effect
    s -= 0.5 * row["dead_frontage_yn"]                   # blank walls, nobody watching
    s -= 0.6 * row["isolated_spot_yn"]                   # hidden corners
    if row["slot"] == "11pm":
        s -= 0.3                                         # late night feels riskier
    return float(np.clip(s, 1, 5))                       # keep it on the 1-5 scale


def simulate_ratings(score):
    """Pretend 5 women each rate the street 1-5. Each one is a bit different
    (that's the noise), which is what real survey answers look like."""
    ratings = score + rng.normal(0, RATER_NOISE, size=RATERS)
    ratings = np.clip(np.round(ratings), 1, 5)
    return ratings.astype(int)


# ---------------------------------------------------------------------------
# STEP 5: average rating -> label (same thresholds as our data guide)
# ---------------------------------------------------------------------------
def rating_to_label(mean_rating):
    if mean_rating < 2.5:
        return "risky"
    elif mean_rating <= 3.5:
        return "moderate"
    else:
        return "safe"


# ---------------------------------------------------------------------------
# PUT IT ALL TOGETHER
# ---------------------------------------------------------------------------
def main():
    # Read our real list of 43 segments (we only need id and street name).
    segments = pd.read_csv(AUDIT_SHEET)[["segment_id", "street", "stretch"]]

    rows = []
    for _, seg in segments.iterrows():
        street_type = get_street_type(seg["segment_id"])
        fixed = make_fixed_features(street_type)          # made ONCE per segment

        for night in range(1, NIGHTS + 1):
            is_weekend = night in WEEKEND_NIGHTS
            for slot in SLOTS:
                row = {
                    "segment_id": seg["segment_id"],
                    "street": seg["street"],
                    "street_type": street_type,
                    "night": night,
                    "weekend_yn": int(is_weekend),
                    "slot": slot,
                }
                row.update(fixed)
                row.update(make_changing_features(street_type, slot, is_weekend))

                score = hidden_safety_score(row)
                ratings = simulate_ratings(score)
                for i, r in enumerate(ratings, start=1):
                    row[f"rating_{i}"] = int(r)
                row["mean_rating"] = round(float(ratings.mean()), 2)
                row["label"] = rating_to_label(row["mean_rating"])
                row["hidden_score"] = round(score, 2)   # kept ONLY for the rule-based baseline
                row["data_source"] = "synthetic"
                rows.append(row)

    data = pd.DataFrame(rows)
    data.to_csv(OUTPUT_FILE, index=False)

    # ---- quick sanity checks, printed to the screen ----
    print(f"Saved {len(data)} rows to {OUTPUT_FILE}\n")
    print("Label balance (aim: no class below ~20%):")
    print(data["label"].value_counts(normalize=True).round(2), "\n")
    print("Average rating by street type and slot (lanes at 11pm should be lowest):")
    print(data.pivot_table(index="street_type", columns="slot",
                           values="mean_rating", aggfunc="mean").round(2))


if __name__ == "__main__":
    main()
