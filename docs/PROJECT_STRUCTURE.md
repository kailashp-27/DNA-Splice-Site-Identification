# EcoSplice folder guide

Run all commands from the project root. This organisation separates interface code, analysis code, scientific artifacts and development evidence.

| Location | Purpose |
| --- | --- |
| `frontend/src/` | Existing green React interface and browser utilities |
| `frontend/public/` | Static assets copied by Vite |
| `frontend/index.html` | Frontend entry point |
| `frontend/tests/` | Input/QC, API/stale-response/filter/export and real FASTA tests |
| `backend/ecosplice/` | Sequence/model/algorithm/comparison utilities, FastAPI service, SQLite storage and report renderers |
| `backend/tests/` | Python unit tests and real dataset checks |
| `scripts/data/` | Development-time source downloads and dataset preparation |
| `scripts/models/` | Reproducible development-time training and algorithm measurements |
| `scripts/analyze_sequence.py` | Offline CLI using saved model artifacts |
| `scripts/start_backend.py` | Loopback FastAPI launcher with configuration and port checks |
| `models/ecosplice-v1/` | Portable saved coefficients, preprocessing, thresholds/routing and model provenance |
| `results/` | Genuine model evaluation, raw benchmark measurements and demo predictions |
| `data/raw/` | Original downloaded reference cache, ignored by Git |
| `data/local/` | Runtime SQLite history, created on launch and ignored by Git |
| `data/processed/` | Frozen labelled windows, split membership, provenance and verification |
| `data/demo/` | Small real FASTA files for an offline demonstration |
| `docs/` | Dataset methods, five-part implementation plan and this folder guide |
| `qa/screenshots/` | Local UI screenshots, ignored by Git |
| `qa/experiments/` | Local regeneration/check outputs, ignored by Git |
| `node_modules/` | Installed JavaScript dependencies, ignored by Git |
| `dist/` | Generated production frontend, ignored by Git |

Root files stay small and practical: README for setup, PROJECT_HANDOVER for continuation, package files and Vite configuration for tooling, and `start-ecosplice.cmd` / `setup-ecosplice.cmd` for normal launch/setup. `start-dashboard.cmd` / `start-backend.cmd` remain development shortcuts. Git settings preserve byte-level scientific artifact hashes. Python runtime dependencies are in `backend/requirements.txt`; HTTP test dependencies add `backend/requirements-dev.txt`.

## Commands

```powershell
npm run dev
npm run dev:backend
npm test
npm run test:backend
npm run build
npm run preview
```

Direct Python commands remain available without npm:

```powershell
python scripts/data/download_reference.py
python scripts/data/prepare_dataset.py
python -m unittest discover -s backend/tests -p "test_*.py" -v
```

`start-dashboard.cmd` starts the integrated frontend at 127.0.0.1:5188 from the root. Start `start-backend.cmd` separately on port 8765; Vite proxies /api. Vite reads `frontend/` and writes its production build to root `dist/`. Dependencies stay in root `node_modules/`; they do not need reinstalling after the move.

## Where the next work belongs

Parts 2 and 3 supply model/algorithm/service/storage/report modules inside `backend/ecosplice/`, training/measurement utilities in `scripts/models/`, saved artifacts under `models/`, and scientific experiment records under `results/`. Part 4 is complete: focused React comparison/validation/reports pages, useWorkspace state and lib/api adapters integrate actual service results. Part 5 supplies the combined local production launcher and submission documents, alongside existing scripts/docs. Read [LOCAL_SERVICE.md](LOCAL_SERVICE.md) for the current API. Do not create empty placeholder folders for unimplemented features.

The saved dataset remains immutable during this reorganisation. Its preparation-code hashes record the original implementation in Git commit `fadf3c6`. Relocated preparation scripts retain the scientific algorithm, but newly generated manifests correctly identify their current code paths and hashes. Verify equivalent dataset output using the three file hashes in the frozen manifest, rather than requiring the entire new provenance manifest to be identical.

## Part 4 module map

- `frontend/src/App.jsx`: navigation, next-run controls, shared filters, native HTTP exports.
- `frontend/src/useWorkspace.js`, `lib/api.js`: actual service state, readable errors, request generation, real coordinate adapters and filter/export contracts.
- `frontend/src/comparison-page.jsx`, `validation-page.jsx`, `reports-page.jsx`: focused scientific and persistence screens.
- `frontend/src/pages.jsx`, `workspace.jsx`, `components.jsx`: input/QC/help, linked bounded explorer and shared presentation.
- `frontend/src/app.css`: layout for new controls, measurements, history and responsive tables.
- `backend/ecosplice/comparison.py`, `backend/tests/test_comparison.py`: fresh fair measurements, quality/work/provenance and failure/persistence checks.
- `docs/DASHBOARD_INTEGRATION.md`: contracts and actual full-workflow evidence.

## Organisation checks: 6 October 2026

All seven JavaScript tests and ten Python tests passed after the move. The production frontend build passed. Running the relocated preparation script into `qa/experiments/dataset-reorganization` reproduced all three derived-data hashes. Frozen dataset, manifest, verification and demo files were also checked byte-for-byte against the initial Git commit and remain unchanged. Local evidence is in `qa/experiments/reorganization-verification.json`.

## Part 5 release files

- `start-ecosplice.cmd`, `setup-ecosplice.cmd`: user launch and one-time setup.
- `scripts/start_local.py`, `setup_local.py`, `package_release.py`, `verify_local_release.py`: combined service, locked preparation, ZIP and fresh offline checks.
- `backend/ecosplice/local_app.py`, `backend/requirements-lock.txt`: production static/API routing and complete Python runtime lock.
- `frontend/src/guide-page.jsx`, `lib/workflow.js`, `app.css`: minimal help, real progress and consolidated styles.
- `docs/submission/`: final report/source, slides, architecture, figures, demo script and viva notes. Builders stay under `scripts/submission/`.
- `docs/MANUAL_TESTING.md`, `data/demo/EcoSplice_test.fasta`: self-test checklist and real input.
- `config.example.ps1`, `docs/THIRD_PARTY_NOTICES.md`: optional configuration and bundled software notices.
- `releases/`: deterministic ZIP (ignored by Git) and source hash manifest. `.venv/`, `.cache/`, local history and QA remain ignored.
