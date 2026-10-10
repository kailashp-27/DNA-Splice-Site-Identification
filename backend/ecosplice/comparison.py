"""Repeated warm computations on identical input, with counters and quality."""
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import random
from statistics import median

import numpy as np

from .algorithms import METHODS, analyze
from .evaluation import binary_metrics
from .model import sha256


def labelled_quality(candidates, provenance):
    annotations = provenance.get("annotations")
    if annotations is None:
        return None
    result = {"scope": "All canonical motif candidates in this oriented input, including unscored edges; absent annotations mean unannotated.",
              "annotation_scope": provenance["annotation_scope"]}
    for kind in ("donor", "acceptor"):
        known = {site["position1"] for site in annotations if site["type"] == kind}
        sites = [site for site in candidates if site["type"] == kind]
        result[kind] = binary_metrics([site["position1"] in known for site in sites], [site["predicted"] for site in sites])
    return result


def compare(run, bundle, repeats=5):
    raw = run["input_sequence"]
    batch = run["analysis"]["batch_size"]
    power = run["energy"]["assumed_power_watts"]
    seed = 20261008
    rng = random.Random(seed)
    # Warm each operational path on this input, outside recorded trials.
    reference = None
    for method in METHODS:
        warm = analyze(raw, bundle, method, batch)
        if method == "exhaustive":
            reference = warm["candidates"]
    raw_trials = {method: [] for method in METHODS}
    quality, work, disagreement = {}, {}, {}
    orders = []
    maximum_difference = 0.
    for _ in range(repeats):
        order = list(METHODS)
        rng.shuffle(order)
        orders.append(order)
        for method in order:
            result = analyze(raw, bundle, method, batch)
            sites = result["candidates"]
            if len(sites) != len(reference):
                raise ValueError("Methods produced different canonical candidate sets.")
            changes = 0
            for site, expected in zip(sites, reference):
                if (site["position1"], site["type"], site["unavailable_reason"]) != (expected["position1"], expected["type"], expected["unavailable_reason"]):
                    raise ValueError("Methods disagree on coordinates/eligibility.")
                changes += site["predicted"] != expected["predicted"]
                if method != "adaptive":
                    difference = abs(site["score"] - expected["score"]) if site["score"] is not None else 0.
                    maximum_difference = max(maximum_difference, difference)
                    if difference > 1e-12 or site["predicted"] != expected["predicted"]:
                        raise ValueError("Exhaustive/filtered prediction agreement failed.")
            raw_trials[method].append(result["timing_ms"])
            work[method] = result["work"]
            quality[method] = labelled_quality(sites, run["input_provenance"])
            disagreement[method] = changes
    summaries = {}
    for method, stages in raw_trials.items():
        times = [stage["total_ms"] for stage in stages]
        q1, q3 = np.percentile(times, [25, 75])
        summaries[method] = {"median_ms": median(times), "min_ms": min(times), "max_ms": max(times),
                             "iqr_ms": float(q3 - q1), "raw_total_ms": times, "raw_stages_ms": stages,
                             "median_stages_ms": {key: median(stage[key] for stage in stages) for key in stages[0]},
                             "work": work[method], "quality": quality[method],
                             "prediction_disagreements_vs_exhaustive": disagreement[method],
                             "estimated_joules": power * median(times) / 1000}
    baseline = summaries["exhaustive"]
    for summary in summaries.values():
        summary["runtime_reduction_vs_exhaustive"] = 1 - summary["median_ms"] / baseline["median_ms"]
        summary["estimated_energy_reduction_vs_exhaustive"] = 1 - summary["estimated_joules"] / baseline["estimated_joules"] if baseline["estimated_joules"] else None
    eligible = work["filtered"]["eligible_candidates"]
    return {"schema_version": 1, "run_id": run["id"], "created_at": datetime.now(timezone.utc).isoformat(),
            "input": run["analysis"]["input"], "model_id": bundle.identity,
            "dataset_fingerprint": bundle.metadata["dataset_fingerprint"], "settings": run["analysis"]["settings"],
            "batch_size": batch, "repeats": repeats, "warmup_runs_per_method": 1, "seed": seed,
            "repetition_method_orders": orders, "methods": summaries,
            "baseline_filtered_max_score_difference": maximum_difference,
            "adaptive_detailed_evaluations_avoided": eligible - work["adaptive"]["detailed_evaluations"],
            "adaptive_detailed_work_reduction": 1 - work["adaptive"]["detailed_evaluations"] / eligible if eligible else None,
            "energy": {"assumed_power_watts": power, "formula": "assumed watts × median computation ms / 1000",
                       "assumption": "Constant assumed active power; estimated energy, not measured laptop power."},
            "hardware": {"os": platform.platform(), "cpu": platform.processor(), "logical_cpu_count": os.cpu_count()},
            "versions": {"python": platform.python_version(), "numpy": np.__version__},
            "code_sha256": {"algorithms.py": sha256(Path(__file__).with_name("algorithms.py")), "comparison.py": sha256(Path(__file__))},
            "timing_scope": "Fresh analysis-engine computations; model and operational warm-up excluded; no HTTP, serialization, SQLite or UI time. Methods run sequentially in shuffled order.",
            "quality_scope": "Canonical candidates including unscored edges; no accuracy without annotation labels. Disagreement is relative to exhaustive predictions, not biological truth."}
