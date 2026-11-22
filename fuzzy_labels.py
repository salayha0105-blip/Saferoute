"""
Safe Route Lahore - Step 4: fuzzy logic safety score + ranges (course Week XI)
=============================================================================

WHAT THIS FILE DOES:
  Turns the decision tree's risk and the street's lighting into ONE safety
  score from 0 to 1, then shows it as a simple range:

      0.00 - 0.30   Avoid
      0.30 - 0.50   Risky
      0.50 - 0.70   Be careful
      0.70 - 1.00   Safer        (never "safe": no street is guaranteed safe)

WHERE IS THE FUZZY LOGIC? (Dr. Sidra may ask)
  The ranges are only the LAST step, for display. The score itself comes
  from a fuzzy inference system:
    1. FUZZIFY: each input belongs PARTLY to several words.
         risk (0-1, from the decision tree): low / medium / high
         lighting (0-2, average over the nights): dark / bright
       e.g. risk 0.6 is 0.71 "medium" AND 0.29 "high" at the same time.
    2. RULES: 6 rules like "IF risk medium AND dark THEN safety 0.40".
       "AND" = take the smaller membership (the standard fuzzy AND = min).
    3. DEFUZZIFY: weighted average of the rule outputs, weighted by how
       strongly each rule fired (Sugeno style). Result: one crisp score 0-1.
    4. RANGE: put the crisp score into one of the 4 boxes above.

WHY FUZZY LOGIC (and not a hard cut-off on risk):
  With a hard rule like "risk > 0.5 = risky", 0.49 is fine and 0.51 is
  risky. Fuzzy rules blend smoothly, and they let lighting soften or sharpen
  the tree's risk in the way people describe it ("medium risk but well lit").
  The 4 ranges are easy to read; the fuzzy score behind them is what makes
  them sensible.

Written by hand (no fuzzy library) so every step is visible.
"""


def triangle(x, left, peak, right):
    """Triangular membership: 0 outside [left, right], 1 at the peak,
    straight lines in between. This is the most common fuzzy shape."""
    if x <= left or x >= right:
        return 1.0 if x == peak else 0.0
    if x <= peak:
        return (x - left) / (peak - left)
    return (right - x) / (right - peak)


def shoulder_left(x, full, zero):
    """1 below `full`, sliding down to 0 at `zero` (for words like 'low')."""
    if x <= full:
        return 1.0
    if x >= zero:
        return 0.0
    return (zero - x) / (zero - full)


def shoulder_right(x, zero, full):
    """0 below `zero`, rising to 1 at `full` (for words like 'high')."""
    if x <= zero:
        return 0.0
    if x >= full:
        return 1.0
    return (x - zero) / (full - zero)


# --- Step 1: fuzzify ---------------------------------------------------------
# The memberships of each input add up to 1 everywhere, so every value is
# covered by some word and no rule set is ever "empty".
def fuzzify(risk, lighting):
    return {
        "risk_low": shoulder_left(risk, 0.15, 0.5),
        "risk_medium": triangle(risk, 0.15, 0.5, 0.85),
        "risk_high": shoulder_right(risk, 0.5, 0.85),
        "dark": shoulder_left(lighting, 0.8, 1.6),
        "bright": shoulder_right(lighting, 0.8, 1.6),
    }


# --- Step 2 + 3: rules and defuzzification ------------------------------------
#   (risk word, light word) -> safety the rule suggests (0-1)
RULES = [
    ("risk_low", "bright", 0.90),      # IF risk low AND bright THEN very safer
    ("risk_low", "dark", 0.70),        # IF risk low AND dark THEN safer, but less
    ("risk_medium", "bright", 0.60),   # IF risk medium AND bright THEN be careful
    ("risk_medium", "dark", 0.40),     # IF risk medium AND dark THEN risky
    ("risk_high", "bright", 0.30),     # IF risk high AND bright THEN risky / avoid
    ("risk_high", "dark", 0.10),       # IF risk high AND dark THEN avoid
]


def safety_score(risk, lighting):
    m = fuzzify(risk, lighting)
    fired = [(min(m[a], m[b]), out) for a, b, out in RULES]   # fuzzy AND = min
    total = sum(strength for strength, _ in fired)
    if total == 0:
        return 0.5
    return sum(strength * out for strength, out in fired) / total


# --- Step 4: ranges -------------------------------------------------------------
BANDS = [            # (lowest score, name) from best to worst
    (0.70, "Safer"),
    (0.50, "Be careful"),
    (0.30, "Risky"),
    (0.00, "Avoid"),
]


def safety_band(score):
    for low, name in BANDS:
        if score >= low:
            return name
    return "Avoid"


def night_phrase(bands_by_slot):
    """Summarise one segment's ranges at 6, 9 and 11 PM in a few words.
    bands_by_slot example: {"6pm": "Safer", "9pm": "Safer", "11pm": "Risky"}"""
    times = [("6pm", "6 PM"), ("9pm", "9 PM"), ("11pm", "11 PM")]
    runs = []
    for slot, name in times:
        if not runs or runs[-1][0] != bands_by_slot[slot]:
            runs.append((bands_by_slot[slot], name))
    if len(runs) == 1:
        return f"{runs[0][0]} all evening"
    if len(runs) == 2:
        return f"{runs[0][0]} before {runs[1][1]}, {runs[1][0].lower()} after"
    return " · ".join(f"{t} {b.lower()}" for b, t in runs)


def label_all_segments(segment_risk):
    """Add the fuzzy safety score, its range and a night phrase to the table
    from train_models.py (segment_risk.csv)."""
    table = segment_risk.copy()
    table["safety_0to1"] = [round(safety_score(r, l), 3)
                            for r, l in zip(table["risk"], table["lighting_0to2"])]
    table["band"] = table["safety_0to1"].apply(safety_band)
    phrases = {}
    for seg, rows in table.groupby("segment_id"):
        phrases[seg] = night_phrase(dict(zip(rows["slot"], rows["band"])))
    table["night_phrase"] = table["segment_id"].map(phrases)
    return table


if __name__ == "__main__":
    import pandas as pd
    table = label_all_segments(pd.read_csv("segment_risk.csv"))
    table.to_csv("segment_risk.csv", index=False)
    print(table.drop_duplicates("segment_id")[["segment_id", "night_phrase"]].to_string(index=False))
    print("\nRange counts (segment x slot):", table["band"].value_counts().to_dict())
    print("Demo: risk 0.5 when dark vs bright ->",
          round(safety_score(0.5, 0.5), 2), "vs", round(safety_score(0.5, 2.0), 2),
          "| risk 0.49 vs 0.51 (bright) ->",
          round(safety_score(0.49, 2.0), 3), "vs", round(safety_score(0.51, 2.0), 3), "(smooth, no jump)")
