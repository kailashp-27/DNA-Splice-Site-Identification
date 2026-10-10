"""Exercise an extracted release via real HTTP in a fresh, offline runtime."""
from pathlib import Path
import csv
import hashlib
from io import StringIO
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    evidence = ROOT / "qa/experiments/local-release"
    evidence.mkdir(parents=True, exist_ok=True)
    experiment = Path(tempfile.mkdtemp(prefix="extracted-", dir=evidence))
    archive = ROOT / "releases/EcoSplice-1.0.0.zip"
    with zipfile.ZipFile(archive) as bundle:
        for name in bundle.namelist():
            if name.startswith("/") or ".." in Path(name).parts:
                raise ValueError("Unsafe archive path")
        bundle.extractall(experiment)
    application = experiment / "EcoSplice"
    manifest = json.loads((application / "RELEASE_MANIFEST.json").read_text())
    for name, expected in manifest["contents"].items():
        assert hashlib.sha256((application / name).read_bytes()).hexdigest() == expected, name
    assert not (application / "data/local").exists(), "User history leaked into the release"
    assert not (application / "data/processed/windows.jsonl").exists()
    assert not (application / "package.json").exists(), "Prebuilt release should not require Node"
    shutil.copytree(ROOT / ".cache/wheels", application / ".cache/wheels")
    print("Preparing a fresh extracted-package environment using offline wheels only.", flush=True)
    with (experiment / "setup.log").open("w", encoding="utf-8") as setup_log:
        setup = subprocess.run([sys.executable, str(application / "scripts/setup_local.py"), "--offline"],
                               cwd=experiment, stdout=setup_log, stderr=subprocess.STDOUT, text=True, timeout=180)
    assert setup.returncode == 0, (experiment / "setup.log").read_text()
    python = application / ".venv/Scripts/python.exe"
    if sys.platform != "win32":
        python = application / ".venv/bin/python"
    environment = os.environ.copy()
    for variable in ("ECOSPLICE_DB_PATH", "ECOSPLICE_MODEL_DIR", "ECOSPLICE_PORT"):
        environment.pop(variable, None)
    environment["PYTHONUNBUFFERED"] = "1"
    # The service has no internet even if the laptop is connected. Loopback remains usable.
    guard = experiment / "offline_server.py"
    guard.write_text("""import runpy, socket, sys
from pathlib import Path
original_connect = socket.socket.connect
original_connect_ex = socket.socket.connect_ex
def allowed(address):
    if isinstance(address, tuple) and address[0] not in ('127.0.0.1', '::1', 'localhost'):
        Path(__file__).with_name('outbound-attempts.log').open('a').write(repr(address)+'\\n')
        raise OSError('Outbound networking blocked for release verification')
def guarded_connect(sock, address):
    allowed(address)
    return original_connect(sock, address)
def guarded_connect_ex(sock, address):
    allowed(address)
    return original_connect_ex(sock, address)
socket.socket.connect = guarded_connect
socket.socket.connect_ex = guarded_connect_ex
sys.argv = [sys.argv[1], '--port', sys.argv[2]]
runpy.run_path(sys.argv[0], run_name='__main__')
""", encoding="utf-8")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    process, log = None, None
    def stop():
        nonlocal process, log
        if process:
            process.terminate()
            process.wait(timeout=15)
            process = None
        if log:
            log.close()
            log = None
    def start(number):
        nonlocal process, log
        log = (experiment / f"server-{number}.log").open("w", encoding="utf-8")
        process = subprocess.Popen([str(python), str(guard), str(application / "scripts/start_local.py"), str(port)],
                                   cwd=experiment, env=environment, stdout=log, stderr=subprocess.STDOUT)
        for _ in range(100):
            if process.poll() is not None:
                raise AssertionError("Service exited during startup. Inspect server log.")
            try:
                if request("/api/health")[1]["status"] == "ready":
                    return
            except (URLError, ConnectionError):
                pass
            time.sleep(.1)
        raise AssertionError("Local service did not become ready")
    def request(path, method="GET", body=None, raw=False):
        data = json.dumps(body).encode() if body is not None else None
        req = Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"} if data else {})
        try:
            with urlopen(req, timeout=60) as response:
                payload, status = response.read(), response.status
        except HTTPError as error:
            payload, status = error.read(), error.code
        return status, payload if raw or not payload else json.loads(payload)
    checks = []
    try:
        start(1)
        checks.append("fresh environment startup with outbound sockets blocked")
        status, index = request("/", raw=True)
        assert status == 200
        assets = re.findall(r'(?:src|href)="(/[^\"]+)"', index.decode())
        assert len(assets) >= 3
        assert not re.search(r'(?:src|href)="https?://', index.decode())
        for asset in assets:
            status, content = request(asset, raw=True)
            assert status == 200 and content == (application / "dist" / asset.lstrip("/")).read_bytes(), asset
        checks.append(f"built dashboard and {len(assets)} local assets served byte-for-byte")
        assert request("/api/missing")[0] == 404
        assert request("/assets/missing.js")[0] == 404
        for path in ("/api/evaluation", "/api/benchmarks", "/api/model", "/api/samples"):
            assert request(path)[0] == 200, path
        status, run = request("/api/analyses", "POST", {"sample_id": "REAL-003", "method": "adaptive", "name": "Offline package verification", "assumed_power_watts": 17})
        assert status == 201 and run["evaluation"] is not None
        url = "/api/runs/" + run["id"]
        status, _ = request(url + "/comparison", "POST", {"repeats": 3})
        assert status == 200
        saved = request(url)[1]
        assert saved["analysis"] == run["analysis"]
        checks.append("genuine annotated sample, actual adaptive routes and three-method comparison")
        fasta = (application / "data/demo/REAL-003.fasta").read_text()
        uploaded = request("/api/analyses", "POST", {"sequence": fasta})[1]
        assert uploaded["evaluation"] is None
        checks.append("FASTA prediction without invented accuracy labels")
        for text in ("", "ACTZ" * 50, ">first\n" + "ACGT" * 30 + "\n>second\n" + "ACGT" * 30, "A" * 100001):
            assert request("/api/analyses", "POST", {"sequence": text})[0] == 422
        assert request("/api/analyses", "POST", {"sequence": "ACCT" * 100})[1]["analysis"]["candidates"] == []
        checks.append("invalid, multi-record, oversized and valid no-candidate flows")
        print("Checking actual HTTP inference at the 100,000-base limit.", flush=True)
        status, long_run = request("/api/analyses", "POST", {"sequence": "GTAG" * 25000, "method": "filtered", "name": "Synthetic maximum-length verification"})
        assert status == 201 and long_run["evaluation"] is None
        assert len(long_run["analysis"]["candidates"]) == 50000
        assert long_run["analysis"]["work"]["peak_batch_windows"] <= 512
        maximum = {"bases": 100000, "candidates": 50000, "work": long_run["analysis"]["work"], "timing_ms": long_run["analysis"]["timing_ms"]}
        del long_run
        checks.append("100,000 bases and 50,000 candidates through real HTTP with bounded batches")
        stop()
        start(2)
        assert request(url)[1] == saved
        renamed = request(url, "PATCH", {"name": "Offline reopened"})[1]
        report = request(url + "/export")[1]
        assert report["analysis"] == renamed["analysis"] and report["comparison"] == saved["comparison"]
        filtered = request(url + "/export?scope=filtered&type=acceptor&min_score=0.5&predicted_only=true")[1]
        csv_bytes = request(url + "/export?format=csv&scope=filtered&type=acceptor&min_score=0.5&predicted_only=true", raw=True)[1]
        rows = list(csv.DictReader(StringIO(csv_bytes.decode())))
        csv_sites = [row for row in rows if row["record"] == "candidate"]
        assert [int(row["position1"]) for row in csv_sites] == [site["position1"] for site in filtered["analysis"]["candidates"]]
        html_bytes = request(url + "/export?format=html&scope=filtered&type=acceptor&min_score=0.5&predicted_only=true", raw=True)[1]
        assert renamed["name"].encode() in html_bytes
        assert request(url, "DELETE")[0] == 204 and request(url)[0] == 404
        checks.append("process restart, exact snapshot reopen, rename, matching filtered CSV/JSON/HTML and deletion")
    finally:
        stop()
    assert not (experiment / "outbound-attempts.log").exists()
    # Helpful failures are checked without modifying the normal installed model.
    missing_env = {**environment, "ECOSPLICE_MODEL_DIR": str(experiment / "missing-model")}
    missing = subprocess.run([str(python), str(application / "scripts/start_local.py"), "--check"], env=missing_env, capture_output=True, text=True, timeout=30)
    assert missing.returncode != 0 and "cannot start" in missing.stdout + missing.stderr
    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen()
        conflict = subprocess.run([str(python), str(application / "scripts/start_local.py"), "--port", str(occupied.getsockname()[1])], env=environment, capture_output=True, text=True, timeout=30)
    assert conflict.returncode != 0 and "occupied or reserved" in conflict.stdout + conflict.stderr
    checks.append("missing model and occupied port give useful failures")
    result = {"passed": True, "release": manifest["release"], "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
              "verified_files": len(manifest["contents"]), "experiment_directory": str(experiment), "checks": checks,
              "maximum_input": maximum, "network_test": "Outbound connect/connect_ex denied in service process; actual loopback HTTP permitted. No remote assets in built index. OS connectivity unchanged."}
    (evidence / "verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"passed": True, "checks": checks, "evidence": str(evidence / "verification.json")}, indent=2))


if __name__ == "__main__":
    main()
