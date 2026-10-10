"""Three actual processing methods; identical eligibility and canonical output scope."""
from time import perf_counter_ns
import hashlib

from .model import CLASS_INDEX
from .sequence import FLANK, context_at, parse_sequence

METHODS = ("exhaustive", "filtered", "adaptive")


def analyze(raw, bundle, method="filtered", batch_size=512):
    if method not in METHODS:
        raise ValueError("Method must be exhaustive, filtered, or adaptive.")
    if not isinstance(batch_size, int) or not 1 <= batch_size <= 8192:
        raise ValueError("Batch size must be between 1 and 8192.")
    start = perf_counter_ns()
    parsed = parse_sequence(raw)
    sequence = parsed["sequence"]
    sequence_hash = hashlib.sha256(sequence.encode("ascii")).hexdigest()
    stages = {"input_ms": (perf_counter_ns() - start) / 1e6, "scan_ms": 0., "context_ms": 0.,
              "preliminary_inference_ms": 0., "detailed_inference_ms": 0.}
    tick = perf_counter_ns()
    candidates = {}
    for index in range(len(sequence) - 1):
        motif = sequence[index:index + 2]
        if motif in ("GT", "AG"):
            kind = "donor" if motif == "GT" else "acceptor"
            candidates[index] = {"id": f"C-{index + 1}", "position1": index + 1, "type": kind, "motif": motif,
                                 "score": None, "preliminary_score": None, "threshold": None,
                                 "predicted": False, "route": "unscored", "scorer": None, "unavailable_reason": None}
    stages["scan_ms"] = (perf_counter_ns() - tick) / 1e6
    work = {"scanned_positions": len(sequence) - 1, "canonical_candidates": len(candidates),
            "context_positions_considered": 0, "eligible_candidates": 0, "unscored_candidates": 0,
            "preliminary_evaluations": 0, "detailed_evaluations": 0, "preliminary_final": 0,
            "detailed_final": 0, "peak_batch_windows": 0}

    def finish(index, score, scorer_name, preliminary_score=None):
        site = candidates[index]
        kind = site["type"]
        threshold = bundle.thresholds[scorer_name][kind]
        site.update(score=float(score), preliminary_score=preliminary_score, threshold=threshold,
                    predicted=bool(score >= threshold), route="fast" if scorer_name == "preliminary" else "detailed",
                    scorer=getattr(bundle, scorer_name).identity)
        work[scorer_name + "_final"] += 1

    def process(indices, contexts):
        if not contexts:
            return
        work["peak_batch_windows"] = max(work["peak_batch_windows"], len(contexts))
        if method != "adaptive":
            tick = perf_counter_ns()
            scores = bundle.detailed.score(contexts)
            stages["detailed_inference_ms"] += (perf_counter_ns() - tick) / 1e6
            work["detailed_evaluations"] += len(contexts)
            for index, values in zip(indices, scores):
                if index in candidates:
                    finish(index, values[CLASS_INDEX[candidates[index]["type"]]], "detailed")
            return
        tick = perf_counter_ns()
        preliminary = bundle.preliminary.score(contexts)
        stages["preliminary_inference_ms"] += (perf_counter_ns() - tick) / 1e6
        work["preliminary_evaluations"] += len(contexts)
        uncertain, pending_contexts, pending_indices = [], [], []
        for index, context, values in zip(indices, contexts, preliminary):
            kind = candidates[index]["type"]
            value = float(values[CLASS_INDEX[kind]])
            low, high = bundle.routing[kind]["low"], bundle.routing[kind]["high"]
            if value <= low or value >= high:
                finish(index, value, "preliminary", value)
            else:
                pending_contexts.append(context)
                pending_indices.append(index)
                uncertain.append(value)
        if pending_contexts:
            tick = perf_counter_ns()
            detailed = bundle.detailed.score(pending_contexts)
            stages["detailed_inference_ms"] += (perf_counter_ns() - tick) / 1e6
            work["detailed_evaluations"] += len(pending_contexts)
            for index, values, value in zip(pending_indices, detailed, uncertain):
                finish(index, values[CLASS_INDEX[candidates[index]["type"]]], "detailed", value)

    indices, contexts = [], []
    positions = range(len(sequence) - 1) if method == "exhaustive" else candidates.keys()
    for index in positions:
        tick = perf_counter_ns()
        work["context_positions_considered"] += 1
        context = context_at(sequence, index)
        if index in candidates:
            if context is None:
                reason = "sequence_edge" if index < FLANK or index + 2 + FLANK > len(sequence) else "unknown_context"
                candidates[index]["unavailable_reason"] = reason
                work["unscored_candidates"] += 1
            else:
                work["eligible_candidates"] += 1
        if context is not None:
            indices.append(index)
            contexts.append(context)
        stages["context_ms"] += (perf_counter_ns() - tick) / 1e6
        if len(contexts) == batch_size:
            process(indices, contexts)
            indices, contexts = [], []
    process(indices, contexts)
    total = (perf_counter_ns() - start) / 1e6
    stages["other_ms"] = max(0., total - sum(stages.values()))
    return {"schema_version": 1, "method": method, "input": {"name": parsed["name"], "length": len(sequence),
            "sha256": sequence_hash},
            "coordinate_convention": "1-based motif start in the oriented input sequence",
            "model_id": bundle.identity, "score_meaning": "Model score; not a calibrated biological probability",
            "dataset_fingerprint": bundle.metadata["dataset_fingerprint"],
            "settings": {"thresholds": bundle.thresholds, "routing": bundle.routing, "context_width": 102,
                         "orientation": "Forward input only; no automatic reverse-complement analysis"},
            "batch_size": batch_size, "candidates": list(candidates.values()), "work": work,
            "timing_ms": {**stages, "total_ms": total},
            "detailed_work_avoided_vs_filtered": work["eligible_candidates"] - work["detailed_evaluations"] if method == "adaptive" else 0}
