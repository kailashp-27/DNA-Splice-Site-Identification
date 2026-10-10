"""Operational parity, held-out demo pipeline quality and repeated real timings."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import platform
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
import numpy as np
from ecosplice.algorithms import METHODS, analyze
from ecosplice.evaluation import binary_metrics
from ecosplice.model import ModelBundle, sha256


def quality(result, annotations, length):
    metrics = {}
    for kind in ("donor", "acceptor"):
        truth = np.zeros(length - 1, dtype=bool)
        predicted = np.zeros(length - 1, dtype=bool)
        for annotation in annotations:
            if annotation["type"] == kind:
                truth[annotation["position1"] - 1] = True
        for site in result["candidates"]:
            if site["type"] == kind and site["predicted"]:
                predicted[site["position1"] - 1] = True
        metrics[kind] = binary_metrics(truth, predicted)
        metrics[kind]["unscoreable_annotated_sites"] = sum(a["type"] == kind and not a["scorable"] for a in annotations)
    return metrics


def parity(baseline, filtered):
    if len(baseline["candidates"]) != len(filtered["candidates"]):
        raise AssertionError("Canonical candidate counts disagree.")
    difference = 0.
    for left, right in zip(baseline["candidates"], filtered["candidates"]):
        for key in ("position1", "type", "motif", "predicted", "unavailable_reason"):
            if left[key] != right[key]:
                raise AssertionError(f"Baseline/filtered disagree: {key}")
        if (left["score"] is None) != (right["score"] is None):
            raise AssertionError("Baseline/filtered score eligibility differs.")
        if left["score"] is not None:
            difference = max(difference, abs(left["score"] - right["score"]))
    if difference > 1e-12:
        raise AssertionError(f"Baseline/filtered score difference: {difference}")
    return difference


def measure(sequence, bundle, repeats, batch_size, rng):
    warm = {method: analyze(sequence, bundle, method, batch_size) for method in METHODS}
    difference = parity(warm["exhaustive"], warm["filtered"])
    timings, stage_timings, order_log = {m: [] for m in METHODS}, {m: [] for m in METHODS}, []
    for repeat in range(repeats):
        order = list(METHODS)
        rng.shuffle(order)
        order_log.append(order)
        for method in order:
            result = analyze(sequence, bundle, method, batch_size)
            timings[method].append(result["timing_ms"]["total_ms"])
            stage_timings[method].append(result["timing_ms"])
    report = {}
    for method in METHODS:
        values = timings[method]
        report[method] = {"median_ms": statistics.median(values), "min_ms": min(values), "max_ms": max(values),
                          "iqr_ms": float(np.percentile(values, 75) - np.percentile(values, 25)),
                          "raw_total_ms": values, "raw_stages_ms": stage_timings[method], "work": warm[method]["work"]}
    return {"length": len(sequence), "sha256": hashlib.sha256(sequence.encode()).hexdigest(), "results": report,
            "baseline_filtered_max_score_difference": difference, "repetition_method_orders": order_log}, warm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=ROOT / "models/ecosplice-v1")
    parser.add_argument("--output", type=Path, default=ROOT / "results/algorithm-verification.json")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=512)
    args = parser.parse_args()
    if args.repeats < 3:
        parser.error("Use at least three repetitions.")
    bundle = ModelBundle.load(args.model)
    demos = json.loads((ROOT / "data/processed/demo_samples.json").read_text())
    rng, inputs, demo_predictions = random.Random(20261006), [], []
    for demo in demos:
        print(f"Checking {demo['id']} / {demo['name']}...", flush=True)
        measured, warm = measure(demo["sequence"], bundle, args.repeats, args.batch_size, rng)
        measured.update(id=demo["id"], source=demo["source"], gene_id=demo["gene_id"],
                        split="test", strand=demo["genomic_region"]["strand"],
                        quality={method: quality(warm[method], demo["annotations"], len(demo["sequence"])) for method in METHODS})
        inputs.append(measured)
        demo_predictions.append({"sample_id": demo["id"], "genomic_region": demo["genomic_region"],
                                 "annotations": demo["annotations"], "filtered": warm["filtered"], "adaptive": warm["adaptive"]})
    # Maximum-size checks include dense and empty motifs; synthetic stress data has no biological metrics.
    for identity, sequence in (("stress-motif-free", "ACCT" * 25000), ("stress-motif-rich", "GTAG" * 25000)):
        print(f"Checking {identity}, 100,000 bases...", flush=True)
        measured, _ = measure(sequence, bundle, args.repeats, args.batch_size, rng)
        measured.update(id=identity, source="Explicit synthetic stress input; no biological ground truth")
        inputs.append(measured)
    report = {"schema_version": 1, "model_id": bundle.identity, "model_manifest_sha256": sha256(args.model / "manifest.json"),
              "dataset_fingerprint": bundle.metadata["dataset_fingerprint"], "repeats": args.repeats, "batch_size": args.batch_size,
              "seed": 20261006, "hardware": {"os": platform.platform(), "cpu": os.environ.get("PROCESSOR_IDENTIFIER", platform.processor()),
                                            "logical_cpu_count": os.cpu_count()},
              "versions": {"python": platform.python_version(), "numpy": np.__version__}, "inputs": inputs,
              "code_sha256": {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in
                              (Path(__file__), ROOT / "backend/ecosplice/algorithms.py", ROOT / "backend/ecosplice/model.py")},
              "timing_scope": "Input validation, scan, context preparation, feature encoding, inference and result construction. Loaded model; warm-up excluded; fresh computation every trial; shuffled order; no network/UI latency.",
              "quality_scope": "Four held-out cropped genomic demos. Canonical annotations only; unscoreable annotated edges count as false negatives. Unannotated is not experimentally proven inactive. Sampled-window metrics remain in model-evaluation.json.",
              "stage_scope": "Inference stages include DNA encoding and coefficient summation; context stage extracts/checks windows. Timing counters themselves add overhead.",
              "memory_scope": "Batch window count is verified, not a measurement of resident RAM.",
              "energy_scope": "No laptop power measurement; energy integration remains Part 4."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    (args.output.parent / "demo-predictions.json").write_text(json.dumps(demo_predictions, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("All baseline/filtered parity checks passed, including 100,000-base stress inputs.", flush=True)


if __name__ == "__main__":
    main()
