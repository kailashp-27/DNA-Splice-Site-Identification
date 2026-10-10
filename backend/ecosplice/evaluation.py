"""Metrics and threshold/routing selection. Call selection on validation only."""
import numpy as np

from .model import CLASS_INDEX


def binary_metrics(truth, predicted):
    truth, predicted = np.asarray(truth, dtype=bool), np.asarray(predicted, dtype=bool)
    if truth.shape != predicted.shape:
        raise ValueError("Labels and predictions must have the same shape.")
    tp = int(np.sum(truth & predicted))
    fp = int(np.sum(~truth & predicted))
    fn = int(np.sum(truth & ~predicted))
    tn = int(np.sum(~truth & ~predicted))
    precision = tp / (tp + fp) if tp + fp else 0.
    recall = tp / (tp + fn) if tp + fn else 0.
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "support": int(truth.sum()),
            "count": len(truth), "precision": precision, "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.,
            "accuracy": (tp + tn) / len(truth) if len(truth) else 0.}


def motif_masks(contexts):
    return {kind: np.array([context[50:52] == motif for context in contexts])
            for kind, motif in (("donor", "GT"), ("acceptor", "AG"))}


def choose_thresholds(labels, scores, masks):
    chosen, curves = {}, {}
    for kind, mask in masks.items():
        truth = labels[mask] == CLASS_INDEX[kind]
        values = scores[mask, CLASS_INDEX[kind]]
        curve = [{"threshold": float(t), **binary_metrics(truth, values >= t)} for t in np.linspace(.01, .99, 99)]
        # Highest F1, then precision, then higher threshold; deterministic ties.
        best = max(curve, key=lambda m: (m["f1"], m["precision"], m["threshold"]))
        chosen[kind], curves[kind] = best["threshold"], curve
    return chosen, curves


def calibration_summary(truth, values):
    truth, values = np.asarray(truth, dtype=float), np.asarray(values, dtype=float)
    bins = []
    for i in range(10):
        mask = (values >= i / 10) & (values <= 1 if i == 9 else values < (i + 1) / 10)
        if mask.any():
            bins.append({"low": i / 10, "high": (i + 1) / 10, "count": int(mask.sum()),
                         "mean_score": float(values[mask].mean()), "positive_fraction": float(truth[mask].mean())})
    return {"brier_score": float(np.mean((values - truth) ** 2)), "bins": bins,
            "interpretation": "Descriptive calibration on the sampled dataset only; scores are not calibrated genome-wide probabilities."}


def evaluate_scores(labels, scores, masks, thresholds):
    result = {}
    for kind, mask in masks.items():
        truth = labels == CLASS_INDEX[kind]
        predicted = mask & (scores[:, CLASS_INDEX[kind]] >= thresholds[kind])
        result[kind] = {
            "canonical_candidates": binary_metrics(truth[mask], predicted[mask]),
            "all_sampled_positions": binary_metrics(truth, predicted),
            "calibration_on_candidates": calibration_summary(truth[mask], scores[mask, CLASS_INDEX[kind]])}
    return result


def choose_routing(labels, preliminary, detailed, masks, thresholds):
    policy, selected = {}, {}
    for kind, mask in masks.items():
        truth = labels[mask] == CLASS_INDEX[kind]
        light, heavy = preliminary[mask, CLASS_INDEX[kind]], detailed[mask, CLASS_INDEX[kind]]
        lt, ht = thresholds["preliminary"][kind], thresholds["detailed"][kind]
        reference = binary_metrics(truth, heavy >= ht)
        choices = []
        for lower_fraction in (0., .05, .1, .25, .5, .75, .9, 1.):
            for upper_fraction in (0., .1, .25, .5, .75, .9, 1.):
                low, high = lt * lower_fraction, lt + (1 - lt) * upper_fraction
                fast = (light <= low) | (light >= high)
                decision = np.where(fast, light >= lt, heavy >= ht)
                metrics = binary_metrics(truth, decision)
                if metrics["f1"] >= reference["f1"] - .005 and metrics["recall"] >= reference["recall"] - .01:
                    choices.append({"low": low, "high": high, "avoided": int(fast.sum()), "metrics": metrics})
        # (0,1) routes every finite non-extreme softmax score to detailed; safe fallback.
        best = max(choices, key=lambda c: (c["avoided"], c["metrics"]["f1"], c["high"] - c["low"]))
        policy[kind] = {"low": best["low"], "high": best["high"]}
        selected[kind] = {"detailed_reference": reference, **best, "candidates": int(mask.sum())}
    return policy, selected


def adaptive_scores(preliminary, detailed, masks, routing, thresholds):
    """Evaluation helper uses precomputed arrays; operational routing lives in algorithms.py."""
    decisions, routed = {}, {}
    for kind, mask in masks.items():
        light = preliminary[:, CLASS_INDEX[kind]]
        fast = mask & ((light <= routing[kind]["low"]) | (light >= routing[kind]["high"]))
        decision = np.where(fast, light >= thresholds["preliminary"][kind],
                            detailed[:, CLASS_INDEX[kind]] >= thresholds["detailed"][kind]) & mask
        decisions[kind], routed[kind] = decision, {"preliminary_final": int(fast.sum()), "detailed_final": int((mask & ~fast).sum())}
    return decisions, routed
