# EcoSplice local service and saved runs

Implemented and verified: 8 October 2026 (Parts 3–4). Python 3.12, FastAPI, Uvicorn and SQLite run on this laptop. The green React dashboard now uses the real service for prediction, evaluation, comparison, history and exports; see [DASHBOARD_INTEGRATION.md](DASHBOARD_INTEGRATION.md).

## Setup and launch

From the project root:

```powershell
python -m pip install -r backend/requirements.txt
python scripts/start_backend.py
```

Alternatively use `npm run dev:backend` or double-click `start-backend.cmd`. Check [service health](http://127.0.0.1:8765/api/health). This launcher binds **127.0.0.1:8765**, starts one worker, loads and warms the saved model once, and performs no training or downloads. Stop with Ctrl+C. An unavailable model leaves history readable but predictions return a clear 503 error. Logs explain missing/corrupt artifacts and database startup failures.

Use `python scripts/start_backend.py --port 8766` if the port is occupied/reserved. `ECOSPLICE_PORT` also controls the default. `ECOSPLICE_MODEL_DIR` overrides the saved model directory; `ECOSPLICE_DB_PATH` overrides the database file. Settings must be applied before starting/restarting. Default paths resolve relative to the project, rather than relying on the shell's working directory. Port 8000 was unavailable on the development laptop; 8765 passed actual launch/restart checks.

Normal service use requires only the installed runtime dependencies, saved model, and included small samples/evaluation artifact. Raw references and training dependencies are unnecessary. The API's OpenAPI contract is at `/openapi.json`; CDN-backed Swagger/ReDoc pages are disabled so service use needs no external assets. A single combined frontend/backend launcher and fresh offline setup verification belong to Part 5.

## API contract

All routes use `/api`. Request/response JSON uses snake_case. Unknown request fields are rejected. Errors have `{"error":{"code":"...","message":"..."}}`; field-validation errors also include `details`. The service never supplies sample results after a real failure.

| Method and route | Result |
| --- | --- |
| `GET /health` | Ready/degraded status, model/history/sample flags and input limits |
| `GET /model` | Loaded model manifest, scorers, frozen thresholds/routing and dataset identity |
| `GET /samples` | Four genuine held-out demo summaries and annotated-boundary counts |
| `GET /samples/{id}` | Oriented DNA, labels, genomic region and annotation scope |
| `GET /evaluation` | Genuine saved test/validation metrics, curves, calibration summaries and artifact hash; identities must match the loaded model |
| `POST /analyses` | Run one actual method, persist it, then return the complete run (201) |
| `GET /runs?limit=50&offset=0` | Paginated history summaries and total count; maximum page size 100 |
| `GET /runs/{id}` | Complete original snapshot and current run name |
| `PATCH /runs/{id}` | Rename using `{"name":"..."}`; scientific results remain unchanged |
| `DELETE /runs/{id}` | Delete this local history record (204); exported files remain separate |
| `GET /runs/{id}/export` | JSON, CSV or printable HTML from this saved run |
| `HEAD /runs/{id}/export` | Validate scope/existence before streaming a browser download; no rendered body |
| `GET /benchmarks` | Matching frozen measured multi-input reference experiment and artifact hash |
| `POST /runs/{id}/comparison` | Fresh same-input repeated measurements, attached to the saved run |

Example in PowerShell:

```powershell
$runRequest = @{
  sample_id = 'REAL-003'
  method = 'adaptive'
  name = 'ARVCF demonstration'
  assumed_power_watts = 15
  client_request_id = 'analysis-1'
} | ConvertTo-Json
$savedRun = Invoke-RestMethod -Uri http://127.0.0.1:8765/api/analyses -Method Post -ContentType application/json -Body $runRequest
Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/runs/$($savedRun.id)"
```

Supply exactly one of `sample_id` or `sequence`. The latter contains pasted DNA or **single-record FASTA text**, not a filesystem path. A frontend upload reads the file as text and sends it here. The service scans forward input only, accepts A/C/G/T/N, requires at least 20 called bases, limits normalized length to 100,000 bases, and rejects unsupported symbols/multiple records. Complete 102-base A/C/G/T contexts receive real scores. Edge and N-containing contexts retain `score=null` and a reason. Empty candidate sets are valid completed runs.

Methods are `exhaustive`, `filtered` (default), and `adaptive`. `batch_size` is an integer in 1–8192 (default 512); `assumed_power_watts` is finite 0–500 (default 15 W). Names allow 1–120 trimmed characters without control characters. Request bodies are capped at 1,000,000 bytes, including streamed/chunked bodies. Raw sequence text has a separate 300,000-character cap to allow ordinary FASTA formatting.

Adaptive processing uses the validated, frozen scorer-specific thresholds. There is no decision-threshold override. An export score filter changes which rows are shown, without changing saved prediction decisions or routing. `client_request_id` is echoed and saved for the frontend to reject stale responses; it is **not** an idempotency key. Each successful POST creates a new run. Closing a client does not promise cancellation of work already started.

Only one computation executes at a time to reduce timing contention. A simultaneous analysis receives `503 analysis_busy` and can be retried. Reads and independent SQLite operations use separate connections/transactions. A failed computation returns `500 analysis_failed`; failed persistence returns `503 history_unavailable`. Neither returns successful fixture data. Missing IDs return 404, invalid DNA/fields return 422, oversized bodies return 413. CORS permits localhost/127.0.0.1 development frontends on ports 5188 and the previous 5173. Vite's default same-origin /api proxy needs no browser CORS request.

## Repeated comparison

Send `POST /runs/{id}/comparison` with `{"repeats":5}` (strict integer 3–7). Original model-manifest and algorithm hashes must match the loaded artifacts, otherwise 409 `comparison_model_mismatch`. Analysis and comparison share the computation lock. Methods warm once and execute sequentially in shuffled order, using identical DNA/batch/model/frozen settings and saved watts. The returned run adds `comparison`: raw timing/stages, median/min/max/IQR, stage medians, work, canonical parity/decision differences, quality when labelled, median-derived estimated joules and hardware/code provenance. Failures leave original predictions intact. SQLite attaches completed comparison atomically and never recreates a deleted run.

Original scientific fields remain unchanged; comparison has a distinct measurement scope. Stopping client waiting may still let the computation finish and attach. See [DASHBOARD_INTEGRATION.md](DASHBOARD_INTEGRATION.md) for frontend state and actual workflow evidence.

## What is preserved

SQLite history is created at `data/local/runs.sqlite3`, ignored by Git. Each completed run stores normalized DNA, its hash/name/length, input source/annotation provenance, base quality counts, every candidate (including unscored candidates), scorer identity, scores/thresholds, actual routes, work counts, stage timing, original model manifest, timestamp and measurement provenance. Model loading/warm-up, HTTP validation, serialization/transfer and database writes are outside the engine computation timer. Hardware/versions and model-manifest/algorithm hashes accompany that single computation.

The response's `evaluation` is `null` for arbitrary input, including a user-uploaded copy of a demo FASTA: the server cannot assume its labels. Selecting the verified `sample_id` uses the bundled labels. Its metrics count unscoreable annotated canonical boundaries as false negatives and interpret absent annotations as unannotated, not experimentally inactive. Population test evaluation is obtained separately from `/evaluation`; it is not upload-specific accuracy.

Estimated energy is `assumed_power_watts × timing_ms.total_ms / 1000` joules. Both the assumption and exact measured engine time are saved. This is a constant-power estimate, not direct laptop energy measurement. Runs contain **one original** timing observation. Part 4 can attach a separate repeated comparison with its own median/variation/stages/counters/quality/provenance. Existing Part 2 benchmark records remain unchanged and are served separately by /benchmarks when artifact identities match.

Renaming changes only presentation metadata; reopening never reruns or adopts a new model, threshold, power setting or timing. History/export retrieval still works if the current model is unavailable. SQLite transactions commit complete snapshots, and SQL parameters handle names/IDs safely. Deletion removes the history entry; it is not a secure erasure guarantee for database pages/backups. Copy the database while the service is stopped to back up local history.

## Exports

Examples:

```text
/api/runs/{id}/export?format=json
/api/runs/{id}/export?format=csv
/api/runs/{id}/export?format=html
/api/runs/{id}/export?format=json&scope=filtered&type=donor&min_score=0.5&predicted_only=true
```

Default scope is `all`. Set `scope=filtered` to apply optional type, minimum model score, predicted-only and `query` search filters (ID/position/motif/type, up to 120 characters). Applying filters to `scope=all` is rejected rather than silently ignored. Scores that are unavailable fail a minimum-score filter. JSON includes the selected rows and explicit `export` scope/filter/count fields. Full-run timing, work, energy and evaluation are retained and identified as complete-computation measurements, even when rows are filtered.

CSV has one rectangular header: `record,field,value` followed by the candidate columns. `record=metadata` rows preserve input DNA, identities, settings, measurements, assumptions and export scope; structured values are JSON. `record=candidate` rows use the named candidate columns. Metadata remains present when there are zero candidates. Floating-point scores retain their original precision. Formula-like user strings are prefixed with an apostrophe for spreadsheet safety.

HTML shows the same selected candidate values, run settings and provenance, repeats the table header when printed, and can be saved as PDF using the browser's Print command. To keep printing practical it identifies DNA by name/hash/length; full normalized DNA is in the saved run and JSON/CSV. Names and metadata are escaped; reports use no scripts, remote fonts or other remote assets. Filenames derive from the run ID. Every format uses the saved snapshot, not current analysis state.

## Verification

```powershell
python -m pip install -r backend/requirements-dev.txt
python -m unittest discover -s backend/tests -p "test_*.py" -v
node --test frontend/tests/analysis.test.js frontend/tests/api.test.js frontend/tests/real-samples.test.js
```

Forty-five Python tests (14 API/storage/report checks, five comparison checks and 26 scientific checks) and twelve JavaScript tests pass. Tests cover restart/rename/delete, export agreement/filters, labels versus unknown truth, empty results, invalid input, N/edge handling, missing models, corrupt samples/evaluation identity, database/inference failures, request limits, CORS, escaping, real routing and concurrent transactions. Some Windows sandboxes block Python's event-loop sockets; test execution must permit local sockets.

Actual Uvicorn process launch/restart also passed, with a real annotated adaptive sample, CSV/JSON/HTML retrieval and occupied-port messaging. A synthetic 100,000-base `GTAG` stress request produced 50,000 raw candidates, 49,950 detailed evaluations and a maximum inference batch of 512; it saved/reopened/exported successfully. Its single engine measurement was 845.8739 ms, **not** a repeated benchmark or biological accuracy result. Local QA evidence and generated reports are in `qa/experiments/backend-service/verification.json` and its sibling files. These tests did not download data; fresh disconnected-machine packaging validation remains Part 5.

Implementation follows [FastAPI lifespan guidance](https://fastapi.tiangolo.com/advanced/events/), [CORS documentation](https://fastapi.tiangolo.com/tutorial/cors/), and [Python SQLite transactions](https://docs.python.org/3.12/library/sqlite3.html).

## Release update: 9 October 2026

Part 5 now supplies the combined launcher, locked setup, offline package verification and submission materials. Earlier pending statements describe the historical development state. See [LOCAL_RELEASE.md](LOCAL_RELEASE.md) and [MANUAL_TESTING.md](MANUAL_TESTING.md).
