"""Fair, persisted comparisons and failure paths, using the actual saved models."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from fastapi.testclient import TestClient
from ecosplice.api import Settings, create_app
from ecosplice.storage import RunStore


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        (ROOT / "qa/test-temp").mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "qa/test-temp")
        self.addCleanup(self.temp.cleanup)
        self.settings = Settings(db_path=Path(self.temp.name) / "runs.sqlite3")
        self.client = self.enterContext(TestClient(create_app(self.settings)))

    def run_analysis(self, **settings):
        return self.client.post("/api/analyses", json={"sample_id": "REAL-003", **settings}).json()

    def test_real_measurements_are_persisted_with_original_prediction_snapshot(self):
        run = self.run_analysis(method="adaptive", assumed_power_watts=27)
        response = self.client.post("/api/runs/" + run["id"] + "/comparison", json={"repeats": 3})
        self.assertEqual(response.status_code, 200, response.text)
        updated = response.json()
        measured = updated["comparison"]
        self.assertEqual(updated["analysis"], run["analysis"])
        self.assertEqual(updated["energy"], run["energy"])
        self.assertEqual(measured["input"]["sha256"], run["analysis"]["input"]["sha256"])
        self.assertEqual(measured["baseline_filtered_max_score_difference"], 0)
        self.assertGreater(measured["adaptive_detailed_evaluations_avoided"], 0)
        for method in ("exhaustive", "filtered", "adaptive"):
            value = measured["methods"][method]
            self.assertEqual(len(value["raw_total_ms"]), 3)
            self.assertEqual(value["median_ms"], sorted(value["raw_total_ms"])[1])
            self.assertGreaterEqual(value["max_ms"], value["median_ms"])
            self.assertLessEqual(value["min_ms"], value["median_ms"])
            self.assertGreaterEqual(value["iqr_ms"], 0)
            self.assertEqual(value["estimated_joules"], 27 * value["median_ms"] / 1000)
            self.assertLessEqual(value["work"]["peak_batch_windows"], 512)
            self.assertEqual(value["quality"]["donor"]["count"], sum(site["type"] == "donor" for site in run["analysis"]["candidates"]))
        self.assertEqual(measured["methods"]["filtered"]["prediction_disagreements_vs_exhaustive"], 0)
        with TestClient(create_app(self.settings)) as restart:
            saved = restart.get("/api/runs/" + run["id"]).json()
            self.assertEqual(saved["comparison"], measured)
            exported = restart.get("/api/runs/" + run["id"] + "/export?scope=filtered&query=C-477").json()
            self.assertEqual(exported["comparison"], measured)
            expected = [site for site in run["analysis"]["candidates"] if "c-477" in site["id"].lower()]
            self.assertEqual(exported["analysis"]["candidates"], expected)
            self.assertEqual(restart.get("/api/runs/" + run["id"] + "/export?query=C-1").status_code, 422)
            preflight = restart.head("/api/runs/" + run["id"] + "/export?format=csv&scope=filtered&query=C-477")
            self.assertEqual(preflight.status_code, 200)
            self.assertEqual(preflight.content, b"")
            self.assertIn("attachment", preflight.headers["content-disposition"])
            self.assertEqual(restart.head("/api/runs/missing/export").status_code, 404)
            self.assertEqual(restart.head("/api/runs/" + run["id"] + "/export?query=C-1").status_code, 422)

    def test_unknown_truth_and_zero_power_remain_explicit(self):
        run = self.client.post("/api/analyses", json={"sequence": "ACCT" * 100, "assumed_power_watts": 0}).json()
        result = self.client.post("/api/runs/" + run["id"] + "/comparison", json={"repeats": 3}).json()["comparison"]
        self.assertIsNone(result["adaptive_detailed_work_reduction"])
        self.assertEqual(result["methods"]["filtered"]["work"]["detailed_evaluations"], 0)
        self.assertGreater(result["methods"]["exhaustive"]["work"]["detailed_evaluations"], 0)
        for measured in result["methods"].values():
            self.assertIsNone(measured["quality"])
            self.assertEqual(measured["estimated_joules"], 0)
            self.assertIsNone(measured["estimated_energy_reduction_vs_exhaustive"])

    def test_comparison_rejects_changed_model_and_invalid_repeat_settings(self):
        run = self.run_analysis()
        for repeats in (1, 8, True, "5"):
            self.assertEqual(self.client.post("/api/runs/" + run["id"] + "/comparison", json={"repeats": repeats}).status_code, 422)
        modified = {**run, "id": "old-model", "analysis": {**run["analysis"], "model_id": "old"}}
        RunStore(self.settings.db_path).save(modified)
        response = self.client.post("/api/runs/old-model/comparison", json={"repeats": 3})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "comparison_model_mismatch")

    def test_failed_comparison_keeps_original_run_and_releases_compute_lock(self):
        run = self.run_analysis()
        with patch("ecosplice.api.compare", side_effect=ValueError("parity failure")), patch("ecosplice.api.logging.exception"):
            response = self.client.post("/api/runs/" + run["id"] + "/comparison", json={"repeats": 3})
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json()["error"]["code"], "comparison_failed")
        self.assertEqual(self.client.get("/api/runs/" + run["id"]).json(), run)
        self.assertEqual(self.client.post("/api/runs/" + run["id"] + "/comparison", json={"repeats": 3}).status_code, 200)

    def test_reference_experiment_requires_matching_artifacts(self):
        response = self.client.get("/api/benchmarks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["benchmark"]["model_id"], self.client.get("/api/model").json()["model_id"])
        self.assertEqual(len(response.json()["benchmark"]["inputs"]), 6)
        directory = Path(self.temp.name)
        (directory / "algorithm-verification.json").write_text(json.dumps({"model_id": "wrong"}))
        with TestClient(create_app(Settings(db_path=directory / "other.sqlite3", results_dir=directory))) as client:
            self.assertEqual(client.get("/api/benchmarks").json()["error"]["code"], "benchmarks_unavailable")


if __name__ == "__main__":
    unittest.main()
