# EcoSplice

A React dashboard for the first software demonstration of **Energy-Optimized DNA Splice Site Identification**, a Design and Analysis of Algorithms course project.

## Completion work

The remaining work is organised into five parts in [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md): dataset/coordinates; models/algorithms; backend/history; UI/measurements; release/submission.

Part 1 adds Python data preparation alongside the existing React interface. Its source selection, window rules, coordinate mapping and leakage controls are documented in [docs/DATASET_AND_COORDINATES.md](docs/DATASET_AND_COORDINATES.md). These utilities do not yet add model scores to the dashboard.

```powershell
python scripts/download_reference.py
python scripts/prepare_dataset.py
python -m unittest discover -s tests -p "test_*.py" -v
```

Use Python 3.12. The data scripts require no third-party Python packages. Downloading the frozen GENCODE v49 annotation and GRCh38 chromosome 22 requires internet once; preparation uses cached files. Windows' bundled curl is used for robust downloads when available. Generated real FASTA examples live in `data/demo`; the current upload flow can scan their motifs without inventing prediction scores. Ground-truth labels and genomic provenance are stored separately in `data/processed/demo_samples.json`.

## Run locally

Requirements: Node.js 20.19+ or 22.12+ and npm.

```powershell
npm install
npm run dev
```

Open http://127.0.0.1:5173. After dependencies are installed, you can also double-click `start-dashboard.cmd` to launch the app. The application does not need a Python service for this first version.

If your Windows npm command points to a broken global installation, use the npm CLI bundled with Node:

```powershell
node 'C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js' install
node 'C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js' run dev
```

## Included pages

- **Analyse:** a linked candidate map, DNA base viewer, searchable results, and selected-site details. Select a marker, highlighted motif, or table row to inspect the same candidate across all views. Browse sequence regions or jump to a base position.
- **Data quality tab:** alphabet checks, unknown bases, GC content, and base composition within Analyse.
- **Validate:** a threshold-dependent confusion matrix, precision, recall, F1, and accuracy calculated on 200 constructed records.
- **Compare:** processing schematics, cost models, hardcoded timing snapshots, and adjustable energy/carbon assumptions.
- **Reports:** complete CSV/JSON downloads and a printable report that can be saved as PDF.
- **Help & methods:** introductory biology, input instructions, analysis scope, and reference links.

Use **Try a sample**, **Paste DNA**, or **Upload FASTA** to load a sequence. The active-sequence dropdown switches directly between the three synthetic samples. Custom inputs support up to 100,000 bases. Invalid characters stay visible in the quality report; motif scanning is blocked until alphabet and minimum-length checks pass. `N` is accepted as an unknown base.

## What is real and what is illustrative

Input parsing, quality statistics, canonical motif scanning, threshold filtering, evaluation arithmetic, energy conversion, and local file exports run in the browser.

Built-in DNA sequences are artificial. Their listed candidates and 0–1 scores are constructed fixtures. Additional GT/AG motifs can occur in those sequences. Runtime snapshots are hardcoded. Validation labels are also constructed; the resulting metrics describe only that fixture.

Custom sequences receive every forward-sequence GT/AG motif occurrence, with no fabricated model scores or timing results. Positions are **1-based starts of the two-letter motif within the loaded sample**, not genomic coordinates or inferred exon boundaries. This version does not inspect the reverse complement, pair introns, identify noncanonical sites, predict variant effects or establish cryptic-site activity.

Energy (joules) = assumed active power (watts) × illustrative runtime (seconds). Carbon uses an editable hypothetical grid factor. This prototype does not measure laptop energy, cloud costs, or energy savings on edge hardware.

The algorithm page compares an operation model of `O(n × w)` against `O(n + k × w)`, where n is sequence length, w is context width, and k is the number of raw motif candidates. With fixed w, both are O(n); motif filtering reduces detailed work while restricting coverage to canonical sites.

## Data handling

Sequences are held in browser memory for the current session. The application does not upload them or write them into browser storage. Downloads are generated locally. Reloading resets the workspace. Fonts use system fallbacks so the application can run without a font service.

## Developer commands

```powershell
npm test
npm run build
npm run preview
```

The analysis utilities are in `src/lib/analysis.js`; synthetic fixtures are in `src/data.js`. A later Python prediction service can replace the fixtures with model inference and measured runtime, keeping the React interface. See [PROJECT_HANDOVER.md](PROJECT_HANDOVER.md) for the verified current state, detailed completion plan, and a continuation prompt for a new chat.

Biology references: [NHGRI intron explanation](https://www.genome.gov/genetics-glossary/Intron) and [Illumina SpliceAI](https://github.com/Illumina/SpliceAI).
