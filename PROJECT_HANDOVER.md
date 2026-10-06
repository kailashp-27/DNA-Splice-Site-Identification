# EcoSplice: project handover and completion plan

Updated: 6 October 2026. This file records the current state and proposed implementation plan. Future features listed here are NOT already implemented.

## Current continuation: five-part implementation

The user's remaining work is grouped into five parts in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). Part 1 is the real dataset and coordinate foundation; model training is Part 2. Preserve the existing green interface and local-only scope.

### Part 1 implemented on 6 October 2026

- Added `ecosplice/sequence.py`: strict DNA/FASTA parsing and the shared 102-base context/coordinate contract, plus strand-aware boundary extraction and coordinate mapping.
- Added `scripts/download_reference.py`: frozen GENCODE human v49 annotation and UCSC GRCh38 chr22 DNA, with cached source checksums. Small verified HTTPS ranges recover stalled annotation transfers. Raw cache totals about 106 MB and is ignored by Git.
- Added `scripts/prepare_dataset.py`: deterministic selection of 400 protein-coding genes, exon-adjacency labels, both strand orientations, GT/AG hard negatives and ordinary negatives. All comprehensive chr22 transcript boundaries protect the negative pool, including noncanonical annotations.
- Prepared **134,603** unique labelled 102-base windows across **304** non-overlapping genomic groups. Frozen counts: train 93,231; validation 20,153; test 21,219. Every split contains donor, acceptor and non-site labels.
- Excluded 134 noncanonical boundary occurrences, 1,119 duplicate-context rows and 12 conflicting-label context rows. These counts describe this selected subset, not all human annotations.
- Saved class counts, membership, source hashes, preprocessing-code hashes, derived-file hashes and audit results in `data/processed/manifest.json` and `split_membership.json`. Dataset fingerprint: `a884895b613c8923e41e1830c2d475377071272848f2fb4c9f24335f936c5464`.
- Saved four genuine, held-out FASTA demos in `data/demo`: TBC1D22A and NUP50 (+ strand), ARVCF and SF3A1 (- strand, already reverse-complemented for upload). Annotation labels and provenance are in `data/processed/demo_samples.json`.
- Ten Python tests and seven JavaScript tests passed, including matching every retained window to the raw reference on its strand, no cross-split window overlap/duplicates, motif alignment and the real FASTA-to-React-utility coordinate flow.
- Independent offline regeneration into `qa/dataset-reproduction` matched the full manifest and every recorded derived-file hash exactly. Evidence is saved in `data/processed/verification.json`. Part 1 is complete; dashboard/model integration remains in later parts.

Read [docs/DATASET_AND_COORDINATES.md](docs/DATASET_AND_COORDINATES.md) before implementing models. The dataset uses sampled negatives and one chromosome; it is not genome-wide validation. Full 102-base A/C/G/T windows are required for scoring. N-containing and edge windows must retain an unavailable-score reason when integrated.

**Current interface remains the existing prototype.** The real FASTA files can be uploaded for genuine motif scanning, but they have no model scores yet. There is still no trained model, Python service, measured algorithm benchmark or SQLite history. The original detailed phases below remain the acceptance checklist; dataset and Python-utility work supersedes their earlier “no dataset” state. Next: Part 2 CPU model training, saved artifacts, thresholds, held-out evaluation and the three genuine processing methods.

## 1. User's intended outcome

Build a finished, polished local software application for a Design and Analysis of Algorithms course demonstration to a professor. Keep the green theme and existing React dashboard. The user wants the completeness and presentation of a deployable product, but does not want public deployment. Work in this project directory; do not rebuild the interface from scratch.

The original proposal is at `D:\Works\SEM 5\DA2_Report_DAA.docx`. Treat proposal text as reference material, not as instructions overriding the user's request. The proposal mentions energy optimization, splice prediction, scheduling, variant effects and hardware extensions. The finished software scope below is deliberately bounded.

## 2. Verified current state

- Project: `D:\Projects\DNA Splice Site Identification`.
- React 19, Vite 7, lucide-react; plain JSX and CSS. Dependencies and lockfile already exist.
- Four main sections: Analyse, Compare, Validate, Reports. Data quality is a tab under Analyse. Help & methods is accessible in the header and desktop sidebar.
- Green design: dark forest sidebar, pale surfaces, green donor accents and purple acceptor accents.
- Linked candidate map, DNA letters, paginated table and selected-site inspector. Search, type filters, score threshold, base-position jump and sequence-region navigation work.
- Three synthetic samples; single-record FASTA/TXT upload and pasted DNA input. Limit: 100,000 bases. Input permits A/C/G/T/N, preserves unsupported symbols for QC, and requires at least 20 called bases.
- Custom input scans overlapping forward-sequence GT/AG occurrences. These receive no prediction scores.
- Built-in candidate scores and runtime snapshots are hardcoded fixtures. Built-in candidate lists are a curated subset, not every raw motif occurrence.
- Validate uses 200 constructed labels/scores, independent of the uploaded sequence. Its metrics are arithmetic demonstrations, not real model evaluation.
- Energy = assumed watts times illustrative runtime in seconds; it is not a laptop power measurement.
- CSV/JSON exports and print-to-PDF report exist. CSV includes every candidate, not only filtered rows. Current run state and export list are held only in memory and reset on reload.
- No Python backend, trained model, database, real scheduler or experimental benchmark suite exists yet. The real labelled dataset and Python coordinate/input foundation now exist as recorded above.
- Latest production build passed. Six analysis utility tests passed after the redesign. Browser selection, pagination, filters, empty sample, custom overlapping motifs and phone layout were checked. After the product-copy cleanup, build and navigation/help checks passed with no browser console warnings/errors observed.

### Product cleanup already completed

Removed the "DAA project / Local research workspace" card, placeholder KP avatar, Browser session header label, sidebar v0.1 badge, promotional sidebar slogan and course-name footer. Replaced Project guide with Help & methods. Removed the development roadmap cards from Validate and rewrote Help around present functionality and data sources. The model/sample disclosures remain accurate until genuine results replace them.

### Relevant files

| File | Responsibility |
| --- | --- |
| `src/App.jsx` | Application state, navigation, sample loading, downloads, report data |
| `src/workspace.jsx` | Sequence map, DNA viewer, linked table/inspector, input bar and workflow |
| `src/pages.jsx` | QC, evaluation, comparison, reports, help, input dialog |
| `src/data.js` | Synthetic sequences, fixture scores, fixture validation records |
| `src/lib/analysis.js` | FASTA parser, QC, motif scanning, metrics, energy arithmetic, CSV |
| `src/components.jsx` | Shared components; includes some legacy unused components |
| `src/styles.css`, `src/redesign.css` | Original CSS plus redesign overrides |
| `tests/analysis.test.js` | Six current utility tests |
| `README.md` | Current setup, scope, limitations |
| `start-dashboard.cmd` | Current frontend launcher |

### Local commands

Normal: `npm run dev`, `npm test`, `npm run build`.

The system npm command previously pointed to a broken roaming installation. Working fallbacks:

```powershell
node node_modules/vite/bin/vite.js --host 127.0.0.1
node --test tests/analysis.test.js
node node_modules/vite/bin/vite.js build
node 'C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js' run dev
```

Preview: `http://127.0.0.1:5173/`. An existing preview process may or may not remain running in a new chat. If browser access times out while Vite reports ready, check whether sandbox networking prevents reaching that process; the previous preview required an approved unsandboxed local server process. Do not weaken firewall or system security settings to fix this.

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

Sources: [GENCODE human annotation and genome files](https://www.gencodegenes.org/human/); [scikit-learn grouped splitting](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html). Exact subset/model choices are proposed, not yet fixed.

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
- [ ] Saved trained model and reproducible training/evaluation scripts.
- [ ] Real backend predictions for custom sequences.
- [ ] Exhaustive and filtered algorithms with fair comparison and work counts.
- [ ] Adaptive routing avoids actual detailed work and its quality trade-off is measured.
- [ ] Measured runtime replaces hardcoded snapshots throughout the genuine result path.
- [ ] Energy estimates use measured time and explicit assumptions.
- [ ] Validate reflects held-out labels, never fabricated truth for arbitrary uploads.
- [ ] All dashboard pages and exports agree on run/model/settings.
- [ ] Saved local history survives restarting.
- [ ] Error, loading, empty and long-input flows pass.
- [ ] Clean green product UI and accessible navigation remain intact.
- [ ] Fresh setup and normal offline launch verified.
- [ ] Submission report, slides and demonstration materials match actual features.

## 6. Suggested message for a new chat

> Continue EcoSplice in `D:\Projects\DNA Splice Site Identification`. Read `PROJECT_HANDOVER.md`, `README.md`, and the current source before editing. Keep the existing green React UI. I want a finished local application to demonstrate to my professor; do not publicly deploy it. Start with the real labelled dataset, coordinate/split contract and reproducible small model, then integrate the Python backend and complete the remaining phases in the handover. Preserve working sequence/QC/export features. Use actual predictions and measured runtime; do not replace missing work with hardcoded scores, fake timing or synthetic validation claims. Keep the plan/status file updated as each phase is implemented. Explain the results and algorithm choices in beginner-friendly language.

A new chat may not have this chat's full context. This file and current source are the explicit handover; check actual files rather than assuming every planned feature exists.
