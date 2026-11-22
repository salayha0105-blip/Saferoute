# ⚠️ SIMULATED survey (n = 50): not real responses

**No real person answered this survey.** `simulated_survey.py` makes up 50 plausible sets of
answers to our questionnaire (`questionnaire.md`), using a fixed seed (7). Every row says
`data_source = SIMULATED`. Dr. Sidra approved generated data for this course project
(6 Nov 2026); the survey is labelled the same way as the street data.

## What it is for
A **sanity check of our design**, not training data. The models never see it.
1. Do the factors women would rate highest match what our generator and fuzzy rules lean on?
2. Does felt safety fall from 6 PM to 11 PM, and is a gali lower than a main road?

## Where the numbers come from

| Answer | We aimed for | Basis |
|---|---|---|
| Harassed in public, last 12 months | ~80% | **Published:** Aurat Foundation, Lahore public-transport study of 903 women: 82% faced harassment at stops |
| Knows the 1043 helpline | ~5% | **Published:** same study: 98% did not know of any helpline |
| Gali at 9 PM rated "1 = very unsafe" | ~30% | **Published:** CERP: about 30% of Lahore women call walking in their own neighbourhood "very unsafe" |
| Knows the PSCA Women Safety app | ~15% | **Our assumption** (no figure found) |
| Felt-safety averages by time and place | 3.9 → 1.5 | **Our assumption**: later = lower, gali < main road |
| Factor ratings | lighting 4.6 … hospital 2.9 | **Our assumption**, ordered after Safetipin's audit parameters (lighting, openness, visibility, security, walk path) |

Each simulated person also gets a personal "worry" level, so her answers hang together
(someone who feels unsafe at 6 PM also tends to feel unsafe at 11 PM), plus a little noise.

## Results (from `results/survey_summary.json`)
- **Top factors:** good lighting 4.5, main road 4.2, shops open 4.1, police nearby 3.9 (out of 5).
  These are the same factors our fuzzy rules (lighting) and decision tree (main road vs gali,
  shops open, police) rely on most, so the design is consistent with what we assumed women value.
- **Felt safety:** main road 3.9 → 3.2 → 2.5 and gali 2.8 → 2.1 → 1.6 (6 → 9 → 11 PM).
  26% rate a gali at 9 PM "very unsafe".
- **Harassed in the last 12 months:** 72%. **Know 1043:** 4%. **Know the PSCA app:** 18%.
- **Would use the app:** 4.0 / 5.

Charts: `results/survey_factors.png`, `results/survey_felt_safety.png`.

## Limits (say this out loud)
The survey agrees with our design partly **because we built it from the same assumptions**.
It shows the pieces are consistent, not that real women in Gulberg feel this way.
The next step is to run the questionnaire for real (Google Form, anonymous) and compare.
