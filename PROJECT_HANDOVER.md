# EcoSplice: project handover and completion plan

Updated: 9 October 2026. All five implementation parts are complete. Historical notes and the original acceptance checklist remain below; explicitly listed future work is not implemented.

## Current continuation: five-part implementation

The work is grouped into five parts in [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md). All five parts are complete: real dataset/model, algorithms, service/history, dashboard/measurements, and local release/submission. Preserve the existing interface and local-only scope.

### Part 5 implemented on 9 October 2026

- `start-ecosplice.cmd` starts one loopback service with the built React interface and API at port 8765. `setup-ecosplice.cmd` prepares Python 3.12, the complete dependency lock and caches; a prebuilt ZIP needs no Node. Missing builds/models/dependencies and occupied ports have clear errors. Fresh extracted setup and actual offline HTTP/restart/export/100k checks use isolated history and deny outbound sockets.
- Consolidated three stylesheets into `frontend/src/app.css`, preserving their final cascade. Updated Vite to 7.3.7 and esbuild to 0.28.1 after advisory review; npm install reported zero vulnerabilities. Chart build intermediates moved to QA. No frozen model/dataset or measurement artifacts changed.
- Shorter headings and expandable explanations keep the green interface minimal. A visible Load → Analyse → Compare → Export path follows real completed work, including reopened comparisons. It never marks a measurement complete merely from page navigation. `guide-page.jsx` supplies concise instructions and detailed methods on demand.
- `/api/samples/{sample_id}/fasta` downloads integrity-checked demo DNA. `data/demo/EcoSplice_test.fasta` is a byte-identical copy of REAL-003 (ARVCF, 2,402 bases). Uploads retain no invented labels. `docs/MANUAL_TESTING.md` explains the flow and expected checks.
- Delivered seven-page `docs/submission/EcoSplice_Report.pdf`, editable report source, native 13-slide `EcoSplice_Presentation.pptx`, architecture SVG/Mermaid, demo script and viva notes. Every report page and slide was rendered and visually reviewed; slides contain editable diagrams, tables and charts. PDF plus Markdown were selected because the bundled Windows document-rendering environment lacks LibreOffice.
- 49 Python and 14 JavaScript tests and production build pass. Windows sandbox blocks asyncio's internal localhost socket pair; approved test/service runs resolve it. The earlier approval-review usage-limit failure recovered. Final guided UI and fresh package evidence are recorded under QA and in the release/integration docs.
- Read `docs/LOCAL_RELEASE.md` for packaging/setup and `docs/MANUAL_TESTING.md` for user testing. No public deployment, Git commit or push was made for this work.

### Part 4 implemented on 8 October 2026

- Connected every React page to actual FastAPI predictions, saved held-out evaluation, repeated measurements and SQLite history. Removed fixture DNA/scores/timings/validation records; `data.js` now contains navigation only. Preserved the green interface, linked candidate explorer, QC and phone navigation.
- Added focused API/workspace/comparison/validation/report modules. Correlation plus generation/abort checks reject stale responses; input/file reads cannot overwrite later edits. Loading, empty, offline/degraded, retry and failures are explicit, without sample fallback. Modal focus/keyboard handling and unavailable context/scorer explanations are implemented.
- Added persisted same-input comparisons (3–7 repeated trials, one warm-up per method, shuffled sequential method order). All methods use original saved input/model/batch/settings/power; median/min/max/IQR, stages, work, annotation quality, prediction differences and provenance are saved. Original predictions/single-run timings remain unchanged. Frozen reference benchmarks require matching artifact identities.
- Validate shows actual donor/acceptor detailed/adaptive/preliminary metrics and descriptive test curves; no input accuracy without labels. Reports reopens/renames/deletes and exports all or filtered rows from one server snapshot. Filter search/type/minimum score/predicted-only choices agree across CSV/JSON/HTML. HEAD preflight plus native HTTP downloads works in the in-app browser.
- Development frontend is now **127.0.0.1:5188**, with Vite `/api` proxy to backend **127.0.0.1:8765**; ports 5173/5174 belonged to other apps. No public deployment. Launch the two existing scripts separately until Part 5 provides the combined production launcher.
- All **45 Python tests**, **12 JavaScript tests** and the production build pass. Browser sample/upload/analysis/comparison/history/restart/rename/export, input/service failures, no-label handling, empty/N/edge inputs and phone layout pass. All main screens fit 390×844 without horizontal body overflow; no console warnings/errors observed.
- A browser-driven 100,000-base synthetic GTAG stress run produced 50,000 candidates, 49,950 eligible calls and peak batch 512. Original single compute: **1165.6214 ms**. Seven-repeat medians: exhaustive **1482.9209 ms**, filtered **805.0881 ms**, adaptive **412.4652 ms**. These are synthetic stress measurements, not accuracy claims. Replacing DNA during the comparison clears the old display; completed work remains attached to the original saved run.
- Real ARVCF (2,402 bp) three-repeat medians were **32.1583 / 6.8484 / 3.0955 ms**; adaptive avoided 280/339 detailed calls but changed three decisions and reduced this cropped sample's donor/acceptor F1. Population evaluation remains distinct.
- Read [docs/DASHBOARD_INTEGRATION.md](docs/DASHBOARD_INTEGRATION.md) for contracts and verification. Local evidence is under `qa/experiments/part4-ui/` and `qa/screenshots/part4-*.jpg`. QA used a separate history database; do not copy test runs into ordinary history.
- At Part 4 completion, Part 5 was still pending; it is now completed as recorded above.

### Part 3 implemented on 8 October 2026

- Added `backend/ecosplice/api.py`, `storage.py` and `reports.py`. FastAPI startup loads and warms saved models once; no training/download. SQLite saves complete immutable scientific snapshots with normalized DNA, provenance, quality, original model/thresholds/routes, counts, stage timing and hardware/version/code hashes. Names are independently mutable. Local database is ignored by Git.
- APIs provide strict raw DNA/single-record FASTA predictions, verified annotated sample access, matching held-out evaluation, health/model status, paginated runs, reopen/rename/delete and CSV/JSON/printable HTML exports. Arbitrary DNA has `evaluation=null`; only explicit verified sample IDs use bundled labels. Unscored annotated edges count as false negatives. Failed real requests never receive fixture results.
- Exports explicitly support all versus filtered scope. Filtering retains original full-computation measurements/settings, with clear selected/total counts. CSV is rectangular with metadata/candidate records and spreadsheet-safe strings. Printable HTML escapes input and uses no external assets. All formats come from the same saved snapshot.
- Estimated energy uses actual single-run engine time times explicit assumed power (default 15 W), with units/assumptions saved. It is not laptop power measurement or repeated-benchmark evidence. Separate repeated comparisons and quality/speed views were added in Part 4.
- `python scripts/start_backend.py`, `npm run dev:backend` and `start-backend.cmd` start a single-worker service at `127.0.0.1:8765`. Port 8000 was unavailable on this laptop. `--port`/`ECOSPLICE_PORT`, `ECOSPLICE_MODEL_DIR` and `ECOSPLICE_DB_PATH` configure launch. Missing/invalid models allow history reads while predictions fail clearly; database/inference/busy/input/size errors have consistent envelopes. Documentation/OpenAPI require no CDN assets.
- Computation is serialized to reduce measurement contention; simultaneous analyses receive an explicit busy response. `client_request_id` echoes a frontend correlation token, not an idempotency key. Part 4 implements UI stale-response protection, cancellation/loading/error presentation.
- All 40 Python tests (14 new API checks) and seven JavaScript tests passed. Actual HTTP process restart/reopen/rename/export/delete and occupied-port messaging passed. A synthetic 100,000-base motif-rich HTTP request yielded 50,000 candidates, 49,950 detailed evaluations, peak batch 512; saved/reopened/exported successfully. Single engine time was 845.8739 ms. QA evidence: `qa/experiments/backend-service/verification.json`. No downloads occurred; fresh offline packaging validation remains Part 5.
- Read [docs/LOCAL_SERVICE.md](docs/LOCAL_SERVICE.md) for the current API/persistence/export contract. React integration was pending at the end of Part 3; Part 4 now supplies real results throughout.

### Part 2 implemented on 7 October 2026

- Saved real CPU model `ecosplice-v1-64223ad070d6` in `models/ecosplice-v1/`. It contains preliminary 22-base single-letter logistic coefficients and detailed 102-base single-letter/adjacent-pair logistic coefficients. Runtime uses only pinned NumPy; training uses pinned SciPy/sklearn/threadpoolctl.
- `scripts/models/train_models.py` verifies frozen source hashes, fits on train only, selects thresholds/routing on validation, persists choices, and then evaluates test. Detailed validation macro F1 0.7695 exceeds short-context reference 0.6937. Fitted coefficients export to safe numeric `.npz` arrays, with sklearn prediction parity within `1e-12`.
- Detailed canonical-candidate test F1: donor 0.7987, acceptor 0.7173. Donor precision/recall: 0.8063/0.7911; acceptor: 0.7424/0.6939. This is sampled chr22 evaluation, not genome-wide accuracy. Calibration bins/Brier scores are descriptive; displayed scores must remain model scores rather than confidence/probability claims.
- Preliminary thresholds: donor 0.36, acceptor 0.31. Detailed thresholds: donor 0.41, acceptor 0.44. Adaptive fast bounds: donor <=0.18 or >=0.52; acceptor <=0.0775 or >=0.655. Intermediate cases call detailed; final score uses the actual final scorer's threshold.
- Adaptive sampled test F1: donor 0.7858, acceptor 0.7238. It avoids 12,132 of 15,020 detailed evaluations (80.77%). Donor test F1 loss exceeds its validation selection tolerance; this is disclosed without tuning from test. Retain the quality/speed trade-off when presenting results.
- `backend/ecosplice/algorithms.py` implements actual exhaustive, filtered and adaptive processing with streaming batches, stage times, work counts, input hashes and provenance. Exhaustive scores every eligible position, even on motif-free input. Filtered uses the same detailed scorer. Adaptive never calls detailed for accepted fast cases.
- `scripts/analyze_sequence.py` loads saved artifacts and predicts from one FASTA/raw DNA file offline. It has no training/download dependency and fails clearly for invalid input/missing models. Arbitrary files receive no invented accuracy metric.
- `scripts/models/verify_algorithms.py` warms loaded models, shuffles method order and records five fresh computations per input, with medians/spread/raw stages/counters/hardware. It also evaluates four full held-out cropped demo regions, counting unscoreable annotated edges as false negatives. Two explicit synthetic 100,000-base stress inputs pass parity and bounded-batch checks; synthetic stress has no biological accuracy claim.
- Exhaustive/filtered canonical scores agree within `1e-12`; routing tests instrument true detailed call counts. Independent retraining produced byte-identical weights and the model manifest. All 26 Python and seven JavaScript tests passed.
- Genuine reports are in `results/model-evaluation.json`, `algorithm-verification.json`, `demo-predictions.json` and `model-reproducibility.json`. Pseudocode, complexity, measured tables and reproduction commands are in [docs/MODELS_AND_ALGORITHMS.md](docs/MODELS_AND_ALGORITHMS.md).

**Integration contract (current after Part 4):** React uses genuine service results throughout. The API now loads saved models at startup; never retrain/download there. Preserve one-based motif starts, full-context/N eligibility reasons, scorer-specific thresholds, final routes, model/dataset identity and computation timings. Adaptive routing applies to frozen thresholds; custom decision thresholds require compatible policy selection or disabling shortcuts. UI score filtering is separate from changing saved prediction decisions. SQLite/API/reports, single-run estimated energy, complete UI integration and repeated comparisons are implemented. Keep original predictions separate from attached comparison summaries.

### Folder organisation: 6 October 2026

Source files now live in `frontend/` and `backend/`, their tests live alongside them, data utilities live in `scripts/data/`, and the detailed plan lives in `docs/`. Root npm commands and `start-dashboard.cmd` continue to work. QA screenshots and experiment outputs are grouped under `qa/screenshots/` and `qa/experiments/`. Read [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for the map and future file locations.

The frozen scientific artifacts were not rewritten during organisation. Their manifest retains the original preparation-code identities from Git commit `fadf3c6`; moving and updating current script paths changes the current code hash, not the saved dataset identity. Reproduction with the reorganised scripts should match the three derived-data file hashes; the new manifest records the current preparation code and therefore has a different fingerprint.

Organisation verification passed: seven JavaScript tests, ten Python tests, production build, all three regenerated dataset hashes, and byte-for-byte preservation of the frozen scientific artifacts. Local evidence is saved in `qa/experiments/reorganization-verification.json`. Part 2 was subsequently completed as recorded above.

### Part 1 implemented on 6 October 2026

- Added `backend/ecosplice/sequence.py`: strict DNA/FASTA parsing and the shared 102-base context/coordinate contract, plus strand-aware boundary extraction and coordinate mapping.
- Added `scripts/data/download_reference.py`: frozen GENCODE human v49 annotation and UCSC GRCh38 chr22 DNA, with cached source checksums. Small verified HTTPS ranges recover stalled annotation transfers. Raw cache totals about 106 MB and is ignored by Git.
- Added `scripts/data/prepare_dataset.py`: deterministic selection of 400 protein-coding genes, exon-adjacency labels, both strand orientations, GT/AG hard negatives and ordinary negatives. All comprehensive chr22 transcript boundaries protect the negative pool, including noncanonical annotations.
- Prepared **134,603** unique labelled 102-base windows across **304** non-overlapping genomic groups. Frozen counts: train 93,231; validation 20,153; test 21,219. Every split contains donor, acceptor and non-site labels.
- Excluded 134 noncanonical boundary occurrences, 1,119 duplicate-context rows and 12 conflicting-label context rows. These counts describe this selected subset, not all human annotations.
- Saved class counts, membership, source hashes, preprocessing-code hashes, derived-file hashes and audit results in `data/processed/manifest.json` and `split_membership.json`. Dataset fingerprint: `a884895b613c8923e41e1830c2d475377071272848f2fb4c9f24335f936c5464`.
- Saved four genuine, held-out FASTA demos in `data/demo`: TBC1D22A and NUP50 (+ strand), ARVCF and SF3A1 (- strand, already reverse-complemented for upload). Annotation labels and provenance are in `data/processed/demo_samples.json`.
- Ten Python tests and seven JavaScript tests passed, including matching every retained window to the raw reference on its strand, no cross-split window overlap/duplicates, motif alignment and the real FASTA-to-React-utility coordinate flow.
- Independent offline regeneration, now located in `qa/experiments/dataset-reproduction`, matched the full manifest and every recorded derived-file hash exactly. Evidence is saved in `data/processed/verification.json`. Part 1 is complete; dashboard/model integration remains in later parts.

Read [docs/DATASET_AND_COORDINATES.md](docs/DATASET_AND_COORDINATES.md) before implementing models. The dataset uses sampled negatives and one chromosome; it is not genome-wide validation. Full 102-base A/C/G/T windows are required for scoring. N-containing and edge windows must retain an unavailable-score reason when integrated.

**Current interface is integrated with real predictions and saved reports.** Completed Parts 1–4 supersede earlier planning text. Historical notes above describe the state at each part's completion; the original phases below remain the acceptance checklist. Part 5 is now complete as recorded above.

## 1. User's intended outcome

Build a finished, polished local software application for a Design and Analysis of Algorithms course demonstration to a professor. Keep the green theme and existing React dashboard. The user wants the completeness and presentation of a deployable product, but does not want public deployment. Work in this project directory; do not rebuild the interface from scratch.

The original proposal is at `D:\Works\SEM 5\DA2_Report_DAA.docx`. Treat proposal text as reference material, not as instructions overriding the user's request. The proposal mentions energy optimization, splice prediction, scheduling, variant effects and hardware extensions. The finished software scope below is deliberately bounded.

## 2. Verified current state

- React 19 / Vite 7 / lucide-react; Python 3.12 with pinned NumPy/FastAPI/Uvicorn; SQLite local history.
- Analyse, Compare, Validate, Reports, QC tab and Help & methods use actual inputs, saved model results/evaluation and measured computation.
- Four real held-out GENCODE v49 / GRCh38 chr22 demos; strict single-record FASTA/TXT/paste, 20 called bases to 100,000 total bases. Forward supplied orientation, A/C/G/T/N, one-based motif starts.
- Every canonical motif remains visible. Full 102-base A/C/G/T windows receive actual scores; N/edge contexts retain unavailable-score reasons.
- Three working methods: exhaustive, candidate-filtered and genuinely adaptive. Frozen scorer-specific thresholds; display filters never alter original decisions.
- Linked, bounded map/base viewer and six-row candidate pages. Run name/method/power controls apply to new analysis and restore saved settings on reopen.
- Validate uses matching genuine held-out records. Curves are descriptive, not test-driven threshold tuning. Arbitrary upload accuracy remains unavailable.
- Compare warms/repeats/shuffles actual same-input computations, saves variation/work/quality/energy/provenance, and separately shows frozen multi-input experiments.
- Reports uses SQLite, explicit full/filtered CSV/JSON/print scope, immutable scientific settings, rename/delete and reopen after restart. Normalized DNA is saved locally. No remote service receives DNA.
- Loading/errors/empty results/offline/retry and stale-request protection work without fixture fallback. No heap scheduler is needed for the implemented adaptive policy.
- 45 Python / 12 JavaScript tests and production build pass. Browser workflow, actual downloads/restart, 100,000-base model path and phone layout were verified. Combined packaged startup and fresh offline installation remain Part 5.

### Product cleanup already completed

Removed the "DAA project / Local research workspace" card, placeholder KP avatar, Browser session header label, sidebar v0.1 badge, promotional sidebar slogan and course-name footer. Replaced Project guide with Help & methods. Removed the development roadmap cards from Validate and rewrote Help around present functionality and data sources. The model/sample disclosures remain accurate until genuine results replace them.

### Relevant files

| File | Responsibility |
| --- | --- |
| `frontend/src/App.jsx` | Application state, navigation, sample loading, downloads, report data |
| `frontend/src/workspace.jsx` | Sequence map, DNA viewer, linked table/inspector, input bar and workflow |
| `frontend/src/pages.jsx` and focused page modules | QC/help/input modal, genuine comparison/validation/history screens |
| `frontend/src/data.js` | Navigation only; no fixtures |
| `frontend/src/lib/analysis.js`, `lib/api.js`, `useWorkspace.js` | Input QC, API errors/adapters/filters, request generation and workspace state |
| `frontend/src/components.jsx` | Shared presentation/loading/error components |
| `frontend/src/app.css` | Consolidated green UI, integration controls and responsive guide styling |
| `frontend/tests/` | 12 parser/QC/API/stale-response/export/real FASTA checks |
| `backend/ecosplice/sequence.py` | Python input, window and strand/coordinate contract |
| `backend/tests/` | 45 scientific, service/storage/report/comparison and failure checks |
| `scripts/data/` | Reference download and deterministic dataset preparation |
| `backend/ecosplice/model.py`, `algorithms.py`, `evaluation.py` | Portable saved-model inference, actual methods, metrics/selection |
| `scripts/models/`, `scripts/analyze_sequence.py` | Training, verification and offline real-prediction CLI |
| `models/ecosplice-v1/`, `results/` | Saved model/settings and genuine experiment records |
| `README.md` | Current setup, scope, limitations |
| `start-dashboard.cmd` | Current frontend launcher |

### Local commands

Normal: `npm run dev`, `npm test`, `npm run build`.

The system npm command previously pointed to a broken roaming installation. Working fallbacks:

```powershell
node node_modules/vite/bin/vite.js --host 127.0.0.1
node --test frontend/tests/analysis.test.js frontend/tests/api.test.js frontend/tests/real-samples.test.js
python -m unittest discover -s backend/tests -p "test_*.py" -v
node node_modules/vite/bin/vite.js build
node 'C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js' run dev
```

Frontend: `http://127.0.0.1:5188/`. Start the backend separately with `python scripts/start_backend.py` at port 8765. An existing preview process may or may not remain running in a new chat. If browser access times out while Vite reports ready, check whether sandbox networking prevents reaching that process; the previous preview required an approved unsandboxed local server process. Do not weaken firewall or system security settings to fix this.

## 3. Recommended final scope

An application that accepts DNA, validates it, predicts canonical donor/acceptor candidates using an actual trained model, compares exhaustive processing with candidate filtering and adaptive routing, displays measured runtime and model evaluation, estimates energy from measured runtime, saves runs locally, and exports reproducible reports.

Predict possible boundaries; do not present the system as cutting DNA or inferring complete exon/intron structures. Retain an explicit canonical-site scope. Start with input already oriented 5' to 3' in the direction being analysed; disclose forward-only processing. Reverse-complement analysis is a separate extension with explicit coordinate mapping if later included.

No required cloud account, login, public hosting, GPU, Jetson, NPU, IoT, federated learning or hardware power meter. Variant/cryptic-site claims and quantization stay future work unless separately requested. No claimed accuracy percentage or energy-saving target before measurements support it.

## 4. Implementation phases and acceptance criteria

### Phase 1: dataset and coordinate contract

1. Select a manageable, documented public annotation/sequence subset. Preferred research direction: matched GENCODE gene annotation and reference genomic DNA for one recorded assembly/release. Check data-use terms, source sizes and laptop feasibility before choosing the exact subset. Do not download a whole genome by default if a reproducible subset suffices.
2. Use genomic sequences containing introns. Spliced transcript/cDNA sequences alone do not preserve the intronic GT/AG boundaries being predicted.
3. Derive annotated donor and acceptor positions from exon/intron boundaries with correct strand orientation. Deduplicate boundaries shared across transcripts; retain gene and interval identities.
4. Create fixed-width contexts around motif starts. Specify alignment, edge padding or excluded edge windows, and N handling. Store how many windows are excluded.
5. Include annotated positive boundaries, hard negative GT/AG occurrences without a positive annotation, and ordinary negative positions needed to evaluate exhaustive scoring. Describe negatives as non-sites under the chosen annotation, not experimentally proven never-active sites.
6. Split train/validation/test by genes or non-overlapping genomic groups; prevent overlapping or duplicate windows leaking across splits. A chromosome split is another valid approach if enough classes remain in each partition.
7. Freeze the split manifest and random seed. Fit encoders/model/calibration only on appropriate training data. Choose thresholds on validation, then report final test performance.
8. Bundle a small set of genuine held-out annotated sequence examples for an offline professor demonstration, with source, assembly, gene/interval and labels.

Acceptance: regenerable dataset script, manifest with counts per class/split, no cross-split duplicates/overlaps, verified positive motif alignment, and real annotated examples in the app.

Sources: [GENCODE human annotation and genome files](https://www.gencodegenes.org/human/); [scikit-learn grouped splitting](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html). The completed Part 1 and Part 2 notes above record the frozen subset/model choices.

### Phase 2: reproducible prediction model

1. Train a small CPU model on encoded DNA contexts. Start with a simple interpretable classifier, such as logistic regression, as a reference. Select a modest detailed model based on validation quality and measured inference cost; do not assume that a larger model is better.
2. Define donor/acceptor/non-site outputs or separate donor/acceptor classifiers consistently. The exported score must have a documented meaning.
3. Save model artifact, encoding, context width, model identifier/version, training settings, dataset manifest identifier and threshold settings. Training runs separately; ordinary app startup only loads the artifact.
4. If scores are displayed as probabilities/confidence percentages, assess calibration using held-out data. Otherwise call them model scores. Do not infer reliability from a number simply being between 0 and 1.
5. Compare against a motif-only rule/reference so the learned model must demonstrate useful discrimination among motif occurrences.

Acceptance: reproducible training command, saved artifact, deterministic inference, validation report and independent test results. No fixture score generator on the genuine analysis path.

Source: [scikit-learn probability calibration](https://scikit-learn.org/stable/modules/calibration.html).

### Phase 3: actual DAA algorithms

Implement three methods with a shared coordinate and output contract:

1. **Exhaustive baseline:** form contexts and run the detailed scorer at every eligible position. Apply the declared canonical output rule afterwards.
2. **Candidate-filtered method:** scan once for GT/AG, form contexts and run the same detailed scorer only at canonical candidates. Apply the same output rule/threshold. For canonical-site comparison, the baseline and filtered outputs should agree within numerical tolerance.
3. **Adaptive method:** run a genuinely cheaper preliminary scorer at canonical candidates; retain sufficiently decisive decisions and route uncertain candidates to the detailed scorer. Tune the routing policy on validation data. Store preliminary score, chosen route, final scorer and final score. Compare any accuracy loss against saved work and measured runtime.

Do not assign Fast path after already computing the expensive score for every candidate; that changes a label without avoiding the expensive work. Do not introduce artificial sleep delays to make the baseline slower. A priority queue is only needed if actual priority ordering is implemented; merely reordering identical work does not establish energy savings.

Show counts of scanned positions, canonical candidates, preliminary evaluations and detailed evaluations. Write pseudocode, algorithm rationale and time/space complexity for the actual code.

For n positions, k canonical candidates, detailed per-window cost C(w,M) and preliminary cost L(w), approximate work is baseline O(n*C), filtered O(n + k*C), adaptive O(n + k*L + m*C) for m routed candidates. The exact model evaluation cost must be explained. For fixed window/model sizes, baseline and candidate filtering are both O(n) in the worst case; the intended benefit is less expensive work, not a false change from quadratic to linear time. Sorting/heap complexity should appear only if implemented.

Acceptance: algorithm implementations, operation counters, output parity checks for baseline vs filtered canonical mode, real adaptive route counts and trade-off evaluation.

### Phase 4: Python API and reliable analysis flow

Recommended architecture: React interface + local Python FastAPI service + saved model artifacts. Use SQLite for local saved runs when history is added. FastAPI can run on a local ASGI server such as Uvicorn: [official server guidance](https://fastapi.tiangolo.com/deployment/manually/).

1. Add backend modules for parsing, QC, context extraction, model loading, scoring, method comparison and result schemas.
2. Backend remains authoritative for valid input and model results. Keep frontend QC as immediate feedback but enforce matching rules server-side.
3. Define schemas for sequence, sample ID, coordinate convention, method, thresholds, model version, candidate results, QC, runtime stages, work counts, energy assumptions and errors.
4. Provide health/model status, real samples, analysis, comparison, evaluation and run/report retrieval endpoints. Use synchronous requests initially if fast; add cancellable job processing/status only when measured workload needs it.
5. Configure API address/origins/limits through documented settings. Bound sequence/file sizes, prevent path traversal, and return useful validation errors. Never execute uploaded content or load user-supplied serialized model artifacts.
6. Show service unavailable, model missing, rejected input, running analysis, completed results and failed analysis states. Ignore stale responses if the user changes sequence while a request is in flight. Never silently replace a failed real run with sample scores.

Acceptance: a custom sequence receives genuine backend predictions; API errors are readable and recoverable; displayed results always belong to the selected run.

### Phase 5: measured benchmarks and real evaluation

1. Time parsing/QC, scanning, context preparation, preliminary inference, detailed inference and total algorithm work using an appropriate monotonic high-resolution clock. Separate backend computation from network/UI latency.
2. Load the model before timed runs; warm up, repeat, alternate/randomize method order, and report median plus spread and repetition count. Use equivalent batching, thread settings and hardware for fair comparisons. Disclose any method-specific batching overhead.
3. Test multiple sequence lengths and motif densities. Use actual genomic sequences where available; clearly labelled synthetic sequences may additionally stress performance but cannot establish biological accuracy.
4. Record machine/CPU, RAM, Python/library/model versions, seed, input hash, length, motif count and settings. Do not reuse cached results inside the timed benchmark.
5. Report donor and acceptor precision, recall, F1, confusion matrices and threshold trade-offs. Consider precision-recall curves because non-site positions are numerous. Show support/class counts; accuracy alone is insufficient.
6. Distinguish model evaluation on held-out annotated data from an unlabelled uploaded sequence. An arbitrary FASTA has no ground truth, so show predictions without inventing sequence accuracy.
7. Evaluate the complete filtering/routing pipeline over the declared test domain so skipped sites and routing mistakes count. A test consisting only of retained candidates can conceal recall losses. State how noncanonical annotations are excluded or counted.

Acceptance: repeatable benchmark command, saved raw measurements, length/work/runtime charts and test metrics derived from genuine labels. A speedup may be absent on short sequences; report it honestly.

### Phase 6: energy from measured time

1. Replace fixture runtime with measured algorithm runtime.
2. Energy in joules = assumed average active power in watts * measured runtime in seconds. Record the assumption, timed interval and units in UI/exports.
3. Compare both methods under the same power assumption unless separate measurements justify a different assumption.
4. Call the result estimated energy and estimated reduction. Under a shared power assumption this largely reflects runtime reduction, not independent proof of device energy savings.
5. Carbon conversion is optional secondary information; keep it out of the main flow if it clutters the DAA comparison.

Acceptance: estimates update with measured results and assumptions, units are correct, provenance is exported, no laptop-battery measurement claim.

### Phase 7: finish every product page

| Page | Final output |
| --- | --- |
| Analyse | Real input/QC, run status, total candidates, scores, motifs, consistent positions, linked map/base viewer/table/details and real processing routes |
| Compare | Same-input methods, measured runtime, work counts, memory where measured, estimated energy, sequence-length chart and algorithm explanation |
| Validate | Named model and dataset/split, real test counts, class metrics, matrices, threshold curves and baseline/adaptive trade-offs; explicitly independent of unlabelled input |
| Reports | Saved run list, reopen/export, input/model/data provenance, settings, results, measurements and assumptions in CSV/JSON/print report |
| Help & methods | Concise input instructions, biology terms, coordinate rules, model/data sources and implemented method limits |

Remove development scaffolding, outdated guide text, fake account elements and duplicate disclosures once real features are in place. Preserve green styling, keyboard access, focus states, responsive tables/viewer, legible text and meaningful empty/loading/error states. Label each source accurately: real annotated sample, user input or explicit synthetic demonstration.

### Phase 8: saved runs and complete reports

1. Store completed runs and settings locally in SQLite with stable IDs/timestamps. Reopen a run after restarting the app; allow renaming, deletion and a clear retention policy. Specify whether raw DNA is saved or only hashes/results.
2. Snapshot model/threshold/energy settings with the run so later settings changes do not rewrite past results.
3. CSV should include coordinate convention, type, motif, score meaning, actual route/scorer and annotation status only when known. JSON should include complete provenance and measured stages/counts.
4. Make full-results vs filtered-results export scope explicit. Ensure printed summaries and tables match the selected run and paginate cleanly.
5. Persist benchmark/evaluation artifacts separately as reproducible experiment records. Keep evaluation dataset identity distinct from run input identity.

Acceptance: reload/restart preserves runs; report downloads reflect saved results; no mixed run/sample/threshold data.

### Phase 9: tests, code cleanup and laptop performance

1. Keep current utility tests; add Python tests for coordinate alignment, strand normalization if used, edge windows, N handling, motifs, model schemas and counters.
2. Verify train/test isolation and annotated boundary extraction on known examples. Test baseline/filtered output equality and adaptive routing before/after detailed evaluation.
3. Exercise full upload -> validation -> prediction -> comparison -> save/reopen -> export, plus empty, malformed, oversized, motif-free and service-error inputs.
4. Test the supported maximum sequence length. Batch contexts instead of materializing every full window at once; paginate/virtualize large tables and bound map markers. Avoid promising 100,000-base support until the model path passes this check.
5. Measure memory with a named method if shown; don't fabricate memory figures. Separate model-resident memory from extra per-run allocations.
6. Remove unused legacy components/imports and consolidate duplicate CSS after functional integration. Add lint/format checks, pinned dependency setup and sensible folder boundaries.

Acceptance: meaningful tests pass; build succeeds; common failure states and long inputs behave; there are no placeholder successful results or console errors.

### Phase 10: local release package and submission materials

1. Add a documented setup script and single local launch command for backend plus the built frontend, preferably served from the local backend. Keep dev mode separate. Check missing dependencies/model artifacts and port conflicts clearly.
2. Pin Python dependencies, keep npm lockfile, include example settings, model artifact and appropriately licensed small samples. Include training/data preparation scripts and model/data hashes.
3. Prepare dependencies once, then verify that normal inference, sample loading, history and exports work without internet. Do not train or download datasets during the professor's demonstration.
4. Record tested operating system/runtime versions and a fresh-environment setup test. Public deployment is outside this request. A container is optional, not a completion requirement.
5. Update the report to describe the implemented software. Include architecture, data provenance, pseudocode, time/space complexity, genuine result tables/charts, trade-offs and limitations. Move unimplemented hardware/advanced features to future work.
6. Prepare slides, a 3-5 minute demo sequence, screenshots and viva notes explaining GT/AG candidates, classifier scores, n/k/w, actual optimization, accuracy vs speed and estimated vs measured energy.

Acceptance: one launch starts a complete offline-ready demonstration after setup; report/slides match the shipped implementation; results can be traced to reproducible experiments.

## 5. Completion checklist

- [x] Genuine annotated dataset and frozen train/validation/test partitions.
- [x] Saved trained model and reproducible training/evaluation scripts.
- [x] Real backend predictions for custom sequences.
- [x] Exhaustive and filtered algorithms with fair comparison and work counts.
- [x] Adaptive routing avoids actual detailed work and its quality trade-off is measured.
- [x] Measured runtime replaces hardcoded snapshots throughout the genuine result path.
- [x] Energy estimates use measured time and explicit assumptions.
- [x] Validate reflects held-out labels, never fabricated truth for arbitrary uploads.
- [x] All dashboard pages and exports agree on run/model/settings.
- [x] Saved local history survives restarting.
- [x] Error, loading, empty and long-input flows pass.
- [x] Clean green product UI and accessible navigation remain intact.
- [ ] Fresh setup and normal offline launch verified.
- [ ] Submission report, slides and demonstration materials match actual features.

## 6. Suggested message for a new chat

> Continue EcoSplice in `D:\Projects\DNA Splice Site Identification`. Read `PROJECT_HANDOVER.md`, `README.md`, and the current source before editing. Keep the existing green React UI. I want a finished local application to demonstrate to my professor; do not publicly deploy it. Parts 1–4 are complete: data/model/algorithms, backend/SQLite, genuine React integration and repeated measurements. All five parts are implemented. Read the Part 5 notes and manual testing guide, then address the user's requested follow-up. Preserve working sequence/QC/export features. Use actual predictions and measured runtime; do not replace missing work with hardcoded scores, fake timing or synthetic validation claims. Keep the plan/status file updated as each phase is implemented. Explain the results and algorithm choices in beginner-friendly language.

A new chat may not have this chat's full context. This file and current source are the explicit handover; check actual files rather than assuming every planned feature exists.
