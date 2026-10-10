"""Saved-model integrity, true avoided inference, parity and predictable failures."""
from pathlib import Path
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
import numpy as np
from ecosplice.algorithms import analyze
from ecosplice.evaluation import adaptive_scores, binary_metrics, motif_masks
from ecosplice.model import LinearScorer, ModelBundle, encode_contexts


class FeatureTests(unittest.TestCase):
    def test_invalid_contexts_are_rejected(self):
        for context in ("A" * 101, "A" * 50 + "N" + "A" * 51, "A" * 101 + "é"):
            with self.assertRaises(ValueError):
                encode_contexts([context])

    def test_exported_feature_sum_and_softmax(self):
        # Independent hand calculation of position weights, without fitting a model.
        weights = np.zeros((3, 8))
        weights[1, 2] = 2.  # G at first position
        weights[2, 7] = 3.  # T at second position
        scorer = LinearScorer(weights, np.zeros(3), 0, False, "test")
        scores = scorer.score(["A" * 50 + "GT" + "A" * 50])[0]
        expected = np.exp([0., 2., 3.]) / np.exp([0., 2., 3.]).sum()
        np.testing.assert_allclose(scores, expected, atol=1e-15)

    def test_adjacent_pair_coefficients_use_correct_order(self):
        weights = np.zeros((3, 24))
        weights[1, 8 + 2 * 4 + 3] = 4.  # GT pair
        scorer = LinearScorer(weights, np.zeros(3), 0, True, "test")
        self.assertGreater(scorer.score(["A" * 50 + "GT" + "A" * 50])[0, 1], .95)
        np.testing.assert_allclose(scorer.score(["A" * 50 + "TG" + "A" * 50])[0], [1 / 3] * 3)

    def test_metrics_include_false_negatives(self):
        result = binary_metrics([True, True, False, False], [True, False, True, False])
        self.assertEqual((result["tp"], result["fn"], result["fp"], result["tn"]), (1, 1, 1, 1))
        self.assertEqual(result["f1"], .5)


@unittest.skipUnless((ROOT / "models/ecosplice-v1/manifest.json").exists(), "Train the saved model first")
class SavedModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / "qa/test-temp").mkdir(parents=True, exist_ok=True)
        cls.bundle = ModelBundle.load(ROOT / "models/ecosplice-v1")
        cls.demo = json.loads((ROOT / "data/processed/demo_samples.json").read_text())[2]["sequence"]

    def test_model_roundtrip_is_deterministic(self):
        other = ModelBundle.load(ROOT / "models/ecosplice-v1")
        context = self.demo[100:202]
        np.testing.assert_array_equal(self.bundle.detailed.score([context]), other.detailed.score([context]))
        self.assertEqual(self.bundle.identity, other.identity)

    def test_corrupt_model_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "qa/test-temp") as directory:
            path = Path(directory)
            (path / "manifest.json").write_text(json.dumps(self.bundle.metadata))
            (path / "preliminary.npz").write_bytes(b"not a valid model")
            with self.assertRaisesRegex(ValueError, "checksum"):
                ModelBundle.load(path)

    def test_missing_model_is_a_clear_failure(self):
        with self.assertRaisesRegex(ValueError, "unavailable"):
            ModelBundle.load(ROOT / "models/nonexistent-test-model")

    def test_exhaustive_filtered_parity_across_batch_sizes(self):
        baseline = analyze(self.demo, self.bundle, "exhaustive", 37)
        for size in (1, 73, 512):
            filtered = analyze(self.demo, self.bundle, "filtered", size)
            for left, right in zip(baseline["candidates"], filtered["candidates"]):
                self.assertEqual(left["position1"], right["position1"])
                self.assertEqual(left["predicted"], right["predicted"])
                self.assertEqual(left["unavailable_reason"], right["unavailable_reason"])
                if left["score"] is not None:
                    self.assertAlmostEqual(left["score"], right["score"], places=12)
            self.assertLessEqual(filtered["work"]["peak_batch_windows"], size)
        self.assertEqual(baseline["work"]["detailed_evaluations"], len(self.demo) - 101)

    def test_fast_route_never_runs_detailed_model(self):
        metadata = copy.deepcopy(self.bundle.metadata)
        for kind in ("donor", "acceptor"):
            threshold = metadata["thresholds"]["preliminary"][kind]
            metadata["routing"][kind] = {"low": threshold, "high": threshold}
        bundle = ModelBundle(metadata, self.bundle.preliminary, self.bundle.detailed)
        with patch.object(bundle.detailed, "score", wraps=bundle.detailed.score) as detailed:
            result = analyze(self.demo, bundle, "adaptive")
            detailed.assert_not_called()
        self.assertEqual(result["work"]["detailed_evaluations"], 0)
        self.assertEqual(result["work"]["preliminary_final"], result["work"]["eligible_candidates"])

    def test_uncertain_route_calls_detailed_only_for_pending_cases(self):
        with patch.object(self.bundle.detailed, "score", wraps=self.bundle.detailed.score) as detailed:
            result = analyze(self.demo, self.bundle, "adaptive", 64)
            actual = sum(len(call.args[0]) for call in detailed.call_args_list)
        self.assertEqual(actual, result["work"]["detailed_evaluations"])
        self.assertGreater(result["work"]["preliminary_final"], 0)
        self.assertGreater(result["work"]["detailed_final"], 0)
        self.assertEqual(result["work"]["preliminary_final"] + result["work"]["detailed_final"], result["work"]["eligible_candidates"])

    def test_all_uncertain_matches_filtered(self):
        metadata = copy.deepcopy(self.bundle.metadata)
        for kind in ("donor", "acceptor"):
            metadata["routing"][kind] = {"low": 0., "high": 1.}
        bundle = ModelBundle(metadata, self.bundle.preliminary, self.bundle.detailed)
        adaptive, filtered = analyze(self.demo, bundle, "adaptive"), analyze(self.demo, bundle, "filtered")
        self.assertEqual([s["score"] for s in adaptive["candidates"]], [s["score"] for s in filtered["candidates"]])
        self.assertEqual(adaptive["work"]["preliminary_final"], 0)

    def test_edges_and_unknown_context_never_receive_fabricated_scores(self):
        for sequence, reason in (("GT" + "A" * 100 + "AG", "sequence_edge"),
                                 ("A" * 50 + "GT" + "A" * 20 + "N" + "A" * 29, "unknown_context")):
            for method in ("exhaustive", "filtered", "adaptive"):
                result = analyze(sequence, self.bundle, method)
                self.assertTrue(result["candidates"])
                self.assertTrue(all(s["score"] is None and s["unavailable_reason"] in ("sequence_edge", "unknown_context") for s in result["candidates"]))
                if reason == "unknown_context":
                    donor = next(s for s in result["candidates"] if s["position1"] == 51)
                    self.assertEqual(donor["unavailable_reason"], "unknown_context")
                else:
                    self.assertTrue(all(s["unavailable_reason"] == reason for s in result["candidates"]))

    def test_empty_candidates_and_short_sequences_are_valid_empty_results(self):
        for sequence in ("ACCT" * 50, "A" * 20):
            for method in ("exhaustive", "filtered", "adaptive"):
                self.assertEqual(analyze(sequence, self.bundle, method)["candidates"], [])

    def test_invalid_input_settings_and_limits_fail(self):
        for sequence in ("", "A" * 20 + "X", "A" * 100001, ">a\n" + "A" * 20 + "\n>b\n" + "C" * 20):
            with self.assertRaises(ValueError):
                analyze(sequence, self.bundle)
        for kwargs in ({"method": "fake"}, {"batch_size": 0}, {"batch_size": 9000}):
            with self.assertRaises(ValueError):
                analyze(self.demo, self.bundle, **kwargs)

    def test_offline_adaptive_evaluation_agrees_with_operational_predictions(self):
        selected = {}
        with (ROOT / "data/processed/windows.jsonl").open(encoding="utf-8") as source:
            for line in source:
                row = json.loads(line)
                if row["split"] != "test":
                    continue
                motif = row["context"][50:52]
                if motif not in ("GT", "AG"):
                    continue
                key = (row["label"], motif)
                if key not in selected:
                    selected[key] = row["context"]
                if len(selected) == 4:
                    break
        self.assertEqual(len(selected), 4)
        contexts = list(selected.values())
        light, heavy = self.bundle.preliminary.score(contexts), self.bundle.detailed.score(contexts)
        decisions, _ = adaptive_scores(light, heavy, motif_masks(contexts), self.bundle.routing, self.bundle.thresholds)
        for index, context in enumerate(contexts):
            result = analyze(context, self.bundle, "adaptive")
            site = next(s for s in result["candidates"] if s["position1"] == 51)
            self.assertEqual(site["predicted"], bool(decisions[site["type"]][index]))

    def test_cli_loads_saved_model_and_writes_consistent_result(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "qa/test-temp") as directory:
            output = Path(directory) / "analysis.json"
            completed = subprocess.run([sys.executable, str(ROOT / "scripts/analyze_sequence.py"),
                                        "--input", str(ROOT / "data/demo/REAL-003.fasta"),
                                        "--method", "adaptive", "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(output.read_text())
            self.assertEqual(result["model_id"], self.bundle.identity)
            self.assertEqual(result["input"]["length"], len(self.demo))
            self.assertTrue(any(s["score"] is not None for s in result["candidates"]))


if __name__ == "__main__":
    unittest.main()
