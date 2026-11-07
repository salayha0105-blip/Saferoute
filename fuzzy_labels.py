"""
Safe Route Lahore - Step 4: fuzzy logic labels (course Week XI)
================================================================

WHAT THIS FILE DOES:
  Turns numbers into the kind of words people use, e.g.
  "safer until 9 PM, less safe after".

WHY FUZZY LOGIC (and not a hard cut-off):
  With a hard rule like "risk > 0.5 = risky", a street with risk 0.49 is
  "fine" and 0.51 is "risky", which is silly. Fuzzy logic lets a value be
  PARTLY "medium" and PARTLY "high" at the same time, and then blends the
  rules smoothly. That is closer to how people actually judge safety.

HOW IT WORKS (a Sugeno-style fuzzy system, written by hand so every step is visible):
  1. FUZZIFY: turn each input into "how much does it belong" to each word.
       inputs: risk (0-1, from the decision tree)
               women_per_minute (how many other women are around)
  2. RULES: IF ... AND ... THEN danger = some number (0-10).
       "AND" = take the smaller membership (the standard fuzzy AND = min).
  3. DEFUZZIFY: weighted average of the rule outputs, weighted by how
       strongly each rule fired. Result: one danger score 0-10.
  4. Turn the score into a word: safer / be careful / less safe.
     (Never "safe": no street is guaranteed safe.)
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
def fuzzify(risk, women_per_minute):
    return {
        "risk_low": shoulder_left(risk, 0.2, 0.45),
        "risk_medium": triangle(risk, 0.25, 0.5, 0.75),
        "risk_high": shoulder_right(risk, 0.55, 0.8),
        "women_few": shoulder_left(women_per_minute, 0.5, 2.5),
        "women_many": shoulder_right(women_per_minute, 1.5, 4.0),
    }


# --- Step 2 + 3: rules and defuzzification ------------------------------------
def danger_score(risk, women_per_minute):
    m = fuzzify(risk, women_per_minute)
    # (how strongly the rule fires, the danger it suggests on a 0-10 scale)
    rules = [
        (m["risk_low"], 1.5),                                     # IF risk low THEN danger very low
        (min(m["risk_medium"], m["women_many"]), 4.0),            # IF risk medium AND many women THEN lowish
        (min(m["risk_medium"], m["women_few"]), 6.5),             # IF risk medium AND few women THEN highish
        (min(m["risk_high"], m["women_many"]), 7.0),              # IF risk high AND many women THEN high
        (min(m["risk_high"], m["women_few"]), 9.5),               # IF risk high AND few women THEN very high
        (m["risk_medium"] * 0.5, 5.0),                            # weak "middle" rule so nothing is undefined
    ]
    total_strength = sum(strength for strength, _ in rules)
    if total_strength == 0:
        return 5.0
    return sum(strength * out for strength, out in rules) / total_strength


# --- Step 4: words ------------------------------------------------------------
def danger_word(score):
    if score < 4.0:
        return "safer"
    if score < 6.5:
        return "be careful"
    return "less safe"


def night_phrase(words_by_slot):
    """Summarise one segment's words at 6, 9 and 11 PM into one sentence.
    words_by_slot example: {"6pm": "safer", "9pm": "safer", "11pm": "less safe"}"""
    w6, w9, w11 = words_by_slot["6pm"], words_by_slot["9pm"], words_by_slot["11pm"]
    if w6 == w9 == w11:
        return f"{w6} all evening"
    if w6 != "less safe" and w9 == "less safe":
        return "less safe after 9 PM"
    if w9 != "less safe" and w11 == "less safe":
        return "less safe after 11 PM"
    if w6 == "safer" and w9 == "be careful":
        return "be careful after 9 PM"
    if w9 == "safer" and w11 == "be careful":
        return "be careful after 11 PM"
    return f"6 PM {w6}, 9 PM {w9}, 11 PM {w11}"


def label_all_segments(segment_risk):
    """Add fuzzy columns to the table from train_models.py (segment_risk.csv)."""
    table = segment_risk.copy()
    table["danger_0to10"] = [round(danger_score(r, w), 2)
                             for r, w in zip(table["risk"], table["women_per_minute"])]
    table["fuzzy_word"] = table["danger_0to10"].apply(danger_word)
    phrases = {}
    for seg, rows in table.groupby("segment_id"):
        phrases[seg] = night_phrase(dict(zip(rows["slot"], rows["fuzzy_word"])))
    table["night_phrase"] = table["segment_id"].map(phrases)
    return table


if __name__ == "__main__":
    import pandas as pd
    table = label_all_segments(pd.read_csv("segment_risk.csv"))
    table.to_csv("segment_risk.csv", index=False)
    print(table.drop_duplicates("segment_id")[["segment_id", "night_phrase"]].to_string(index=False))
    print("\nDemo: risk 0.5 with 0 vs 5 women per minute ->",
          round(danger_score(0.5, 0), 2), "vs", round(danger_score(0.5, 5), 2))
