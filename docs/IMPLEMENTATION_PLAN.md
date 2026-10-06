# EcoSplice completion in five parts

Updated: 6 October 2026. Preserve the green React UI. Local use only; no public deployment.

| Part | Deliverables | Status |
| --- | --- | --- |
| 1. Dataset and coordinate foundation | Frozen public genomic source, boundary extraction, 102-base windows, annotation-aware negatives, isolated splits, manifest, annotated offline demos, coordinate tests | Complete and verified |
| 2. Prediction models and DAA methods | Reproducible CPU training, saved artifacts, validation thresholds, independent evaluation, exhaustive/filtered/adaptive implementations, counters and pseudocode | Pending |
| 3. Local service and saved runs | FastAPI input/prediction/evaluation APIs, SQLite history, rename/delete/reopen, CSV/JSON/print contracts, readable failures | Pending |
| 4. React integration and measured comparisons | Genuine outputs on every page, stale-request protection, runtime benchmarks, quality trade-offs, explicit energy assumptions, responsive QA | Pending |
| 5. Local release and submission | Maximum-input and full-workflow tests, cleanup, dependency setup, one launch command, offline check, architecture/report/slides/demo/viva notes | Pending |

These are sequential implementation parts, not separate Codex chats. The detailed acceptance criteria remain in [PROJECT_HANDOVER.md](../PROJECT_HANDOVER.md). See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for current file locations.

## Part 1 choices

- Frozen annotation: GENCODE human v49, comprehensive annotation, chr22 records only.
- Sequence: UCSC GRCh38/hg38 primary chr22, corresponding to NC_000022.11. No patch/alternate contigs.
- Up to 400 protein-coding genes with annotated introns; all annotation types protect the negative pool.
- DNA is normalised to the annotated strand for dataset preparation. User input remains forward-only and must already have the direction the user wishes to analyse.
- Context: 50 bases + two-base motif + 50 bases. Full A/C/G/T windows only; no invented padding.
- Output coordinate: one-based motif start. Genomic provenance uses zero-based half-open intervals and strand.
- Train/validation/test: approximately 70/15/15% of connected components of expanded genomic gene spans, seed 20261006. Duplicate windows, including reverse complements, are removed globally before training.
- Scores and biological accuracy remain unavailable until Part 2. Real FASTA files in data/demo can already be uploaded for the existing motif scanner.

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

An independent offline preparation, now stored in `qa/experiments/dataset-reproduction`, matched the full manifest and all three derived-file hashes exactly. Verification evidence is saved in `data/processed/verification.json`. Current scripts are in `scripts/data/`; source reorganisation changes preparation-code provenance in newly generated manifests while retaining identical derived-data hashes. The frozen dataset remains unchanged. Next is Part 2; train only on the frozen training split and tune thresholds/routing only on validation.
