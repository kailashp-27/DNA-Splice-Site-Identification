# EcoSplice models and algorithms

Implemented and verified: 7 October 2026. This is Part 2 of the local application. Predictions currently run through Python and the command line; the React pages still use their disclosed prototype fixtures until service integration.

## Run real predictions

After installing the runtime dependencies once, these commands use local files only. They load saved coefficients and never download data or train a model:

```powershell
python -m pip install -r backend/requirements.txt
python scripts/analyze_sequence.py --input data/demo/REAL-003.fasta --method adaptive --output results/my-analysis.json
```

Methods are `exhaustive`, `filtered` and `adaptive`. Run commands from the project root. Input supports one FASTA record or raw DNA, with the input/coordinate rules in [DATASET_AND_COORDINATES.md](DATASET_AND_COORDINATES.md). Output contains all canonical candidates, unavailable-score reasons, final scores/scorers/routes, per-scorer thresholds, model and dataset identity, input hash, computation timings and work counts. An arbitrary input file has no known labels and receives no invented accuracy result.

## What the models learn

The fixed dataset has 93,231 training, 20,153 validation and 21,219 test windows from isolated genomic groups. Coefficients are fit on training only. Thresholds and routing are selected on validation only and saved before test scores are computed. The original frozen dataset is unchanged.

Both classifiers are small multinomial logistic regressions with classes `non_site`, `donor` and `acceptor`. At each position, an A/C/G/T letter activates one of four indicators. The detailed model also activates one of sixteen adjacent-letter indicators at each pair of neighbouring positions. This lets it learn local combinations without a neural network or GPU.

| Scorer | DNA actually used | Features | Active feature terms per window |
| --- | --- | ---: | ---: |
| Preliminary | 10 bases + motif + 10 bases | 88 single-base indicators | 22 |
| Detailed | 50 bases + motif + 50 bases | 408 single-base and 1,616 adjacent-pair indicators | 203 |

Both use the same full 102-base eligibility contract, even though the preliminary scorer reads the central 22 bases. All windows must exist and contain only A/C/G/T. GT/AG candidates at sequence ends or with N in their full context retain their position but receive no score.

The detailed candidate improved validation macro F1 from **0.6937** for the short-window reference to **0.7695**, so it was retained. Training uses L2 regularisation (`C=1`), LBFGS, maximum 400 iterations, tolerance `1e-5`, fixed seed 20261006 and one numerical-library thread. The saved fits converged in 187 preliminary and 151 detailed iterations.

Inference sums the active coefficients and applies softmax, matching sklearn's exported predictions within `1e-12`. Saved `.npz` arrays load with `allow_pickle=False`, and SHA-256 checks verify them before use. The saved bundle is approximately 52 KB. Runtime requires only NumPy; sklearn and SciPy are development-time training dependencies.

Sources: [scikit-learn logistic regression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html), [NumPy array loading](https://numpy.org/doc/stable/reference/generated/numpy.load.html).

## Thresholds and real routing

The output is a **model score**, not a calibrated biological probability. Its magnitude reflects the sampled training class balance and model fit. Scores from the two scorers must retain their scorer identity and decision threshold.

Validation selects the threshold maximising canonical-candidate F1 on a fixed 0.01–0.99 grid, breaking ties by precision and then higher threshold:

| Type | Preliminary decision threshold | Detailed decision threshold | Preliminary fast-negative cutoff | Preliminary fast-positive cutoff |
| --- | ---: | ---: | ---: | ---: |
| Donor | 0.36 | 0.41 | 0.18 | 0.52 |
| Acceptor | 0.31 | 0.44 | 0.0775 | 0.655 |

For example, a donor with preliminary score 0.10 takes the fast negative route; a donor with preliminary score 0.70 takes the fast positive route. A donor at 0.40 is uncertain and is scored by the detailed model. Fast cases never call the detailed scorer. The saved final score and threshold always come from the scorer that actually made the decision.

Routing searches a predefined grid on validation, maximising avoided detailed evaluations while requiring per-type F1 loss at most 0.005 and recall loss at most 0.01 against detailed scoring on validation. These are selection constraints, not promised test-set guarantees. Offline policy selection computes both models to assess choices; the operational algorithm computes detailed scores only for uncertain candidates.

This routing policy applies to the saved thresholds. A future user-defined prediction threshold requires a new validated policy or disabling the adaptive shortcut; changing a display filter must not silently change the saved biological decision rule.

## Independent test results

These metrics concern canonical candidates in the sampled chromosome 22 test split, not every human splice site. There are 900 donor positives among 7,497 GT candidates and 918 acceptor positives among 7,523 AG candidates.

| Method/scorer | Donor precision | Donor recall | Donor F1 | Acceptor precision | Acceptor recall | Acceptor F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Motif-only reference | 0.120 | 1.000 | 0.214 | 0.122 | 1.000 | 0.218 |
| Preliminary alone | 0.735 | 0.764 | 0.749 | 0.578 | 0.647 | 0.610 |
| Detailed / exhaustive / filtered | 0.806 | 0.791 | 0.799 | 0.742 | 0.694 | 0.717 |
| Adaptive | 0.785 | 0.787 | 0.786 | 0.740 | 0.708 | 0.724 |

Detailed donor confusion counts: TP 712, FP 171, FN 188, TN 6,426. Detailed acceptor counts: TP 637, FP 221, FN 281, TN 6,384. The JSON report also contains all sampled-position metrics, preliminary/adaptive matrices, class support, validation/test threshold curves and calibration bins.

Adaptive routing used **2,888 detailed evaluations instead of 15,020**, avoiding **80.77%** of detailed work among the sampled canonical test candidates. Preliminary evaluations are additional work and are reported separately. Donor F1 fell by 0.0129 on test, more than its allowed validation drop; acceptor F1 rose by 0.0065. These outcomes are reported unchanged, with no tuning from test or demo predictions.

Descriptive detailed-score Brier scores on test candidates are 0.0367 for donors and 0.0496 for acceptors. Reliability bins are saved, but neither these numbers nor softmax establishes calibrated genome-wide probabilities. No calibration transform was fit. See [probability calibration guidance](https://scikit-learn.org/stable/modules/calibration.html).

Four complete cropped held-out demo regions are evaluated separately. Their pipeline evaluation includes unscoreable annotated edge sites as false negatives. The 21,219-window evaluation domain excludes incomplete/N-containing and noncanonical positive windows as specified by the frozen dataset. This distinction prevents hiding boundary coverage losses.

## The three algorithms

### Exhaustive baseline

```text
validate input; identify canonical motifs for the common output list
for every possible two-base start position:
    check and extract its full context
    if context is eligible, add it to a bounded detailed-model batch
    evaluate each batch with the detailed scorer
    retain scores only at GT donor / AG acceptor candidates
apply the detailed threshold for the candidate type
retain unscoreable motifs with their reason
```

Ordinary positions really are evaluated. A motif-free long input still performs exhaustive detailed scoring; there is no early exit that disguises the baseline as filtering.

### Candidate filtering

```text
validate input; scan once for GT and AG
for each canonical candidate:
    check and extract its full context
    if eligible, add it to a bounded detailed-model batch
evaluate each batch using the SAME detailed scorer and thresholds
retain unscoreable motifs with their reason
```

This changes which positions receive expensive scoring, not the shared canonical predictions. Tests verify candidate/decision/eligibility agreement and numerical score differences at most `1e-12` with different batch sizes, real demos and maximum-length stress inputs.

### Adaptive processing

```text
validate input; scan once for GT and AG
for each eligible candidate batch:
    score central 22-base contexts with the preliminary model
    accept decisive low/high preliminary decisions
    collect only uncertain contexts into a detailed batch
    score that smaller batch with the detailed model
    record the actual final scorer, score, threshold and route
retain unscoreable motifs with their reason
```

Tests instrument the detailed scorer: an all-fast policy makes zero detailed calls; mixed routing calls it exactly for counted pending contexts; an all-uncertain policy reproduces filtered scores. Offline adaptive evaluation decisions also match operational predictions.

## Work and complexity

Let `n` be input length, `k` canonical motifs, `e` eligible contexts over all positions, `q` eligible canonical contexts, `m` uncertain canonical contexts, `w=102`, preliminary width `l=22`, batch size `B=512`, and class count `c=3`.

| Method | Detailed evaluations | Preliminary evaluations | Work with variable context width |
| --- | ---: | ---: | --- |
| Exhaustive | e | 0 | O(n*w + e*c*w) |
| Filtered | q | 0 | O(n + k*w + q*c*w) |
| Adaptive | m | q | O(n + k*w + q*c*l + m*c*w) |

Context checking copies/checks up to w characters; coefficient summation has O(c*w) terms including adjacent pairs. With fixed windows/models/classes, all three methods remain **O(n)** in the worst case. The optimisation is avoiding work, not changing linear into a different asymptotic complexity. There is no unnecessary heap, fake delay or post-hoc route label.

Additional memory is O(k + B*c*w), plus fixed model coefficients: candidate outputs are stored, but model windows are streamed in bounded batches. `peak_batch_windows` is a verified operation counter, not a measured RAM statistic. Work reports also separate scanned positions, contexts considered, canonical/eligible/unscoreable candidates, preliminary/detailed evaluations and final routes.

## Measured local computation

Five fresh computations per method/input, model loaded beforehand, one excluded warm-up per method, shuffled method order, identical batch size. The report saves every stage timing, raw total, median, min/max, IQR, input hash, hardware and source/model hashes. Inference timing includes feature encoding and coefficient summation; total includes input validation, scan, contexts and candidate-result construction. Network/UI latency and JSON file writing are outside the computation timer.

Measured on Windows 11, AMD64 Family 25 Model 68 Stepping 1, 16 logical CPUs, Python 3.12.10 / NumPy 2.2.6:

| Input | Bases | Exhaustive median ms | Filtered median ms | Adaptive median ms |
| --- | ---: | ---: | ---: | ---: |
| TBC1D22A, real held-out crop | 1,484 | 11.092 | 2.135 | 1.275 |
| NUP50, real held-out crop | 1,624 | 11.927 | 1.955 | 1.352 |
| ARVCF, real held-out crop | 2,402 | 17.837 | 3.189 | 2.143 |
| SF3A1, real held-out crop | 2,402 | 18.224 | 3.322 | 2.046 |
| Motif-free synthetic stress | 100,000 | 704.363 | 11.339 | 11.131 |
| Motif-rich synthetic stress | 100,000 | 801.624 | 450.336 | 204.600 |

These are this machine's observations, not guaranteed performance or energy savings. Tiny motif-free filtered/adaptive differences are within ordinary timing variation. The motif-rich stress has 49,950 eligible candidates and 50 unscoreable edge motifs; baseline performs 99,899 detailed evaluations. Synthetic stress inputs have no biological accuracy claim. The Python engine passes 100,000-base checks with bounded batching; the complete UI path still needs Part 4 verification.

No laptop power was measured. Estimated energy from these runtimes and explicit power assumptions remains Part 4, alongside broader length/density experiments and interface integration.

## Reproduce and inspect

```powershell
python -m pip install -r scripts/models/requirements.txt
python scripts/models/train_models.py
python scripts/models/verify_algorithms.py
python -m unittest discover -s backend/tests -p "test_*.py" -v
```

Training is development work only. It produces `models/ecosplice-v1/` and `results/model-evaluation.json`. Independent retraining into a separate QA folder produced byte-identical preliminary/detailed `.npz` files and the model manifest. Evidence is in `results/model-reproducibility.json`.

| Artifact | Purpose |
| --- | --- |
| `models/ecosplice-v1/manifest.json` | Model/scorer IDs, frozen thresholds/routing, encoding, dataset/code hashes and versions |
| `models/ecosplice-v1/*.npz` | Small portable saved coefficient arrays |
| `results/model-evaluation.json` | Genuine validation/test support, metrics, matrices, calibration and threshold curves |
| `results/algorithm-verification.json` | Real timings/counters, output parity, full demo-region quality and maximum-size checks |
| `results/demo-predictions.json` | Genuine filtered and adaptive candidate results for held-out demos |
| `results/model-reproducibility.json` | Independent retraining identity check |

At Part 2 completion, 26 Python tests and seven JavaScript tests passed. The model is `ecosplice-v1-64223ad070d6`. Part 3 subsequently adds the local service and SQLite history, documented in [LOCAL_SERVICE.md](LOCAL_SERVICE.md), with 40 Python tests in total. The scientific model/evaluation/benchmark artifacts remain unchanged.
