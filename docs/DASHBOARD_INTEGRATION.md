# Part 4: genuine dashboard and measured comparisons

Completed: 8 October 2026. React now uses the local Python service throughout; illustrative sample scores, timing fixtures and constructed validation records have been removed. The existing green interface remains.

## Architecture and behavior

`App.jsx` owns navigation, shared display filters and next-run controls. `useWorkspace.js` handles health/catalog, input loading, analysis, comparison and reopen. `lib/api.js` supplies readable errors, coordinate adapters, export/filter contracts and a generation/AbortController gate. Focused comparison, validation and reports pages request real endpoints. `data.js` contains navigation only.

Selecting a sample retrieves verified oriented DNA; analysis sends its explicit sample ID. Upload/paste sends actual text, with no inferred labels. Python validates independently, loads frozen model coefficients once, runs the chosen algorithm and commits a complete SQLite run before returning success. The UI renders actual scores/thresholds/routes/reasons from that response.

Changing input or reopening invalidates earlier work. Each analysis includes a correlation token which must match the response. Generation checks reject late responses even when transport ignores abort. No request failure displays canned results. Explicit loading, offline/degraded model, retry, empty-result and error states are available. Stopping client waiting does not guarantee server cancellation or prevent a completed run being saved.

The modal validates alphabet, single first-position FASTA header, minimum known bases, normalized size and file byte size. File reads cannot overwrite later edits; failed/oversized file selection clears earlier file text. Modal focus is trapped/restored and Escape closes it.

Candidate filtering uses the original scorer-specific prediction decisions. Minimum displayed score/search/type/predicted-only filters change rows, not biological thresholds or adaptive routing. Rows are paginated (six); map previews are bounded at 160 markers; DNA rendering is bounded to the local viewport. Actual full-resolution rows remain in saved results/exports.

## Fresh same-input comparisons

`POST /api/runs/{id}/comparison` accepts an integer `repeats` from 3 to 7 (default 5). The interface offers 3/5/7. Original model manifest and algorithm hashes must match current artifacts, otherwise return 409 and require a new analysis. Computations share the analysis lock; busy requests fail explicitly.

For each method, one untimed operational warm-up precedes fresh timed computations on identical normalized DNA, batch size, thresholds, policy and saved power. A reproducible seed shuffles sequential method order per repetition. Timings come from the actual engine, excluding HTTP, serialization, storage, UI and warm-up.

The comparison records raw totals/stages, median/min/max/IQR, stage medians, work counts, hardware/versions/code hashes, coordinate/eligibility agreement, exhaustive/filtered score agreement, adaptive decision differences, and annotation metrics when known. Independent stage medians need not sum to the total median. Zero assumed power gives zero estimated joules and an unavailable percentage energy reduction.

Completed measurements attach atomically to SQLite without rewriting original run predictions or single-run timing/energy. If a run is deleted during measurement it is not recreated. Failures leave the original snapshot intact; partial results are not attached. Comparison rows use median runtime for energy; original Analyse/Reports summary retains its original single-run measurement.

`GET /api/benchmarks` serves the frozen Part 2 multi-input experiment only when model/dataset/manifest/algorithm identities match. It remains separate from the active run's measurement and explicitly identifies synthetic stress inputs.

## Validation and reports

Validate retrieves matching saved held-out evaluation. Donor/acceptor and detailed/adaptive/preliminary selections display their actual canonical-candidate matrices, support and metrics. Detailed/preliminary threshold sliders inspect saved test curves only; they do not tune thresholds or change current predictions. Adaptive's measured quality/work trade-off and donor test loss are disclosed.

Input-specific annotation metrics appear separately for verified samples. Uploaded FASTA—even a copy of a demo—has no automatic known answers. Unscored annotated canonical edges count as missed boundaries.

Reports retrieves paginated SQLite history with reopen, validated rename, explicit delete confirmation and error/retry states. Reopen restores actual original method/power/name controls. Rename updates only matching active metadata, preserving scientific snapshots and any attached comparison.

CSV, JSON and printable HTML share the saved server report. Explicit all versus filtered scope includes search/type/minimum score/predicted-only choices. HEAD checks availability before the browser streams an HTTP attachment; this works when blob URL downloads are restricted. HEAD uses the same validation/existence checks and skips rendering the payload. HTML opens inline and uses browser Print → Save as PDF. Report metadata retains the complete input computation even when candidate rows are filtered.

## Local development

Run `python scripts/start_backend.py` and `npm run dev`. Frontend: **127.0.0.1:5188**; backend: **127.0.0.1:8765**. Vite dev/preview proxy `/api`; override the target with `ECOSPLICE_BACKEND_URL` before launch. Separate API origins may use `VITE_API_BASE`, with compatible server CORS. Default CORS allows local ports 5188 and the previous 5173.

A combined production launcher, fresh dependency/offline setup verification and submission artifacts are Part 5.

## Verification evidence

All **45 Python** and **12 JavaScript** tests pass, including five comparison API checks, real artifact/coordinate/routing checks, export agreement, restart/deletion/failure paths, and response generation/error/export adapters. Production build passes. UI verification used the real loopback FastAPI service and an isolated SQLite database at `qa/experiments/part4-ui/runs.sqlite3`, preserving ordinary application history. One repeat of the full suite encountered memory-allocation errors; after stopping the temporary backend, the standalone full rerun passed all 45 tests in 8.321 seconds.

Browser checks:

- Verified ARVCF sample: 2,402 bases, 349 canonical candidates, adaptive score/route/scorer inspection, explicit 17 W assumption and saved UUID.
- Three-repeat actual ARVCF medians: exhaustive **32.1583 ms**, filtered **6.8484 ms**, adaptive **3.0955 ms**. Adaptive avoided 280/339 detailed calls (**82.6%**) and changed three decisions. Donor F1: detailed 0.750 versus adaptive 0.600; acceptor 0.333 versus 0.308. This is a cropped input annotation check, separate from held-out population evaluation.
- Donor/acceptor held-out screens match artifact metrics; descriptive slider changes the scenario while frozen metric cards remain unchanged.
- Acceptor + minimum score 0.5 + predicted-only filters selected nine candidates. Actual downloaded CSV/JSON and opened HTML have the same candidate values, UUID, settings, 17 W energy and attached comparison.
- Backend process restart, browser reload, rename and reopen preserve identity, predictions, original settings and comparison.
- Genuine FASTA upload scores the same DNA while explicitly showing no input-specific accuracy.
- Empty, unsupported symbols, short DNA, multiple FASTA records and 100,001-base input produce clear modal errors. N/edge contexts retain unavailable scores. Motif-free DNA completes with an exportable empty result.
- Stopping the backend produces a real error and zero successful fallback results; reconnect restores service/history. Missing model/inference/database/export failures are additionally covered by API tests.
- Synthetic 100,000-base GTAG stress input completes through the browser with 50,000 candidates, 49,950 eligible detailed calls and peak batch 512. Original single engine time: **1165.6214 ms**. Seven-repeat medians: exhaustive **1482.9209 ms**, filtered **805.0881 ms**, adaptive **412.4652 ms**. These stress inputs carry no accuracy claim.
- Replacing DNA while that comparison is pending clears earlier results and activates the new sequence. The old computation can still attach to its original saved run. An automated delayed-response check separately proves stale generation rejection even without effective cancellation.
- All main screens fit a 390×844 phone override (375 CSS pixels available beside the scrollbar) without horizontal body overflow. Candidate/comparison tables scroll inside their containers. Desktop checked at 1440×1000; no console errors/warnings observed.

Measurements vary with laptop workload; these are recorded observations, not performance guarantees. Peak batch is a work/memory-control count, not a measured memory usage figure. Raw evidence and reports are under `qa/experiments/part4-ui/`; screenshots under `qa/screenshots/part4-*.jpg`. Fresh offline installation, automated packaged launch and submission materials remain Part 5.

## Release update: 9 October 2026

Part 5 now supplies the combined launcher, locked setup, offline package verification and submission materials. Earlier pending statements describe the historical development state. See [LOCAL_RELEASE.md](LOCAL_RELEASE.md) and [MANUAL_TESTING.md](MANUAL_TESTING.md).

### Final minimal interface and guide

Shortened headings/copy, moved method/provenance/reference/stage/threshold explanations behind disclosure controls, and consolidated styles into app.css. The progress path uses loaded/valid input, a saved run, and a saved comparison. It is present across all screens; page navigation cannot fabricate completion. Reports remain usable for saved runs when the backend model is unavailable.

Actual browser verification on the combined local server (QA port 8767, separate history): empty stage gating; ARVCF load → adaptive run → three-repeat comparison → Reports; browser reload → saved history; Help instructions and actual FASTA download. ARVCF gives 349 candidates / 339 eligible, adaptive 59 detailed calls / 280 avoided, and three changed decisions. Current laptop observations were 43.068 / 6.731 / 4.520 ms medians; these are QA observations, not frozen reference artifacts. The downloaded DNA was checked against the delivered 2,402-base FASTA. Phone Help at 390×844 has body width 375 and no overflow. Current screenshots: qa/screenshots/part5-*.png. Console checks are recorded in local evidence.
