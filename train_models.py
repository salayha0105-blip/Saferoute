"""
Safe Route Lahore - Step 2: train and compare the safety models
================================================================

WHAT THIS FILE DOES:
  It teaches the computer to look at a street's features (lighting, shops,
  cameras, crowd...) and guess its label: risky / moderate / safe.
  We try THREE methods and compare them fairly:

    1. Rule-based baseline   - a few "common sense" if/else rules I wrote by hand.
                                Any AI method must beat this to be worth using.
    2. Decision tree         - machine learning (course Week XII). Learns
                                if/else questions from the data by itself.
    3. Naive Bayes           - probabilistic reasoning. Uses Bayes' rule to
                                estimate P(label | features).

HOW WE TEST FAIRLY (important, Dr. Sidra may ask):
  We use "GroupKFold" cross-validation, grouped by segment_id.
  That means: if MM Alam segment MM2 is in the TEST set, none of MM2's rows
  are in the TRAINING set. So the model is tested on streets it has never
  seen, which is the real situation when you add a new street.
  If we split rows randomly, the same street (on other nights) would leak
  into training and the score would look better than it really is.

Run:      python train_models.py
Creates:  results/metrics.json            (all the scores)
          results/confusion_matrices.png  (where each model gets confused)
          results/decision_tree.png       (picture of the learned tree)
          results/feature_importance.png  (which features matter most)
          models/decision_tree.joblib     (the final trained model)
          segment_risk.csv                (predicted risk for every segment
                                           and time slot, used by the app)
"""

import json
import os

import joblib
import matplotlib
matplotlib.use("Agg")                 # draw pictures to files, no screen needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier, plot_tree

DATA_FILE = "safe_route_synthetic.csv"
LABELS = ["risky", "moderate", "safe"]   # fixed order for every table and chart
SEED = 42

# ---------------------------------------------------------------------------
# Which columns the models are allowed to see
# ---------------------------------------------------------------------------
# We turn "slot" into a number (hour of the night) so models can use it.
# We do NOT give the models: the ratings, mean_rating, hidden_score or label,
# because those ARE the answer. Giving them would be cheating ("leakage").
FEATURES = [
    "hour", "weekend_yn",
    "footpath_yn", "safe_city_camera_yn", "private_cctv_count",
    "police_yn", "guards_yn", "dead_frontage_yn", "isolated_spot_yn",
    "ride_stand_yn", "lighting_0to2", "shops_open", "per_minute",
    "women_per_minute",
]
SLOT_TO_HOUR = {"6pm": 18, "9pm": 21, "11pm": 23}


def load_data():
    data = pd.read_csv(DATA_FILE)
    data["hour"] = data["slot"].map(SLOT_TO_HOUR)
    return data


# ---------------------------------------------------------------------------
# Method 1: the rule-based baseline (no learning at all)
# ---------------------------------------------------------------------------
# These are the rules a sensible person might write without any data:
#   - dark street, or a hidden corner with almost nobody around -> risky
#   - bright street with shops open and women around             -> safe
#   - anything else                                              -> moderate
def rule_based_baseline(row):
    if row["lighting_0to2"] == 0 or (row["isolated_spot_yn"] == 1 and row["per_minute"] < 5):
        return "risky"
    if row["lighting_0to2"] == 2 and row["shops_open"] >= 3 and row["women_per_minute"] >= 2:
        return "safe"
    return "moderate"


# ---------------------------------------------------------------------------
# Choosing the tree's depth
# ---------------------------------------------------------------------------
# A very deep tree memorises the training data (overfitting); a very shallow
# one is too simple (underfitting). We try depths 2-8 and keep the best one,
# judged by cross-validation. A shallow tree is also easier to explain.
def choose_tree_depth(X, y, groups):
    cv = GroupKFold(n_splits=5)
    best_depth, best_f1 = None, -1
    scores = {}
    for depth in range(2, 9):
        f1s = []
        for train_idx, test_idx in cv.split(X, y, groups):
            tree = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=10,
                                          random_state=SEED)
            tree.fit(X.iloc[train_idx], y.iloc[train_idx])
            pred = tree.predict(X.iloc[test_idx])
            f1s.append(f1_score(y.iloc[test_idx], pred, average="macro"))
        scores[depth] = round(float(np.mean(f1s)), 3)
        if scores[depth] > best_f1 + 0.005:   # only go deeper if it clearly helps
            best_depth, best_f1 = depth, scores[depth]
    return best_depth, scores


def main():
    os.makedirs("results", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    data = load_data()
    X, y, groups = data[FEATURES], data["label"], data["segment_id"]

    depth, depth_scores = choose_tree_depth(X, y, groups)
    print(f"Best tree depth: {depth}   (macro-F1 per depth: {depth_scores})")

    # ---- cross-validation: every row gets predicted once, by a model
    # ---- that never saw its street during training
    cv = GroupKFold(n_splits=5)
    predictions = {"Rule-based baseline": pd.Series(index=data.index, dtype=object),
                   "Decision tree": pd.Series(index=data.index, dtype=object),
                   "Naive Bayes": pd.Series(index=data.index, dtype=object)}

    for train_idx, test_idx in cv.split(X, y, groups):
        X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
        X_test = X.iloc[test_idx]

        tree = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=10, random_state=SEED)
        tree.fit(X_train, y_train)
        predictions["Decision tree"].iloc[test_idx] = tree.predict(X_test)

        nb = GaussianNB()
        nb.fit(X_train, y_train)
        predictions["Naive Bayes"].iloc[test_idx] = nb.predict(X_test)

        predictions["Rule-based baseline"].iloc[test_idx] = X_test.apply(rule_based_baseline, axis=1)

    # ---- scores ----
    # Accuracy  = % of rows labelled correctly.
    # Macro-F1  = average F1 over the 3 classes, so the small "moderate" class
    #             counts as much as the big ones. Better than accuracy when
    #             classes are unbalanced.
    # Risky recall = of all truly risky street-times, how many did we catch?
    #             This matters most: calling a risky street "safe" is the
    #             worst mistake for our users.
    metrics = {"tree_depth": depth, "depth_search_macro_f1": depth_scores, "models": {}}
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, (name, pred) in zip(axes, predictions.items()):
        cm = confusion_matrix(y, pred, labels=LABELS)
        risky_recall = cm[0, 0] / cm[0].sum()
        risky_called_safe = int(cm[0, 2])
        metrics["models"][name] = {
            "accuracy": round(accuracy_score(y, pred), 3),
            "macro_f1": round(f1_score(y, pred, average="macro"), 3),
            "risky_recall": round(float(risky_recall), 3),
            "risky_called_safe": risky_called_safe,
        }
        ax.imshow(cm, cmap="Blues")
        ax.set_xticks(range(3), LABELS)
        ax.set_yticks(range(3), LABELS)
        ax.set_xlabel("predicted")
        ax.set_ylabel("true")
        ax.set_title(name)
        for i in range(3):
            for j in range(3):
                ax.text(j, i, cm[i, j], ha="center", va="center",
                        color="white" if cm[i, j] > cm.max() / 2 else "black")
    plt.tight_layout()
    plt.savefig("results/confusion_matrices.png", dpi=130)
    plt.close()

    print("\nCross-validated results (tested on unseen streets):")
    print(pd.DataFrame(metrics["models"]).T.to_string())

    # ---- final model: train the tree on ALL data for use in the app ----
    final_tree = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=10, random_state=SEED)
    final_tree.fit(X, y)
    joblib.dump({"model": final_tree, "features": FEATURES}, "models/decision_tree.joblib")

    # Picture of the tree (this is the "explainable" part)
    plt.figure(figsize=(22, 10))
    plot_tree(final_tree, feature_names=FEATURES, class_names=list(final_tree.classes_),
              filled=True, rounded=True, fontsize=8, max_depth=3)
    plt.title("Decision tree (top 3 levels shown)")
    plt.savefig("results/decision_tree.png", dpi=110, bbox_inches="tight")
    plt.close()

    # Which features the tree relied on most
    importance = pd.Series(final_tree.feature_importances_, index=FEATURES).sort_values()
    importance.plot.barh(figsize=(7, 5), color="#4a7bd0")
    plt.title("Decision tree feature importance")
    plt.tight_layout()
    plt.savefig("results/feature_importance.png", dpi=130)
    plt.close()
    metrics["feature_importance"] = importance.sort_values(ascending=False).round(3).to_dict()

    with open("results/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # ---- segment risk table for the route planner ----
    # For every segment and slot we average the tree's probabilities over the
    # 10 nights. risk = P(risky) + 0.5 * P(moderate), a number from 0 (safe)
    # to 1 (risky). The route planner uses this as the "danger" of a street.
    proba = pd.DataFrame(final_tree.predict_proba(X), columns=final_tree.classes_)
    proba["segment_id"] = data["segment_id"]
    proba["slot"] = data["slot"]
    proba["women_per_minute"] = data["women_per_minute"]
    proba["lighting_0to2"] = data["lighting_0to2"]
    table = proba.groupby(["segment_id", "slot"]).mean().reset_index()
    table["risk"] = (table["risky"] + 0.5 * table["moderate"]).round(3)
    table = table.rename(columns={"risky": "p_risky", "moderate": "p_moderate", "safe": "p_safe"})
    table.round(3).to_csv("segment_risk.csv", index=False)
    print("\nSaved results/, models/decision_tree.joblib and segment_risk.csv")


if __name__ == "__main__":
    main()
