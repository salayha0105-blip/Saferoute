# If Dr. Sidra asks… (catch-up notes for Snaf)

Read this when you're feeling better. Each part has a **one-line summary**, then likely questions with a short answer you can say in your own words. The files are listed in the order you should read them.

---

## 1. `generate_data.py`: the synthetic data
*(Version 3, 22 Nov: no crowd count and no "women around"; main road vs gali and real distance to the nearest police station and hospital added.)*
**In one line:** street type and time of night decide the features, a hidden formula turns features into a safety score, and 5 simulated women rate each street with some disagreement.

- **"Isn't the model just learning your formula back?"**
  Partly, yes, and that is a known limitation. The 5 noisy raters make the labels imperfect, the same way real survey answers are, so the model must learn a *pattern* instead of copying a formula. We present the results as "the pipeline works", not "Lahore is like this".
- **"Where did the formula's weights come from?"**
  They follow Safetipin's audit parameters (lighting, openness, visibility, people, security, walk path, transport, gender usage). Lighting got the largest weight, which matches the safety-audit literature.
- **"Why a fixed seed?"** So anyone who runs the code gets exactly the same dataset (reproducibility).

## 2. `train_models.py`: decision tree vs Naive Bayes vs rules
**In one line:** on streets they had never seen, the decision tree scored 79% accuracy and Naive Bayes 84%, compared with 62% for hand-written rules.

- **"Why GroupKFold?"** If MM2 is in the test set, none of MM2's rows are in training. Splitting randomly would let the same street "leak" into training from other nights and inflate the score.
- **"Why depth 5?"** We tried depths 2–8. Depth 5 had the best cross-validated macro-F1 (0.73), and deeper trees didn't clearly help. A shallow tree is also easier to explain.
- **"Why macro-F1 and less-safe recall, not just accuracy?"** The classes are unbalanced (moderate is only 16%), and the worst mistake is calling a less-safe street safer. Less-safe recall measures how many less-safe streets we catch: 86% for the tree, 94% for Naive Bayes, 38% for the rules.
- **"Which is better, the tree or Naive Bayes?"** Since we dropped "women around", Naive Bayes is better: accuracy 0.84 vs 0.79, macro-F1 0.77 vs 0.73, and it never called a less-safe street "safer" (the tree did 15 times out of 586). We still show the tree in the app because its rules can be explained (`results/decision_tree.png`). Be honest: switching to Naive Bayes is our next step.
- **"What's the 'naive' in Naive Bayes?"** It assumes features are independent given the label. That isn't true here (main roads and shops go together), but it still works well in practice.
- **"Which features matter?"** Main road vs gali dominates (0.63 importance), then gali (0.16), then shops open, lighting and police (about 0.04–0.05 each). *Failure case to mention:* in our generator, street type drives most other features, so the tree uses it as a shortcut and cameras and police get almost no weight.
- **"Why no crowd count?"** A big crowd is not always safer for women (crowded markets can mean harassment), so we left it out. We also dropped "other women around" (22 Nov), so every feature describes the street, not the people on it.
- **"Why say 'safer', not 'safe'?"** No street is guaranteed safe. The labels are less safe / moderate / safer, and the app's ranges are Safer / Be careful / Risky / Avoid.

## 2b. `simulated_survey.py`: the SIMULATED survey
**In one line:** 50 made-up answers to our real questionnaire, labelled SIMULATED everywhere, used only to sanity-check the design.

- **"Is this real data?"** No. No real person answered. It's generated like the street data, which you approved. Where research gives a figure we aimed near it: ~80% harassed (Aurat Foundation: 82% at stops), ~5% know the 1043 helpline (98% unaware), ~30% call a gali at night "very unsafe" (CERP). The rest are our assumptions (`survey/SIMULATED_SURVEY.md`).
- **"What did it show?"** Lighting, main road, open shops and police are the top factors, the same ones our model leans on, and felt safety drops from 6 to 11 PM. That agreement is partly built in, so it shows consistency, not proof.
- **"Next step?"** Run the same questionnaire for real (anonymous Google Form) and compare.

## 3. `road_graph.py`: the map as a graph
**In one line:** 31 junctions (nodes) and 50 street pieces (edges) covering our 43 segments, with each edge storing its length and segment ID.

- **"Do the routes follow real roads?"** Yes. The real street network was downloaded from **OpenStreetMap** with `osmnx`, using a GitHub Action. `tools/build_road_shapes.py` lines up our hand-drawn map with OSM using 8 known crossings (an *affine transform*, about 20 m error), snaps each junction onto its real road, and makes every segment follow the real street shape (*shortest path along OSM streets*).

## 4. `fuzzy_labels.py`: fuzzy logic
**In one line:** it blends the tree's risk with the street's lighting into one safety score (0–1), then shows it as a range: 0.70–1 Safer, 0.50–0.70 Be careful, 0.30–0.50 Risky, 0–0.30 Avoid.

- **"Where is the fuzzy logic if you show ranges?"** The ranges are only the last step. Before that: fuzzify (risk low/medium/high, lighting dark/bright), apply 6 rules like "IF risk medium AND dark THEN safety 0.40" (AND = min), then defuzzify with a weighted average (Sugeno style). That gives the crisp score, and the score is put in a range.
- **"Why not just a threshold on risk?"** With a threshold, 0.49 is fine and 0.51 is risky, which is unrealistic. Fuzzy logic blends smoothly: on a bright street, risk 0.49 → safety 0.61 and 0.51 → 0.59. It also lets lighting count: the same risk (0.5) gives safety 0.40 on a dark street but 0.60 on a bright one.

## 5. `routing.py`: A\* search
**In one line:** cost = length × (1 + weight × risk), where risk = 1 − fuzzy safety score, and A\* finds the cheapest route for the fastest (0), balanced (3) and safety-first (10) weights.

- **"Is your heuristic admissible?"** Yes. h = straight-line distance, and every street's cost is at least its length, which is at least the straight-line distance, so h never overestimates. That means A\* is optimal.
- **"How do you know your A\* is correct?"** For every one of the 465 start/goal pairs, the code checks that our A\* cost equals networkx's Dijkstra cost.
- **"Is A\* better than Dijkstra here?"** Same answer, less work: A\* expanded about 10 junctions on average vs 16 for Dijkstra.
- **"Why not the genetic algorithm from your plan?"** On a 31-node map, A\* is exact and instant. A GA gives good but not guaranteed answers and needs tuning. We kept the GA plan's idea of 3 preference weights.
- **The best demo example (11 PM, Sir Syed / first side road → Tehzeeb Bakers, the app's default; tick all three boxes on the map):** fastest is 1,102 m through lanes (safety 0.45, Risky). Balanced and safety-first both go via Sir Syed and Ghalib Road: 1,128 m (safety 0.77, Safer), just 26 m more. More safety costs more walking, and that's the **trade-off**.
- **"Why can't one route be fastest AND safest?"** Sometimes it is: then all ticked routes overlap and the app says so. When the shortcut uses a less-safe street, no route can be both, so the user picks the trade-off.

## 6. `app.py`: the demo
**In one line:** pick From, To, time and mode, and the app shows a map with coloured streets, the route, and why it was chosen.

- To deploy it: push this folder to GitHub, sign in at share.streamlit.io, choose New app, and pick `app.py`. It's free.

## 7. `safety_tools.py`: panic button, check-in, battery (all simulated)
**In one line:** demo pop-ups that show what a real app would do. Nothing is actually sent.

- **"Why the PSCA Women Safety app and not regular police?"** It's Punjab Safe Cities' service built for women's emergencies, so an alert reaches people trained for exactly this.
- **"How does the 'Are you okay?' timer work without reloading the map?"** It's a Streamlit *fragment* that re-runs only itself every second.
- **"Why warn at 15% battery?"** If the phone dies, the app can't help at all, so at 15% we share the last location while we still can.

## 8. `hammy.py`: Hammy 🐹, the little-brother companion
**In one line:** a *rule-based agent*: IF the message contains certain keywords (e.g. "peecha", "following") THEN pick a matching reply that comforts her *and* gives a concrete action.

- **"Why not ChatGPT/Claude?"** Scripted replies are free, work offline, and every answer can be checked for safety. An AI mode is planned as future work (`ai_reply()`).
- **"What if two intents match?"** Intents are checked in priority order, so "I'm scared someone is following me" is treated as *followed*, the urgent one.

### Hammy 2.0: the 3D boy with voice

- **"Is the 3D model downloaded from somewhere?"** No. We built him in three.js from simple shapes (spheres and cylinders), so there is no copyright issue. He breathes, blinks, waves hello and moves his mouth while talking.
- **"Is the voice AI?"** The listening and speaking use the browser's built-in Web Speech API (speech-to-text and text-to-speech). The *answers* still come from our rule-based agent in `hammy.py`, so every reply can be explained.
- **Limits:** voice input works best in Chrome or Edge and needs microphone permission. Typing always works, and the voice sounds different on each device.
