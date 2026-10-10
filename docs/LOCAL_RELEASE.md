# EcoSplice local release

Release 1.0.0, 9 October 2026. Windows 11 / Python 3.12.10 is the tested platform. No public deployment.

## Setup once

From a source checkout, install Python 3.12 and Node.js 20.19+ or 22.12+, then double-click `setup-ecosplice.cmd`, or run:

```powershell
python scripts/setup_local.py
```

This creates `.venv`, downloads pinned wheels into `.cache/wheels`, installs the complete runtime lock, runs `npm ci` with a private `.cache/npm` cache, and builds React. It does not download genomic data or train. Both caches and the environment are ignored by Git. Internet is needed for this one-time dependency preparation. The npm JS CLI fallback handles the broken global npm wrapper seen on the development laptop.

The release ZIP already contains the production React build and needs **Python 3.12 only**, with no Node.js installation. Extract it to a writable folder and run `setup-ecosplice.cmd` there. Avoid opening it directly inside the ZIP. If `python` points to another version, run `py -3.12 scripts/setup_local.py`.

`--offline` installs from an already prepared `.cache/wheels` and, for a source checkout, `.cache/npm`. Copy those caches from the same Windows/Python architecture for setup on a disconnected laptop. Normal use after setup needs no cache or internet. The ZIP excludes dependency caches and Python itself.

## One launch command

```powershell
.\start-ecosplice.cmd
```

Open **http://127.0.0.1:8765**. One Python process serves both the built green React dashboard and `/api`. The browser needs no account, remote fonts or CDN. The saved model loads during startup. Press Ctrl+C in its terminal to stop. After setup Node.js is unnecessary for normal application use.

For an occupied port:

```powershell
.\start-ecosplice.cmd --port 8766
```

Open the address printed by that terminal. Only loopback binds are permitted by the launcher. Model/database overrides remain available through `ECOSPLICE_MODEL_DIR` and `ECOSPLICE_DB_PATH`; ordinary use needs neither. A missing build, missing dependency, bad model or occupied port produces a readable message. Check files without starting a server with `.venv\Scripts\python.exe scripts/start_local.py --check`.

`config.example.ps1` shows optional environment settings using absolute paths from the application folder. Dot-source it in PowerShell if needed: `. .\config.example.ps1`. The launcher does not silently read an environment file. Scientific source credits and the bundled React/icon copyright notices are included in `docs/`.

## Saved runs and exports

SQLite history lives at `data/local/runs.sqlite3` relative to the extracted application, independent of the terminal's initial directory. Preserve that directory when upgrading. Back up the SQLite database while the service is stopped. Deleting a history entry leaves downloaded reports alone. The package builder never includes local history, user DNA, raw references, environments or QA databases.

Use Reports for JSON, CSV and printable HTML. The browser's Print / Save as PDF creates a PDF for the selected saved run. All or filtered export scope is explicit. Comparisons save with that run without changing its original predictions or timing.

## Development and reproduction

Development remains two processes: `python scripts/start_backend.py` on 8765 and `npm run dev` on 5188. Stop them before starting the combined application on the same port. Training and genomic downloads are separate utilities in `scripts/data` and `scripts/models`; no normal app path calls them.

Build a local ZIP with `python scripts/package_release.py`. Its `RELEASE_MANIFEST.json` records the SHA-256 of every distributed file. The repository retains the complete source, training windows and tests. The small ZIP includes reproduction utilities and manifests, but excludes the 58 MB training-window file and raw genomic caches. Recreating the training dataset requires the documented development-time download/preparation commands.

## Verification

`backend/tests/test_local_release.py` covers static/API routing, missing builds and analysis / comparison / restart / reopen / rename / exports / deletion while outbound socket connections are denied. The release verification script at `scripts/verify_local_release.py` checks an extracted ZIP with a fresh isolated environment using cached wheels, starts a real Uvicorn HTTP process with outbound sockets blocked, downloads every local frontend asset, exercises history and exports after a process restart, and tests the 100,000-base limit. Evidence is saved under ignored `qa/experiments/local-release/`.

Final browser verification of the combined server covers the progress guide, real ARVCF analysis, fresh three-method comparison, reports/history after reload, the actual sample FASTA download and concise help. Phone help at 390×844 has a 375-pixel body width without overflow. Earlier Part 4 QA additionally covers upload, actual report downloads, errors and long input. Screenshots and isolated QA history stay outside the release.

Scientific scope and source attribution: [dataset and coordinates](DATASET_AND_COORDINATES.md), [model and algorithms](MODELS_AND_ALGORITHMS.md). Submission materials: [submission guide](submission/README.md).
