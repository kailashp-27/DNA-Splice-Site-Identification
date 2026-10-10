# EcoSplice completion in five parts

Updated: 9 October 2026. Preserve the green React UI. Local use only; no public deployment.

| Part | Deliverables | Status |
| --- | --- | --- |
| 1. Dataset and coordinate foundation | Frozen public genomic source, boundary extraction, 102-base windows, annotation-aware negatives, isolated splits, manifest, annotated offline demos, coordinate tests | Complete and verified |
| 2. Prediction models and DAA methods | Reproducible CPU training, saved artifacts, validation thresholds, independent evaluation, exhaustive/filtered/adaptive implementations, counters and pseudocode | Complete and verified |
| 3. Local service and saved runs | FastAPI input/prediction/evaluation APIs, SQLite history, rename/delete/reopen, CSV/JSON/print contracts, readable failures | Complete and verified |
| 4. React integration and measured comparisons | Genuine outputs on every page, stale-request protection, runtime benchmarks, quality trade-offs, explicit energy assumptions, responsive QA | Complete and verified |
| 5. Local release and submission | Maximum-input and full-workflow tests, cleanup, dependency setup, one launch command, offline check, architecture/report/slides/demo/viva notes | Complete and verified |

These are sequential implementation parts, not separate Codex chats. The detailed acceptance criteria remain in [PROJECT_HANDOVER.md](../PROJECT_HANDOVER.md). See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for current file locations.

## Part 1 choices

- Frozen annotation: GENCODE human v49, comprehensive annotation, chr22 records only.
- Sequence: UCSC GRCh38/hg38 primary chr22, corresponding to NC_000022.11. No patch/alternate contigs.
- Up to 400 protein-coding genes with annotated introns; all annotation types protect the negative pool.
- DNA is normalised to the annotated strand for dataset preparation. User input remains forward-only and must already have the direction the user wishes to analyse.
- Context: 50 bases + two-base motif + 50 bases. Full A/C/G/T windows only; no invented padding.
- Output coordinate: one-based motif start. Genomic provenance uses zero-based half-open intervals and strand.
- Train/validation/test: approximately 70/15/15% of connected components of expanded genomic gene spans, seed 20261006. Duplicate windows, including reverse complements, are removed globally before training.
- Real FASTA files in data/demo now receive genuine model predictions through the React upload flow. Only selecting an explicit bundled sample ID uses its verified annotation labels.

## Reproduction

```powershell
python scripts/data/download_reference.py
python scripts/data/prepare_dataset.py
python -m unittest discover -s backend/tests -p "test_*.py" -v
```

The download command needs internet once. Preparation and checks use only Python's standard library and the cached sources.

## Part 1 measured outputs

Prepared 400 genes across 304 genomic groups, producing 134,603 unique windows:

| Split | Donor | Acceptor | Non-site | Total |
| --- | ---: | ---: | ---: | ---: |
| Train | 3,654 | 3,811 | 85,766 | 93,231 |
| Validation | 858 | 821 | 18,474 | 20,153 |
| Test | 900 | 918 | 19,401 | 21,219 |

Four held-out demo files are in `data/demo`, with annotation metadata in `data/processed/demo_samples.json`. The existing React upload utilities preserve their labelled motif positions. Ten Python tests and seven JavaScript tests passed. No prediction model or accuracy claim is part of this foundation.

An independent offline preparation, now stored in `qa/experiments/dataset-reproduction`, matched the full manifest and all three derived-file hashes exactly. Verification evidence is saved in `data/processed/verification.json`. Current scripts are in `scripts/data/`; source reorganisation changes preparation-code provenance in newly generated manifests while retaining identical derived-data hashes. The frozen dataset remains unchanged.

## Part 2 completed: 7 October 2026

Saved model `ecosplice-v1-64223ad070d6` bundles a 22-base preliminary logistic scorer and a 102-base detailed scorer with adjacent-pair features. Training uses train only; thresholds/routing are frozen on validation before test evaluation. Independent retraining produced byte-identical weights and metadata.

Canonical-candidate test F1: detailed donor **0.7987**, acceptor **0.7173**; adaptive donor **0.7858**, acceptor **0.7238**. Adaptive avoids **80.77%** of detailed evaluations on sampled test candidates, with the documented donor quality loss. Scores remain model scores, not calibrated biological probabilities.

Three operational methods, work counters, real routing, stage timings and an offline CLI are implemented. Baseline/filtered scores agree within `1e-12`. Five-repeat measurements and four complete held-out demo-region evaluations are saved. Two 100,000-base stress inputs pass bounded-batch/parity checks. All 26 Python and seven JavaScript tests pass.

See [MODELS_AND_ALGORITHMS.md](MODELS_AND_ALGORITHMS.md) for pseudocode, complexity, thresholds, limitations, commands and actual measurement tables. Artifacts are in `models/ecosplice-v1/` and `results/`. At the end of Part 2, React integration was still pending. Part 4 now supplies genuine results throughout.

## Part 3 completed: 8 October 2026

Local FastAPI service loads/warms the saved models once. Strict DNA/FASTA validation, actual predictions, labelled sample access and matching held-out evaluation are available through the API. Completed runs persist in SQLite with normalized DNA, original model/settings, score eligibility/routes, work/timing, hardware/version provenance and explicit runtime-based energy assumptions. History supports reopen, rename and delete; all/filtered CSV, JSON and printable HTML use one saved snapshot. Failures return readable errors without sample fallback.

Launch with `python scripts/start_backend.py` (localhost port 8765) or `start-backend.cmd`. Port/model/database overrides and missing-file/occupied-port messages are implemented. Forty Python and seven JavaScript tests pass. Actual HTTP process restart preserves runs; a 100,000-base motif-rich request saves/reopens/exports with batches bounded at 512. Local evidence is in `qa/experiments/backend-service/`. See [LOCAL_SERVICE.md](LOCAL_SERVICE.md) for endpoint, persistence, export and launch contracts.

## Part 4 completed: 8 October 2026

Every dashboard screen now uses real FastAPI data, measured runtime and SQLite history. Added stale-response/correlation handling, guarded file reads, real loading/empty/error/retry states, explicit no-label accuracy handling, and all/filtered server exports. The same-input comparison API warms each method then repeats fresh computations in shuffled order, saving medians/spread/stages/work/quality/energy/provenance without rewriting original predictions. Genuine held-out validation and frozen multi-input benchmarks have verified artifact identities.

Forty-five Python and twelve JavaScript checks plus the production build pass. Browser verification includes actual CSV/JSON/HTML downloads, process/browser restart/reopen/rename, FASTA upload, failures, 100,000-base scoring/comparison and phone layout. Development frontend now uses port 5188 and proxies the local backend on 8765. Details/evidence: [DASHBOARD_INTEGRATION.md](DASHBOARD_INTEGRATION.md).

## Part 5 completed: 9 October 2026

Added a combined loopback launcher, isolated pinned setup with offline caches, deterministic prebuilt ZIP and fresh-environment verification. The green UI now uses one consolidated stylesheet, shorter headings, expandable explanations and a progress-aware Load → Analyse → Compare → Export guide. A real ARVCF FASTA download and manual checklist support self-testing.

Delivered a seven-page PDF report with editable Markdown, architecture diagram, 13-slide native PowerPoint deck, demo script and beginner viva notes. Scientific figures use real held-out evaluation and recorded measurements. All 49 Python and 14 JavaScript tests plus the production build pass. Fresh package checks cover actual HTTP, offline operation, restart/export consistency and maximum input. Final guided-flow browser evidence is recorded in DASHBOARD_INTEGRATION.md.

Normal launch: `start-ecosplice.cmd`, then http://127.0.0.1:8765. All work stays local. See [LOCAL_RELEASE.md](LOCAL_RELEASE.md), [MANUAL_TESTING.md](MANUAL_TESTING.md) and [submission guide](submission/README.md).
