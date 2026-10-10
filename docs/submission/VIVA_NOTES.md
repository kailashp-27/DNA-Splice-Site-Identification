# EcoSplice viva notes

## What problem does this application solve

It identifies possible canonical splice boundaries in supplied DNA. Splicing removes introns from an RNA transcript and joins exons. We analyse DNA sequence patterns corresponding to those RNA boundaries. The application does not edit DNA, pair complete introns or determine tissue-specific splicing.

## What are donor and acceptor sites

In the analysed direction, canonical introns usually begin with GT in DNA and end with AG. A donor is the beginning boundary and an acceptor is the ending boundary. GT/AG also occur at ordinary positions, so finding a motif alone does not establish a splice site. Noncanonical sites lie outside this version's output scope.

## How does the model make a prediction

The detailed model reads a 102-base context: 50 bases, the two-base motif, and 50 bases. It uses position-specific single-base and adjacent-pair features with trained logistic regression coefficients. The preliminary model uses the central 22 bases and single-base features. Numeric saved coefficients run with NumPy. Opening the app loads the model rather than training it.

## Is a score of 0.9 a 90 percent biological probability

No. It is a softmax classifier score under the sampled training class balance. Calibration and genomic prevalence have not established that probability interpretation. We call it a model score. The final scorer and its applicable threshold are recorded for every prediction.

## Why use a small model

It is reproducible, interpretable enough to explain the features, and comfortable on a laptop CPU. More complex models may improve accuracy but require additional evidence, data and evaluation. A small model also makes actual algorithm work counts easy to compare.

## Where did the labelled data come from

GENCODE human release 49 annotations and UCSC GRCh38 primary chromosome 22 DNA. The frozen dataset includes 400 genes in 304 connected genomic groups and 134,603 unique context windows. Annotated exon adjacency determines positives. Negative examples avoid annotated boundaries but remain unannotated examples rather than proven inactive sites.

## How was leakage controlled

Expanded overlapping gene regions form connected groups. Whole groups stay within one partition. Exact duplicate contexts and reverse-complement equivalents are removed globally. The audit checks cross-split overlap and duplicates. Distant homologous genes may still share biological patterns, which is a limitation of this study.

## What are the partitions used for

Training fits coefficients. Validation selects thresholds and the adaptive routing policy. Test reports final performance. Test counts are 900 donor positives, 918 acceptor positives and 19,401 non-sites. Canonical-candidate metrics exclude ordinary non-motif positions from their respective binary domains. Cropped demo-region evaluation separately includes unscoreable annotated edges as missed sites.

## How do the three methods differ

Exhaustive runs the detailed model at every eligible two-base start, then retains canonical outputs. Candidate filtering scans GT/AG first and runs exactly the same detailed model only there. Adaptive first uses the cheaper model at eligible candidates and sends uncertain ones to the detailed model. The code counts actual evaluations and routes, not labels assigned after expensive work.

## What is the time complexity

Let n be DNA length, k the canonical motifs, w the context width, q the eligible canonical contexts, and m the uncertain contexts. Exhaustive uses about n eligible detailed evaluations, filtered uses q, and adaptive uses q preliminary plus m detailed evaluations. With fixed width and model, each method is O(n) in the worst case. Filtering improves the constant amount of work rather than claiming a new asymptotic class.

## What is the space complexity

O(k + Bcw) extra working/output memory for k candidate outputs, batch size B, c classes and context width w, plus the fixed model. The input itself occupies O(n). Batches default to 512. Peak batch windows are an operation counter, not a measured RAM figure.

## Do exhaustive and filtered predictions agree

Yes, their canonical candidates, eligibility and decisions agree, with numerical scores within 1e-12. They use the same context, detailed coefficients and thresholds. Adaptive may change decisions because its final scorer can be preliminary.

## What accuracy did the finished model achieve

Detailed held-out canonical-candidate F1 is 0.7987 for donors and 0.7173 for acceptors. Adaptive is 0.7858 and 0.7238. It avoids 12,132 of 15,020 detailed canonical test evaluations, or 80.77 percent. Adaptive donor loss exceeded its validation selection tolerance on test, so we disclose that result without retuning on test.

## What do precision recall and F1 mean

Precision asks how many predicted positives match annotations: TP/(TP+FP). Recall asks how many annotated positives were found: TP/(TP+FN). F1 is their harmonic mean: 2TP/(2TP+FP+FN). TP/FP/FN/TN are true positives, false positives, false negatives and true negatives. High overall accuracy can hide poor splice detection when negatives dominate.

## How are benchmarks fair

All methods use identical DNA, batches, model settings and power assumptions. Models load before timing. Each method warms once outside measurement, then fresh repeated computations run in shuffled order. We show medians, min/max and IQR, and preserve raw stage timings. Serialization, network/UI time and database writes lie outside the computation timer. Hardware and hashes are saved.

## How is energy calculated

Estimated energy in joules = assumed watts × measured milliseconds / 1000. For example, 15 W × 0.2 s = 3 J. This is a visible assumption, not direct laptop power measurement. With identical assumed watts, estimated reduction follows runtime reduction. Real different hardware power requires actual measurement.

## What happens at edges or N bases

Input permits A/C/G/T/N and at least 20 called bases. Complete scored contexts contain A/C/G/T only. N or incomplete contexts remain candidates with no score and a reason. The app does not pad ends or replace unknown bases. A valid sequence shorter than 102 bases can therefore have no scored sites.

## What coordinate is displayed

One-based motif start in the supplied sequence. A GT at position 101 occupies 101 and 102, with the donor boundary immediately before 101. An AG at 199 occupies 199 and 200, with the acceptor boundary immediately after 200. Input orientation remains as supplied. The bundled minus-strand demonstrations are already reverse-complemented for their annotated direction.

## Can uploaded FASTA show accuracy

Ordinary FASTA contains no known answers, so it can show predictions only. Validate uses the independent frozen test evaluation. Selecting a bundled annotated sample explicitly supplies its labels. Uploading an identically named FASTA does not confer those labels.

## How are failures and history handled

React shows clear loading/errors and rejects stale responses after input changes. Python rejects invalid input, extra FASTA records, files over 1 MB and sequences above 100,000 bases. Completed scientific snapshots persist in SQLite and survive process restart. Rename changes the presentation name. Comparison attaches measurements without rewriting original predictions. CSV, JSON and print use the same stored snapshot and filter contract.

## What remains future work

Broader chromosome/species evaluation, independent homology grouping, calibrated probabilities, complete intron pairing, variant effects and cryptic sites. Quantization, Jetson/NPU acceleration, cloud offloading and federated learning are proposals only. This delivered application uses a local CPU with no remote inference.
