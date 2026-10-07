# EcoSplice

A DNA sequence analysis dashboard for **Energy-Optimized DNA Splice Site Identification**, a Design and Analysis of Algorithms course project.

The current version lets you inspect a sequence, find canonical GT/AG motifs, and explore how candidate filtering affects a model of processing work. It includes Python scripts for preparing a labelled chromosome 22 dataset. A trained prediction model is still to be added.

## Run the dashboard

Use Node.js 20.19+ or 22.12+. Run from the repository root:

```bash
npm install
npm run dev
```

Open [127.0.0.1:5173](http://127.0.0.1:5173). No Python server is needed for the dashboard. On Windows, `start-dashboard.cmd` also launches it once dependencies are installed.

Load a built-in sample, paste DNA, or upload a single FASTA record. Custom input supports up to 100,000 bases. `N` is accepted as an unknown base; invalid characters remain visible in the quality report and block scanning until corrected. Analysis requires at least 20 called bases.

## Dashboard pages

| Page | What it shows |
| --- | --- |
| Analyse | A linked candidate map, base viewer, results table, and sequence quality checks |
| Validate | Threshold filtering and confusion-matrix metrics on 200 constructed records |
| Compare | Operation models, illustrative timings, and adjustable energy/carbon assumptions |
| Reports | CSV and JSON exports, plus a printable report |
| Help & methods | Input guidance, biology background, and analysis scope |

## Reading the results

Custom sequences are scanned for every forward-sequence `GT` and `AG` occurrence. A motif is a candidate, not proof that a splice site is used. These results have no model score or measured runtime.

Positions are **1-based starts of the two-letter motif in the loaded sample**. They are not genomic coordinates or inferred exon boundaries. The browser scanner does not inspect the reverse complement, pair introns, detect noncanonical sites, or predict variant effects and cryptic-site activity.

The built-in sequences, candidate scores, validation labels, and timing snapshots are demonstration fixtures. Their metrics describe those fixtures, not the prepared biological dataset. Scores are not calibrated probabilities.

Energy is calculated as `assumed power × illustrative runtime`. Carbon uses an editable hypothetical grid factor. The dashboard does not measure device energy or demonstrate measured hardware savings.

The operation comparison is `O(n × w)` versus `O(n + k × w)`: n is sequence length, w is context width, and k is the number of motif candidates. With fixed w, both are O(n). Filtering reduces the detailed work and restricts coverage to canonical motifs.

## Prepare the reference dataset

Use Python 3.12. The scripts use the standard library and need internet for the first reference download:

```bash
python scripts/data/download_reference.py
python scripts/data/prepare_dataset.py
python -m unittest discover -s backend/tests -p 'test_*.py' -v
```

The references are GENCODE v49 annotations and GRCh38 chromosome 22. Downloaded files are cached in `data/raw/`; preparation can then run offline.

Prepared output includes 102-base windows, train/validation/test memberships, provenance, and verification records in `data/processed/`. The preparation groups overlapping gene spans and controls duplicate contexts across splits. This remains a single-chromosome dataset with sampled negatives, not a genome-wide evaluation.

Real FASTA examples are in `data/demo/`, with labels and provenance in `data/processed/demo_samples.json`. They can be uploaded for motif scanning, but their dataset labels are not connected to trained dashboard predictions.

## Development

```bash
npm test
npm run test:backend
npm run build
npm run preview
```

- `frontend/src/lib/analysis.js`: parsing, quality checks, motif scanning, metrics, and exports.
- `frontend/src/data.js`: dashboard demonstration fixtures.
- `backend/ecosplice/`: Python sequence and coordinate utilities.
- `scripts/data/`: reference downloads and dataset preparation.

Sequences stay in browser memory for the session. The dashboard does not upload or persist them, and reloading resets the workspace. Exports are generated locally.

## Project notes

- [Dataset and coordinate rules](docs/DATASET_AND_COORDINATES.md)
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Folder guide](docs/PROJECT_STRUCTURE.md)
- [Project handover](PROJECT_HANDOVER.md)

These cover the remaining model, service, evaluation, and measurement work.
