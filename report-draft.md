# Safe Route Lahore: AI route planning for women's night-time safety
*CSC 241 Artificial Intelligence, Final Project, Fall 2026 (Dr. Sidra Zafar)*
*DRAFT: rewrite in your own words before submitting.*

## 1. Problem and SDG
Women in Lahore often feel unsafe walking alone after dark. Gallup (2025) found that 67% of women feel safe walking alone at night, compared with 78% of men. In the Aurat Foundation's Lahore transport audit of 903 women, 82% reported harassment at stops and 98% did not know of any helpline. CERP found that about 30% of Lahore women describe walking in their own neighbourhood as "very unsafe". Navigation apps optimise only for time. **Safe Route Lahore** recommends walking routes that balance safety against distance, and explains each choice.
**SDG 11.2** (safe, accessible transport for all), with **11.7** (safe public spaces) and **5.2** (eliminating violence against women).

## 2. Data
- **Area:** Gulberg III, bounded by Main Boulevard, Tipu Road, the northern curved road and Noor Jahan Road. It is split into 43 street segments: 28 road segments and 15 lanes.
- **Features**, which mirror our field-audit sheet: footpath, Safe City camera, private CCTV count, police, guards, dead frontage, isolated spot, ride stand, lighting (0–2), shops open, people per minute and women per minute, recorded at 6, 9 and 11 PM.
- **Synthetic generation (approved by the instructor):** each segment gets a street type (main road, commercial, secondary, lane). Fixed features are drawn once per segment from type-specific probabilities, and time-varying features are drawn per night from Poisson distributions whose means fall as the night goes on. A hidden safety score is built from weights that follow Safetipin's audit parameters. **Five simulated raters** add Gaussian noise (σ = 0.6) and round to a 1–5 scale. The mean rating is then labelled: risky < 2.5 ≤ moderate ≤ 3.5 < safe.
- **Size:** 43 × 3 × 10 nights = **1,290 rows**. Labels: 43% risky, 20% moderate, 37% safe. Seed 42.

## 3. Methods and why we chose them
| Task | Method | Alternatives considered |
|---|---|---|
| Predict segment safety | **Decision tree** (depth 4, min 10 samples per leaf) | Naive Bayes (compared), k-NN (less interpretable) |
| Probabilistic comparison | **Gaussian Naive Bayes** | Bayesian network (needs hand-made structure) |
| Human-readable labels | **Fuzzy logic**, Sugeno inference with 5 rules on risk × women present | Fixed thresholds (brittle at the boundaries) |
| Route planning | **A\***, cost = length × (1 + w·risk), with h = straight-line distance (admissible) | Genetic algorithm (not guaranteed optimal), Dijkstra (slower) |

We chose the decision tree because the app must *explain* its recommendations, and a tree's if/else rules can be shown directly.

## 4. Evaluation
**Classifier.** We used 5-fold GroupKFold by segment, so every model is tested on unseen streets.

| Model | Accuracy | Macro-F1 | Risky recall |
|---|---|---|---|
| Rule-based baseline | 0.58 | 0.58 | 0.29 |
| Decision tree | **0.82** | **0.78** | **0.85** |
| Naive Bayes | 0.80 | 0.78 | 0.76 |

*(Insert `results/confusion_matrices.png` and `results/decision_tree.png`.)*

**Routing** results are averaged over all 465 start/goal pairs:

| Slot | Mode | Extra distance | Avg. risk |
|---|---|---|---|
| 11 PM | Fastest | 0% | 0.48 |
| 11 PM | Balanced | +10% | 0.30 |
| 11 PM | Safety-first | +18% | 0.28 |
| 6 PM | Balanced | +15% | 0.14 (fastest: 0.35) |

A\* matched Dijkstra's optimal cost on every pair while expanding 10 junctions on average instead of 16.
**Worked example (11 PM):** the fastest route from Main Blvd/L8 to MM Alam is 1,033 m through three lanes, with average risk 0.91. The balanced route is 1,279 m via Hafeez Centre road, with average risk 0.13.

## 5. Failure cases and limitations
1. **Synthetic data:** the model learns our assumptions. High accuracy shows the pipeline works, not that it is accurate in real life.
2. **Shortcut feature:** people per minute carries 65% of the tree's importance. It acts as a stand-in for street type, so cameras and police got zero importance even though the generator uses them. With real data, correlated features would need careful analysis.
3. **The tree called a truly risky street-time "safe" 3 times out of 555**, while Naive Bayes never did. In a safety app this error matters most, so a cautious ensemble is worth testing.
4. **Map accuracy:** junctions were traced by hand (about ±50 m) because OpenStreetMap could not be downloaded in the build environment.
5. **Coverage:** one neighbourhood and three time slots. There is no weekday/weekend toggle in the app yet.

## 6. Ethics
- **Labelling areas "risky" can stigmatise neighbourhoods** and the people who live there. We label *conditions* (dark, empty, no open shops) at specific times, not communities.
- **False reassurance:** a "safe" label is never a guarantee. The app says so, and the data is clearly marked synthetic.
- **Privacy:** the app collects no user location or ratings. The planned real data (field audit and anonymous survey) holds no personal identifiers.
- **Responsibility:** safety is the duty of the city and of harassers, not of women's route choices. The tool supports choice and does not shift blame.

## 7. Future work
Real field-audit and survey data; the real OpenStreetMap network via osmnx; a weekday/weekend toggle; an SOS/emergency feature; expansion beyond Gulberg III.
