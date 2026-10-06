# EcoSplice folder guide

Run all commands from the project root. This organisation separates interface code, analysis code, scientific artifacts and development evidence.

| Location | Purpose |
| --- | --- |
| `frontend/src/` | Existing green React interface and browser utilities |
| `frontend/public/` | Static assets copied by Vite |
| `frontend/index.html` | Frontend entry point |
| `frontend/tests/` | JavaScript utility and FASTA integration tests |
| `backend/ecosplice/` | Importable Python analysis package; currently sequence/coordinate utilities |
| `backend/tests/` | Python unit tests and real dataset checks |
| `scripts/data/` | Development-time source downloads and dataset preparation |
| `data/raw/` | Original downloaded reference cache, ignored by Git |
| `data/processed/` | Frozen labelled windows, split membership, provenance and verification |
| `data/demo/` | Small real FASTA files for an offline demonstration |
| `docs/` | Dataset methods, five-part implementation plan and this folder guide |
| `qa/screenshots/` | Local UI screenshots, ignored by Git |
| `qa/experiments/` | Local regeneration/check outputs, ignored by Git |
| `node_modules/` | Installed JavaScript dependencies, ignored by Git |
| `dist/` | Generated production frontend, ignored by Git |

Root files stay small and practical: README for setup, PROJECT_HANDOVER for continuation, package files and Vite configuration for tooling, and `start-dashboard.cmd` for launch. Git settings preserve byte-level scientific artifact hashes.

## Commands

```powershell
npm run dev
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

`start-dashboard.cmd` still starts the frontend from the root. Vite reads `frontend/` and writes its production build to root `dist/`. Dependencies stay in root `node_modules/`; they do not need reinstalling after the move.

## Where the next work belongs

Add prediction/model and algorithm modules inside `backend/ecosplice/`. Add training utilities alongside dataset scripts under a purposeful `scripts/models/` folder when Part 2 starts. Create model artifacts under `models/` when a real model is saved, and experiment records under `results/` when measured experiments exist. Add FastAPI and database modules inside the Python package in Part 3. Do not create empty placeholder folders for unimplemented features.

The saved dataset remains immutable during this reorganisation. Its preparation-code hashes record the original implementation in Git commit `fadf3c6`. Relocated preparation scripts retain the scientific algorithm, but newly generated manifests correctly identify their current code paths and hashes. Verify equivalent dataset output using the three file hashes in the frozen manifest, rather than requiring the entire new provenance manifest to be identical.

## Organisation checks: 6 October 2026

All seven JavaScript tests and ten Python tests passed after the move. The production frontend build passed. Running the relocated preparation script into `qa/experiments/dataset-reorganization` reproduced all three derived-data hashes. Frozen dataset, manifest, verification and demo files were also checked byte-for-byte against the initial Git commit and remain unchanged. Local evidence is in `qa/experiments/reorganization-verification.json`.
