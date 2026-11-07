# If Dr. Sidra asks… (catch-up notes for Snaf)

Read this when you're feeling better. Each part has a **one-line summary**, then likely questions with a short answer you can say in your own words. The files are listed in the order you should read them.

---

## 1. `generate_data.py`: the synthetic data
**In one line:** street type and time of night decide the features, a hidden formula turns features into a safety score, and 5 simulated women rate each street with some disagreement.

- **"Isn't the model just learning your formula back?"**
  Partly, yes, and that is a known limitation. The 5 noisy raters make the labels imperfect, the same way real survey answers are, so the model must learn a *pattern* instead of copying a formula. We present the results as "the pipeline works", not "Lahore is like this".
- **"Where did the formula's weights come from?"**
  They follow Safetipin's audit parameters (lighting, openness, visibility, people, security, walk path, transport, gender usage). Women around and lighting got the largest weights, which matches the safety-audit literature.
- **"Why a fixed seed?"** So anyone who runs the code gets exactly the same dataset (reproducibility).

## 2. `train_models.py`: decision tree vs Naive Bayes vs rules
**In one line:** the decision tree scored 82% accuracy on streets it had never seen, compared with 58% for hand-written rules. Naive Bayes was close at 80%.

- **"Why GroupKFold?"** If MM2 is in the test set, none of MM2's rows are in training. Splitting randomly would let the same street "leak" into training from other nights and inflate the score.
- **"Why depth 4?"** We tried depths 2–8. Depth 4 had the best cross-validated macro-F1 (0.777), and deeper trees didn't clearly help. A shallow tree is also easier to explain.
- **"Why macro-F1 and risky recall, not just accuracy?"** The classes are unbalanced (moderate is only 20%), and the worst mistake is calling a risky street safe. Risky recall measures how many risky streets we catch: 85% for the tree vs 29% for the rules.
- **"Naive Bayes never called a risky street safe, but the tree did 3 times. Why pick the tree?"** Good catch. The tree has better overall F1 and risky recall, *and* it's explainable (`results/decision_tree.png`). Naive Bayes is more cautious. In future work we could combine them or use NB for a "second opinion".
- **"What's the 'naive' in Naive Bayes?"** It assumes features are independent given the label. That isn't true here (crowds and shops go together), but it still works well in practice.
- **"Which features matter?"** People per minute (0.65 importance) dominates, followed by dead frontage, shops open and lighting. *Failure case to mention:* crowd count acts as a shortcut for street type, so cameras and police got 0 importance even though the formula uses them. This happens because they are correlated with crowd count.

## 3. `road_graph.py`: the map as a graph
**In one line:** 31 junctions (nodes) and 50 street pieces (edges) covering our 43 segments, with each edge storing its length and segment ID.

- **"Do the routes follow real roads?"** Yes. The real street network was downloaded from **OpenStreetMap** with `osmnx`, using a GitHub Action. `tools/build_road_shapes.py` lines up our hand-drawn map with OSM using 8 known crossings (an *affine transform*, about 20 m error), snaps each junction onto its real road, and makes every segment follow the real street shape (*shortest path along OSM streets*).

## 4. `fuzzy_labels.py`: fuzzy logic
**In one line:** it turns a risk number into words like "risky after 9 PM" without hard cut-offs.

- **"How does it work?"** Fuzzify (risk low/medium/high, women few/many), apply rules like "IF risk medium AND few women THEN danger high", then defuzzify with a weighted average (Sugeno style).
- **"Why not just a threshold?"** With a threshold, 0.49 is fine and 0.51 is risky, which is unrealistic. Fuzzy logic blends smoothly. Demo: the same risk (0.5) gives danger 6.0 with no women around but 4.3 with 5 women per minute.

## 5. `routing.py`: A\* search
**In one line:** cost = length × (1 + weight × risk), and A\* finds the cheapest route for the fastest (0), balanced (3) and safety-first (10) weights.

- **"Is your heuristic admissible?"** Yes. h = straight-line distance, and every street's cost is at least its length, which is at least the straight-line distance, so h never overestimates. That means A\* is optimal.
- **"How do you know your A\* is correct?"** For every one of the 465 start/goal pairs, the code checks that our A\* cost equals networkx's Dijkstra cost.
- **"Is A\* better than Dijkstra here?"** Same answer, less work: A\* expanded about 10.5 junctions on average vs 16 for Dijkstra.
- **"Why not the genetic algorithm from your plan?"** On a 31-node map, A\* is exact and instant. A GA gives good but not guaranteed answers and needs tuning. We kept the GA plan's idea of 3 preference weights.
- **The best demo example (11 PM, Hafeez Centre → Tipu Road north, the app's default; tick all three boxes):** the fastest route is 1,499 m through lane L4 (risk 0.46). The balanced route is 1,790 m via Ghalib Road and MM Alam (risk 0.21). The safety-first route is 1,928 m via Tipu Road (risk 0.18). More safety costs more walking, and that's the **trade-off**.
- **"Why can't one route be fastest AND safest?"** Sometimes it is: then all ticked routes overlap and the app says so. When the shortcut uses a risky street, no route can be both, so the user picks the trade-off.

## 6. `app.py`: the demo
**In one line:** pick From, To, time and mode, and the app shows a map with coloured streets, the route, and why it was chosen.

- To deploy it: push this folder to GitHub, sign in at share.streamlit.io, choose New app, and pick `app.py`. It's free.
