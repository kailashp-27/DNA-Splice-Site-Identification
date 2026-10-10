"""Reproducible CPU training. Freeze validation choices before opening test results."""
from pathlib import Path
import argparse
from collections import Counter
import hashlib
import json
import platform
import sys
from time import perf_counter
import warnings

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
import numpy as np
import scipy
from scipy.sparse import csr_matrix
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

from ecosplice.model import (CLASSES, CLASS_INDEX, LinearScorer, ModelBundle, encode_contexts, feature_indices, sha256)
from ecosplice.evaluation import (adaptive_scores, binary_metrics, choose_routing, choose_thresholds,
                                  evaluate_scores, motif_masks)

SEED = 20261006


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def read_split(directory, split):
    contexts, labels = [], []
    with (directory / "windows.jsonl").open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row["split"] == split:
                contexts.append(row["context"])
                labels.append(CLASS_INDEX[row["label"]])
    return contexts, np.array(labels, dtype=np.int64)


def design_matrix(codes, flank, pairs):
    indices, dimension = feature_indices(codes, flank, pairs)
    count, active = indices.shape
    return csr_matrix((np.ones(indices.size, dtype=np.float64), indices.reshape(-1),
                       np.arange(count + 1, dtype=np.int32) * active), shape=(count, dimension))


def score_batched(scorer, codes, batch_size=512):
    return np.concatenate([scorer.score_codes(codes[i:i + batch_size]) for i in range(0, len(codes), batch_size)])


def fit(codes, labels, flank, pairs, name):
    print(f"Training {name}: flank={flank}, adjacent-pair features={pairs}...", flush=True)
    matrix = design_matrix(codes, flank, pairs)
    estimator = LogisticRegression(C=1., solver="lbfgs", max_iter=400, tol=1e-5, random_state=SEED)
    start = perf_counter()
    with threadpool_limits(limits=1), warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        estimator.fit(matrix, labels)
    seconds = perf_counter() - start
    if list(estimator.classes_) != [0, 1, 2]:
        raise ValueError("Training class order is incompatible with model export.")
    weights, intercept = estimator.coef_, estimator.intercept_
    identity = f"{name}-" + hashlib.sha256(weights.tobytes() + intercept.tobytes()).hexdigest()[:12]
    scorer = LinearScorer(weights, intercept, flank, pairs, identity)
    check = scorer.score_codes(codes[:512])
    np.testing.assert_allclose(check, estimator.predict_proba(matrix[:512]), atol=1e-12, rtol=1e-12)
    return scorer, {"iterations": int(estimator.n_iter_.max()), "training_seconds": seconds,
                    "features": matrix.shape[1], "active_features_per_window": matrix.getnnz(axis=1)[0].item(),
                    "export_matches_sklearn_atol": 1e-12}


def report_split(labels, preliminary, detailed, masks, thresholds, routing):
    decisions, routes = adaptive_scores(preliminary, detailed, masks, routing, thresholds)
    return {
        "class_counts": {kind: int(np.sum(labels == index)) for index, kind in enumerate(CLASSES)},
        "detailed": evaluate_scores(labels, detailed, masks, thresholds["detailed"]),
        "preliminary": evaluate_scores(labels, preliminary, masks, thresholds["preliminary"]),
        "motif_only": {kind: binary_metrics(labels == CLASS_INDEX[kind], mask) for kind, mask in masks.items()},
        "adaptive": {kind: {"canonical_candidates": binary_metrics((labels == CLASS_INDEX[kind])[mask], decisions[kind][mask]),
                             "all_sampled_positions": binary_metrics(labels == CLASS_INDEX[kind], decisions[kind]),
                             "routes": routes[kind]} for kind, mask in masks.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/processed")
    parser.add_argument("--output", type=Path, default=ROOT / "models/ecosplice-v1")
    parser.add_argument("--report", type=Path, default=ROOT / "results/model-evaluation.json")
    args = parser.parse_args()
    manifest = json.loads((args.dataset / "manifest.json").read_text())
    for filename, expected in manifest["files"].items():
        if sha256(args.dataset / filename) != expected:
            raise ValueError(f"Frozen dataset checksum mismatch: {filename}")
    train_contexts, train_labels = read_split(args.dataset, "train")
    validation_contexts, validation_labels = read_split(args.dataset, "validation")
    train_codes, validation_codes = encode_contexts(train_contexts), encode_contexts(validation_contexts)
    preliminary, light_fit = fit(train_codes, train_labels, 10, False, "preliminary-lr22-v1")
    detailed, heavy_fit = fit(train_codes, train_labels, 50, True, "detailed-lr102pairs-v1")
    validation_light = score_batched(preliminary, validation_codes)
    validation_heavy = score_batched(detailed, validation_codes)
    masks = motif_masks(validation_contexts)
    light_thresholds, light_curves = choose_thresholds(validation_labels, validation_light, masks)
    heavy_thresholds, heavy_curves = choose_thresholds(validation_labels, validation_heavy, masks)
    thresholds = {"preliminary": light_thresholds, "detailed": heavy_thresholds}
    routing, routing_selection = choose_routing(validation_labels, validation_light, validation_heavy, masks, thresholds)
    validation = report_split(validation_labels, validation_light, validation_heavy, masks, thresholds, routing)
    if np.mean([validation["detailed"][k]["canonical_candidates"]["f1"] for k in masks]) <= np.mean([validation["preliminary"][k]["canonical_candidates"]["f1"] for k in masks]):
        raise ValueError("Detailed candidate did not outperform the cheaper reference on validation; reconsider model design without consulting test.")
    args.output.mkdir(parents=True, exist_ok=True)
    specs = {}
    for name, scorer in (("preliminary", preliminary), ("detailed", detailed)):
        path = args.output / f"{name}.npz"
        np.savez_compressed(path, weights=scorer.weights, intercept=scorer.intercept)
        specs[name] = {"id": scorer.identity, "flank": scorer.flank, "pairs": scorer.pairs, "sha256": sha256(path)}
    identity_payload = json.dumps({"scorers": specs, "thresholds": thresholds, "routing": routing}, sort_keys=True).encode()
    metadata = {
        "schema_version": 1, "model_id": "ecosplice-v1-" + hashlib.sha256(identity_payload).hexdigest()[:12],
        "classes": list(CLASSES), "context_width": 102, "scorers": specs, "thresholds": thresholds,
        "routing": routing, "dataset_id": manifest["dataset_id"], "dataset_fingerprint": manifest["dataset_fingerprint"],
        "dataset_manifest_sha256": sha256(args.dataset / "manifest.json"), "windows_sha256": manifest["files"]["windows.jsonl"],
        "score_meaning": "Softmax model score under sampled training class balance; not a calibrated biological probability.",
        "training": {"seed": SEED, "solver": "lbfgs", "C": 1., "max_iter": 400, "tol": 1e-5, "threads": 1,
                     "class_weight": None, "fit_split": "train", "threshold_and_routing_split": "validation",
                     "routing_constraint": "Per type, validation F1 loss <=0.005 and recall loss <=0.01 relative to detailed; maximise avoided evaluations.",
                     "model_choice": "Full-window position-specific single-base and adjacent-pair logistic regression versus short-window single-base reference; retain detailed only if validation macro F1 improves."},
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__},
        "code_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in
                        (Path(__file__), ROOT / "backend/ecosplice/model.py", ROOT / "backend/ecosplice/evaluation.py")}}
    # Freeze and persist all choices BEFORE computing held-out test scores.
    write_json(args.output / "manifest.json", metadata)
    bundle = ModelBundle.load(args.output)
    np.testing.assert_allclose(bundle.detailed.score(validation_contexts[:32]), validation_heavy[:32], atol=1e-12)
    print("Validation choices frozen. Evaluating held-out test once...", flush=True)
    test_contexts, test_labels = read_split(args.dataset, "test")
    test_codes = encode_contexts(test_contexts)
    test_light, test_heavy = score_batched(bundle.preliminary, test_codes), score_batched(bundle.detailed, test_codes)
    test = report_split(test_labels, test_light, test_heavy, motif_masks(test_contexts), thresholds, routing)
    report = {"schema_version": 1, "model_id": bundle.identity, "dataset_fingerprint": manifest["dataset_fingerprint"],
              "thresholds": thresholds, "routing": routing, "routing_selection_validation_only": routing_selection,
              "training": {"preliminary": light_fit, "detailed": heavy_fit}, "validation": validation, "test": test,
              "validation_threshold_curves": {"preliminary": light_curves, "detailed": heavy_curves},
              "test_threshold_curves": {name: choose_thresholds(test_labels, scores, motif_masks(test_contexts))[1]
                                        for name, scores in (("preliminary", test_light), ("detailed", test_heavy))},
              "test_curves_use": "Descriptive only; selected thresholds were frozen on validation before test was scored.",
              "scope": "Sampled chr22 annotated canonical sites/non-sites, not genome-wide or clinical validation.",
              "test_access_policy": "Choices frozen before opening test results; do not tune from test/demo outcomes."}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.report, report)
    print(json.dumps({"model_id": bundle.identity, "thresholds": thresholds, "routing": routing,
                      "test_f1": {k: test["detailed"][k]["canonical_candidates"]["f1"] for k in masks},
                      "test_adaptive_f1": {k: test["adaptive"][k]["canonical_candidates"]["f1"] for k in masks}}, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, ConvergenceWarning) as error:
        raise SystemExit(f"Model training failed: {error}") from error
