# Safe Route Lahore: synthetic data generator spec

Dr. Sidra approved generated data on 6 Nov 2026. This spec says *what* the generator should do. You write the code yourself, which keeps you under the 30% AI-use limit. All numbers are starting guesses: change any that don't match what you know about Gulberg, and note the change in your report.

Output: `safe_route_synthetic.csv`, with one row per **segment × time slot × night**.
43 segments × 3 slots (6, 9, 11 PM) × 10 nights = **1,290 rows**. Use a fixed seed (`np.random.seed(42)`).

---

## Step 1: Give each segment a street type (you decide, using your local knowledge)

| street_type | Suggested segments |
|---|---|
| `main_road` | MB1–2, TP1–2 |
| `commercial` | MM1–4, DG1–4, HT1–5 |
| `secondary` | SS1–3, NJ1–3, TQ1–2, CR1–3 |
| `lane` | L1–L15 |

## Step 2: Fixed features (generate once per segment, then keep them the same every night)

These are the chances that a feature is "yes", or the range for a count.

| Feature | main_road | commercial | secondary | lane |
|---|---|---|---|---|
| footpath_yn | 0.9 | 0.8 | 0.6 | 0.2 |
| safe_city_camera_yn | 0.9 | 0.7 | 0.4 | 0.1 |
| private_cctv_count | 2–6 | 4–10 | 1–4 | 0–3 |
| police_yn | 0.4 | 0.2 | 0.1 | 0.02 |
| guards_yn | 0.5 | 0.8 | 0.4 | 0.5 (houses have guards) |
| dead_frontage_yn | 0.1 | 0.05 | 0.3 | 0.5 |
| isolated_spot_yn | 0.05 | 0.05 | 0.2 | 0.4 |
| ride_stand_yn | 0.6 | 0.5 | 0.2 | 0.05 |

## Step 3: Time-varying features (generate fresh for every slot and night)

Mean values are shown below. Add random noise around them: Poisson for counts, and keep lighting between 0 and 2.

| Feature | Slot | main_road | commercial | secondary | lane |
|---|---|---|---|---|---|
| lighting_0to2 | all | 2 | 2 | 1–2 | ~1 |
| shops_open | 6 PM | 8 | 15 | 4 | 0–1 |
| | 9 PM | 6 | 14 | 2 | 0 |
| | 11 PM | 3 | 8 | 1 | 0 |
| per_minute (people + vehicles) | 6 PM | 60 | 45 | 20 | 4 |
| | 9 PM | 45 | 50 | 12 | 2 |
| | 11 PM | 25 | 30 | 5 | 1 |
| women_per_minute | 6 PM | 6 | 8 | 2 | 0.5 |
| | 9 PM | 3 | 6 | 1 | 0.2 |
| | 11 PM | 1 | 2 | 0.3 | 0.05 |

Also add `weekend_yn`: on 3 of the 10 nights, raise shops and crowds by about 20% for commercial roads.

## Step 4: Labels via simulated survey raters (this mirrors your real survey method)

1. **Hidden safety score**, built from the features. The weights roughly follow Safetipin's audit parameters (lighting, openness, visibility, people, security, walk path, transport, gender usage):

```
s = 1.4
  + 0.5 * lighting                 (0–2)
  + 0.08 * min(shops_open, 10)
  + 0.3 * safe_city_camera + 0.05 * min(private_cctv, 6)
  + 0.4 * police + 0.2 * guards
  + 0.2 * footpath + 0.15 * ride_stand
  + 0.25 * min(per_minute / 40, 1)
  + 0.6 * min(women_per_minute / 5, 1)
  - 0.5 * dead_frontage - 0.6 * isolated_spot
  - 0.3 if slot == 11 PM
s = clip(s, 1, 5)
```

2. **5 simulated raters per row:** `rating_i = round(clip(s + Normal(0, 0.6), 1, 5))`.
3. `mean_rating` = the average of the 5 ratings, which gives these labels (the same thresholds as your data guide):
   - under 2.5 = **risky**, 2.5–3.5 = **moderate**, over 3.5 = **safe**

The rater noise is important: it stops the decision tree from just copying the formula back.

## Step 5: Sanity checks before you train

- Label balance: aim for roughly 25–45% in each class. If one class is tiny, adjust the constant 1.2.
- Lanes at 11 PM should be mostly risky, and MM Alam at 6 PM mostly safe. If not, a weight is off.
- Plot `mean_rating` against lighting and against women_per_minute. Both should slope upward.
- **Real spot check (strongly recommended):** walk 5–10 segments once and compare them with the generated values. Report where they differ.

## Step 6: Be honest in the report

- Label the dataset **synthetic** in the README, the report and the app.
- Explain that the rules come from street type and time, with the risk weights based on Safetipin's parameters, and attach this spec as an appendix.
- **Limitation:** the model learns *your assumptions*. Your results show the pipeline works, not real-world accuracy.
- **Fairness check:** compare the decision tree against the **rule-based baseline**, which uses only the formula with no noise, and against **Naive Bayes**. Use the same train/test split, with segments split by ID so the same street never appears in both train and test.
