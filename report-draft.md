# Safe Route Lahore: AI route planning for women's night-time safety
*CSC 241 Artificial Intelligence, Final Project, Fall 2026 (Dr. Sidra Zafar)*
*DRAFT: rewrite in your own words before submitting.*

## 1. Problem and SDG
Women in Lahore often feel unsafe walking alone after dark. Gallup (2025) found that 67% of women feel safe walking alone at night, compared with 78% of men. In the Aurat Foundation's Lahore transport audit of 903 women, 82% reported harassment at stops and 98% did not know of any helpline. CERP found that about 30% of Lahore women describe walking in their own neighbourhood as "very unsafe". Navigation apps optimise only for time. **Safe Route Lahore** recommends walking routes that balance safety against distance, and explains each choice.
**SDG 11.2** (safe, accessible transport for all), with **11.7** (safe public spaces) and **5.2** (eliminating violence against women).

## 2. Data
- **Area:** Gulberg III, bounded by Main Boulevard, Tipu Road, the northern curved road and Noor Jahan Road. It is split into 43 street segments: 28 road segments and 15 lanes.
- **Features**, which mirror our field-audit sheet: footpath, Safe City camera, private CCTV count, police, guards, dead frontage, isolated spot, ride stand, lighting (0–2), shops open and women per minute, recorded at 6, 9 and 11 PM, plus main road vs gali and the real distance to the nearest police station and hospital (OpenStreetMap). The crowd count was deliberately left out: a big crowd is not always safer for women (e.g. harassment in crowded markets).
- **Synthetic generation (approved by the instructor):** each segment gets a street type (main road, commercial, secondary, lane). Fixed features are drawn once per segment from type-specific probabilities, and time-varying features are drawn per night from Poisson distributions whose means fall as the night goes on. A hidden safety score is built from weights that follow Safetipin's audit parameters. **Five simulated raters** add Gaussian noise (σ = 0.6) and round to a 1–5 scale. The mean rating is then labelled: less safe < 2.5 ≤ moderate ≤ 3.5 < safer.
- **Size:** 43 × 3 × 10 nights = **1,290 rows**. Labels: 44% less safe, 16% moderate, 40% safer. We never label a street "safe", only "safer". Seed 42.

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
| Rule-based baseline | 0.62 | 0.61 | 0.40 |
| Decision tree | **0.88** | **0.83** | 0.93 |
| Naive Bayes | 0.86 | 0.78 | **0.94** |

*(Insert `results/confusion_matrices.png` and `results/decision_tree.png`.)*

**Routing** results are averaged over all 465 start/goal pairs:

| Slot | Mode | Extra distance | Avg. risk |
|---|---|---|---|
| 11 PM | Fastest | 0% | 0.37 |
| 11 PM | Balanced | +10% | 0.23 |
| 11 PM | Safety-first | +20% | 0.20 |
| 6 PM | Balanced | +11% | 0.15 (fastest: 0.29) |

A\* matched Dijkstra's optimal cost on every pair while expanding 10 junctions on average instead of 16.
**Worked example (11 PM, Sir Syed Road / first side road → Tehzeeb Bakers on MM Alam):** *fastest* is 1,102 m through lanes L1 and L2 (average risk 0.63). *Balanced* is 1,128 m along Sir Syed and Ghalib (Hafeez Centre) Road (risk 0.45), only 26 m longer. *Safety-first* is 1,346 m via Dopatta Gali (risk 0.32).

## 4b. App features for women
- **Route options** (fastest / balanced / safety-first) toggled on the map.
- **🆘 Panic button** showing 15 (Police), 1122 (Rescue) and 1043 (Punjab Women's Helpline), and sharing the last location with trusted contacts. *(simulated)*
- **"Are you okay?" check-in** if she goes off route: no answer in 60 s alerts trusted contacts, and another 60 s alerts the PSCA Women Safety app with her last known location. *(simulated)*
- **Low-battery care:** a reminder at 30%, and auto-sharing her location at 15%, because a dead phone means the app can't help.
- **Hammy 🐹**, a rule-based "little brother" chat that comforts *and* gives actionable advice in English or Roman Urdu.

## 5. Failure cases and limitations
1. **Synthetic data:** the model learns our assumptions. High accuracy shows the pipeline works, not that it is accurate in real life.
2. **Shortcut feature:** main road vs gali carries 66% of the tree's importance (gali adds 17%). Street type decides most other features in our generator, so cameras, guards and police presence got almost zero importance even though the formula uses them. With real data, correlated features would need careful analysis.
3. **Both the tree and Naive Bayes called a truly less-safe street-time "safer" once** (out of about 570). In a safety app this error matters most, so a cautious ensemble is worth testing.
4. **Map accuracy:** street shapes come from OpenStreetMap, but our segment junctions were traced from a phone map and snapped onto OSM, so which real lane each L1–L15 refers to is approximate. OSM also had small gaps (e.g. Ghalib Road where it crosses MM Alam's dual carriageway), which we bridged along the same named street.
5. **Coverage:** one neighbourhood and three time slots. There is no weekday/weekend toggle in the app yet.

## 6. Ethics
- **Labelling areas "less safe" can stigmatise neighbourhoods** and the people who live there. We label *conditions* (dark, empty, no open shops) at specific times, not communities.
- **False reassurance:** the app never says "safe", only "safer", because no street is guaranteed safe. It says so, and the data is clearly marked synthetic.
- **Privacy:** the app collects no user location or ratings. The planned real data (field audit and anonymous survey) holds no personal identifiers.
- **Responsibility:** safety is the duty of the city and of harassers, not of women's route choices. The tool supports choice and does not shift blame.

## 7. Future work
Real field-audit and survey data; real integrations for the alerts (SMS, PSCA Women Safety app); an AI mode for Hammy; matching every OSM street (not only our 43 segments); a weekday/weekend toggle; an SOS/emergency feature; expansion beyond Gulberg III.
