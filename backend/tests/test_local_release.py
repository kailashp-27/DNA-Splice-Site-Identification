"""Production static routing and a complete flow with outbound sockets blocked."""
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from fastapi.testclient import TestClient
from ecosplice.api import Settings
from ecosplice.local_app import create_local_app


class LocalReleaseTests(unittest.TestCase):
    def setUp(self):
        (ROOT / "qa/test-temp").mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "qa/test-temp")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.frontend = self.path / "dist"
        self.frontend.mkdir()
        (self.frontend / "index.html").write_text("<html><body>Local dashboard</body></html>", encoding="utf-8")
        (self.frontend / "app.js").write_text("console.log('local');", encoding="utf-8")
        # Even if an accidental file exists there, /api must belong to the service.
        (self.frontend / "api").mkdir()
        (self.frontend / "api/missing").write_text("should never be served")
        self.settings = Settings(db_path=self.path / "history.sqlite3")

    def app(self):
        return create_local_app(self.settings, self.frontend)

    def test_static_files_do_not_hide_api_or_missing_asset_errors(self):
        with TestClient(self.app()) as client:
            self.assertIn("Local dashboard", client.get("/").text)
            self.assertEqual(client.get("/").headers["cache-control"], "no-cache")
            self.assertEqual(client.get("/app.js").headers["x-content-type-options"], "nosniff")
            self.assertEqual(client.get("/api/health").json()["status"], "ready")
            for path in ("/api/missing", "/assets/missing.js", "/../models/ecosplice-v1/manifest.json"):
                self.assertEqual(client.get(path).status_code, 404)

    def test_missing_build_is_a_clear_startup_error(self):
        with self.assertRaisesRegex(FileNotFoundError, "Built dashboard missing"):
            create_local_app(self.settings, self.path / "absent")

    def test_downloaded_sample_preserves_dna_but_upload_has_no_labels(self):
        with TestClient(self.app()) as client:
            sample = client.get("/api/samples/REAL-003").json()
            download = client.get("/api/samples/REAL-003/fasta")
            self.assertEqual(download.status_code, 200)
            self.assertIn('attachment;', download.headers['content-disposition'])
            self.assertEqual(''.join(download.text.splitlines()[1:]), sample['sequence'])
            uploaded = client.post('/api/analyses', json={'sequence': download.text, 'method': 'filtered'})
            self.assertEqual(uploaded.status_code, 201, uploaded.text)
            self.assertIsNone(uploaded.json()['evaluation'])
            self.assertEqual(client.get('/api/samples/unknown/fasta').status_code, 404)

    def test_offline_analysis_compare_restart_reopen_export_delete(self):
        original_connect = socket.socket.connect
        outbound = []
        def local_only(sock, address):
            if isinstance(address, tuple) and address[0] not in ("127.0.0.1", "::1", "localhost"):
                outbound.append(address)
                raise OSError("Internet deliberately unavailable during release verification")
            return original_connect(sock, address)
        with patch.object(socket.socket, "connect", local_only), patch("socket.create_connection", side_effect=OSError("External connections blocked")):
            with TestClient(self.app()) as client:
                self.assertEqual(client.get("/").status_code, 200)
                self.assertEqual(client.get("/api/evaluation").status_code, 200)
                self.assertEqual(client.get("/api/benchmarks").status_code, 200)
                response = client.post("/api/analyses", json={"sample_id": "REAL-003", "method": "adaptive", "name": "Offline demonstration", "assumed_power_watts": 17})
                self.assertEqual(response.status_code, 201, response.text)
                run = response.json()
                self.assertGreater(run["analysis"]["work"]["preliminary_final"], 0)
                url = "/api/runs/" + run["id"]
                comparison = client.post(url + "/comparison", json={"repeats": 3})
                self.assertEqual(comparison.status_code, 200, comparison.text)
                saved = client.get(url).json()
                self.assertEqual(saved["analysis"], run["analysis"])
            with TestClient(self.app()) as restarted:
                self.assertEqual(restarted.get(url).json(), saved)
                renamed = restarted.patch(url, json={"name": "Offline reopened"}).json()
                exported = restarted.get(url + "/export").json()
                self.assertEqual(exported["analysis"], renamed["analysis"])
                self.assertEqual(exported["comparison"], saved["comparison"])
                for format in ("csv", "html"):
                    self.assertEqual(restarted.get(url + "/export?format=" + format).status_code, 200)
                self.assertEqual(restarted.delete(url).status_code, 204)
                self.assertEqual(restarted.get(url).status_code, 404)
        self.assertEqual(outbound, [])
