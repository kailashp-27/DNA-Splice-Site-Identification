"""Real HTTP contracts, durable snapshots, consistent exports and failure paths."""
from concurrent.futures import ThreadPoolExecutor
import csv
from io import StringIO
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from fastapi.testclient import TestClient
from ecosplice.api import Settings, create_app
from ecosplice.algorithms import analyze
from ecosplice.model import ModelBundle
from ecosplice.storage import RunStore


class ApiTests(unittest.TestCase):
    def setUp(self):
        (ROOT / "qa/test-temp").mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "qa/test-temp")
        self.addCleanup(self.temp.cleanup)
        self.settings = Settings(db_path=Path(self.temp.name) / "runs.sqlite3")
        self.client = self.enterContext(TestClient(create_app(self.settings), raise_server_exceptions=False))

    def post(self, **fields):
        return self.client.post("/api/analyses", json={"sample_id": "REAL-003", "method": "adaptive", **fields})

    def test_startup_loads_once_and_serves_genuine_artifacts(self):
        with patch("ecosplice.api.ModelBundle.load", wraps=ModelBundle.load) as load:
            with TestClient(create_app(Settings(db_path=Path(self.temp.name) / "other.sqlite3"))) as client:
                self.assertEqual(client.get("/api/health").json()["status"], "ready")
                identity = client.get("/api/model").json()["model_id"]
                self.assertEqual(client.get("/api/evaluation").json()["evaluation"]["model_id"], identity)
                self.assertEqual(len(client.get("/api/samples").json()["samples"]), 4)
                for _ in range(2):
                    self.assertEqual(client.post("/api/analyses", json={"sample_id": "REAL-001"}).status_code, 201)
                self.assertEqual(load.call_count, 1)

    def test_run_survives_restart_with_original_settings_and_input(self):
        response = self.post(name="ARVCF demonstration", assumed_power_watts=23, client_request_id="request-7")
        self.assertEqual(response.status_code, 201, response.text)
        run = response.json()
        self.assertEqual(run["client_request_id"], "request-7")
        self.assertEqual(run["analysis"]["input"]["length"], len(run["input_sequence"]))
        self.assertEqual(run["energy"]["estimated_joules"], 23 * run["analysis"]["timing_ms"]["total_ms"] / 1000)
        self.assertGreater(run["analysis"]["work"]["preliminary_final"], 0)
        self.assertIsNotNone(run["evaluation"])
        self.assertEqual(run["evaluation"]["unscorable_annotated_boundaries"], 1)
        with TestClient(create_app(self.settings)) as restarted:
            self.assertEqual(restarted.get("/api/runs/" + run["id"]).json(), run)
            renamed = restarted.patch("/api/runs/" + run["id"], json={"name": "  Review run  "}).json()
            self.assertEqual(renamed["name"], "Review run")
            self.assertEqual(renamed["analysis"], run["analysis"])
            self.assertEqual(renamed["energy"], run["energy"])
            listing = restarted.get("/api/runs?limit=1&offset=0").json()
            self.assertEqual(listing["total"], 1)
            self.assertEqual(listing["runs"][0]["name"], "Review run")
            self.assertNotIn("input_sequence", listing["runs"][0])
            self.assertEqual(restarted.delete("/api/runs/" + run["id"]).status_code, 204)
        self.assertEqual(self.client.get("/api/runs/" + run["id"]).status_code, 404)

    def test_all_exports_agree_and_filtered_exports_preserve_full_run_measurements(self):
        run = self.post().json()
        url = "/api/runs/" + run["id"] + "/export"
        report = self.client.get(url).json()
        self.assertEqual(report["analysis"], run["analysis"])
        query = "scope=filtered&type=acceptor&min_score=0.4&predicted_only=true"
        filtered = self.client.get(url + "?" + query).json()
        selected = [site for site in run["analysis"]["candidates"] if site["type"] == "acceptor" and site["predicted"] and site["score"] >= .4]
        self.assertGreater(len(selected), 0)
        self.assertEqual(filtered["analysis"]["candidates"], selected)
        self.assertEqual(filtered["analysis"]["timing_ms"], run["analysis"]["timing_ms"])
        self.assertEqual(filtered["energy"], run["energy"])
        csv_response = self.client.get(url + "?format=csv&" + query)
        rows = list(csv.DictReader(StringIO(csv_response.text)))
        csv_sites = [row for row in rows if row["record"] == "candidate"]
        self.assertTrue(all(None not in row for row in rows))
        self.assertEqual([int(site["position1"]) for site in csv_sites], [site["position1"] for site in selected])
        self.assertEqual([float(site["score"]) for site in csv_sites], [site["score"] for site in selected])
        metadata = {row["field"]: row["value"] for row in rows if row["record"] == "metadata"}
        self.assertEqual(json.loads(metadata["energy"]), run["energy"])
        self.assertEqual(json.loads(metadata["analysis.settings"]), run["analysis"]["settings"])
        html = self.client.get(url + "?format=html&" + query)
        self.assertEqual(html.text.count("<tbody><tr>") + html.text.count("</tr><tr>"), len(selected))
        self.assertIn(run["analysis"]["model_id"], html.text)
        self.assertIn("default-src 'none'", html.headers["content-security-policy"])
        self.assertEqual(self.client.get(url + "?min_score=0.5").status_code, 422)
        self.assertEqual(self.client.get(url + "?scope=filtered&min_score=nan").status_code, 422)
        self.assertEqual(self.client.get("/api/runs/" + run["id"]).json(), run)

    def test_empty_results_are_successful_and_exportable(self):
        run = self.client.post("/api/analyses", json={"sequence": "ACCT" * 50}).json()
        self.assertEqual(run["analysis"]["candidates"], [])
        self.assertIsNone(run["evaluation"])
        response = self.client.get("/api/runs/" + run["id"] + "/export?format=csv")
        self.assertIn("analysis.coordinate_convention", response.text)
        self.assertIn(run["analysis"]["input"]["sha256"], response.text)

    def test_invalid_inputs_never_save_sample_results(self):
        requests = [{"sequence": ""}, {"sequence": "ACGTZ" * 30}, {"sequence": "A" * 19},
                    {"sequence": ">one\n" + "A" * 30 + "\n>two\n" + "C" * 30},
                    {"sequence": "A" * 100001}, {"sequence": "A" * 30, "sample_id": "REAL-001"},
                    {}, {"sample_id": "REAL-001", "batch_size": True},
                    {"sample_id": "REAL-001", "method": "invented"},
                    {"sample_id": "REAL-001", "threshold": .5},
                    {"sample_id": "REAL-001", "assumed_power_watts": -1}]
        for body in requests:
            response = self.client.post("/api/analyses", json=body)
            self.assertEqual(response.status_code, 422, response.text)
            self.assertIn("error", response.json())
            self.assertNotIn("candidates", response.json())
        self.assertEqual(self.post(sample_id="../../unknown").status_code, 404)
        self.assertEqual(self.client.get("/api/runs").json()["total"], 0)

    def test_edge_and_unknown_contexts_are_retained_without_scores_or_accuracy(self):
        raw = ">unknown\n" + "GT" + "A" * 55 + "N" + "A" * 49 + "AG" + "A" * 55
        response = self.client.post("/api/analyses", json={"sequence": raw})
        self.assertEqual(response.status_code, 201)
        run = response.json()
        self.assertIsNone(run["evaluation"])
        self.assertEqual(run["quality"]["unknown_bases"], 1)
        self.assertEqual(run["analysis"]["candidates"][0]["unavailable_reason"], "sequence_edge")
        site = next(site for site in run["analysis"]["candidates"] if site["position1"] == 108)
        self.assertEqual(site["unavailable_reason"], "unknown_context")
        self.assertIsNone(site["score"])

    def test_missing_model_keeps_history_readable(self):
        run = self.post().json()
        with patch("ecosplice.api.logging.exception"):
            with TestClient(create_app(Settings(db_path=self.settings.db_path, model_dir=Path(self.temp.name) / "missing"))) as client:
                self.assertEqual(client.get("/api/health").json()["status"], "degraded")
                response = client.post("/api/analyses", json={"sample_id": "REAL-001"})
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()["error"]["code"], "model_unavailable")
                self.assertEqual(client.get("/api/runs/" + run["id"]).json(), run)
                self.assertEqual(client.get("/api/runs/" + run["id"] + "/export").status_code, 200)

    def test_failed_analysis_and_failed_persistence_do_not_return_success(self):
        with patch("ecosplice.api.analyze", side_effect=RuntimeError("inference error")), patch("ecosplice.api.logging.exception"):
            response = self.post()
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json()["error"]["code"], "analysis_failed")
        with patch.object(RunStore, "save", side_effect=sqlite3.OperationalError("disk full")), patch("ecosplice.api.logging.exception"):
            response = self.post()
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()["error"]["code"], "history_unavailable")
        self.assertEqual(self.client.get("/api/runs").json()["total"], 0)
        self.assertEqual(self.post().status_code, 201)

    def test_unusable_history_has_explicit_error(self):
        with patch("ecosplice.api.logging.exception"):
            with TestClient(create_app(Settings(db_path=Path(self.temp.name)))) as client:
                self.assertFalse(client.get("/api/health").json()["history_ready"])
                self.assertEqual(client.get("/api/runs").status_code, 503)
                self.assertEqual(client.post("/api/analyses", json={"sample_id": "REAL-001"}).status_code, 503)

    def test_mismatched_evaluation_and_corrupt_samples_fail_explicitly(self):
        directory = Path(self.temp.name)
        (directory / "model-evaluation.json").write_text(json.dumps({"model_id": "wrong"}))
        sample_path = directory / "demo_samples.json"
        sample_path.write_text("[]")
        with TestClient(create_app(Settings(db_path=directory / "other.sqlite3", results_dir=directory, samples_path=sample_path))) as client:
            self.assertEqual(client.get("/api/evaluation").json()["error"]["code"], "evaluation_unavailable")
            self.assertEqual(client.get("/api/samples").status_code, 503)
            self.assertEqual(client.post("/api/analyses", json={"sequence": "A" * 100}).status_code, 201)

    def test_names_are_escaped_in_exports_and_rename_is_validated(self):
        run = self.post(name="=2+2<script>alert(1)</script>").json()
        url = "/api/runs/" + run["id"]
        csv_text = self.client.get(url + "/export?format=csv").text
        self.assertIn("'=2+2<script>", csv_text)
        html = self.client.get(url + "/export?format=html").text
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        for name in ("   ", "A" * 121, "bad\x00name"):
            self.assertEqual(self.client.patch(url, json={"name": name}).status_code, 422)
        self.assertEqual(self.client.patch("/api/runs/does-not-exist", json={"name": "valid"}).status_code, 404)
        self.assertEqual(self.client.get("/unknown").json()["error"]["code"], "http_error")

    def test_streamed_request_limit_and_cors(self):
        response = self.client.post("/api/analyses", content=(b"A" * 400000 for _ in range(3)), headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["error"]["code"], "request_too_large")
        allowed = self.client.options("/api/analyses", headers={"Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "POST"})
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.headers["access-control-allow-origin"], "http://127.0.0.1:5173")
        denied = self.client.options("/api/analyses", headers={"Origin": "https://other.example", "Access-Control-Request-Method": "POST"})
        self.assertNotIn("access-control-allow-origin", denied.headers)

    def test_parallel_computation_rejects_busy_without_corrupting_history(self):
        entered, release = threading.Event(), threading.Event()
        def slow(*args, **kwargs):
            entered.set()
            if not release.wait(5):
                raise RuntimeError("Timed out waiting for test")
            return analyze(*args, **kwargs)
        with ThreadPoolExecutor(max_workers=1) as executor, patch("ecosplice.api.analyze", side_effect=slow):
            future = executor.submit(self.post)
            try:
                self.assertTrue(entered.wait(5))
                response = self.post()
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()["error"]["code"], "analysis_busy")
            finally:
                release.set()
            self.assertEqual(future.result(timeout=5).status_code, 201)
        self.assertEqual(self.client.get("/api/runs").json()["total"], 1)

    def test_concurrent_storage_transactions_have_unique_durable_runs(self):
        run = self.post().json()
        store = RunStore(self.settings.db_path)
        def save(index):
            snapshot = {**run, "id": f"parallel-{index}", "name": f"Parallel {index}"}
            store.save(snapshot)
            return store.get(snapshot["id"])["name"]
        with ThreadPoolExecutor(max_workers=4) as executor:
            self.assertEqual(list(executor.map(save, range(12))), [f"Parallel {index}" for index in range(12)])
        self.assertEqual(self.client.get("/api/runs?limit=100").json()["total"], 13)


if __name__ == "__main__":
    unittest.main()
