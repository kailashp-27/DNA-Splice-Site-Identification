# EcoSplice dataset and coordinate contract

## Scope

EcoSplice predicts possible canonical splice boundaries: GT donors and AG acceptors in DNA oriented 5' to 3' in the analysed direction. It does not pair boundaries into complete introns or decide which sequence to remove. The first dataset is a laptop-scale chromosome 22 subset, not a claim of genome-wide accuracy.

## Sources and use

- Annotation: [GENCODE human release 49](https://www.gencodegenes.org/human/release_49.html), comprehensive GTF, released for GRCh38.p14. Only primary chr22 records are used. All transcript types are read to avoid treating annotated boundaries outside selected training genes as negatives.
- DNA: [UCSC GRCh38/hg38 chromosome downloads](https://hgdownload.soe.ucsc.edu/goldenPath/hg38/chromosomes/), chr22.fa.gz. UCSC describes these files as freely available for public use. Repeats are lowercase in the original and are normalised to uppercase.
- Reference chromosome: [NC_000022.11](https://www.ncbi.nlm.nih.gov/nuccore/NC_000022.11), 50,818,468 bases. GRCh38.p14 annotation is used on the primary chromosome; patches and alternate contigs are excluded.
- GENCODE states its data is [open access](https://www.gencodegenes.org/pages/data_access.html). [EMBL-EBI terms](https://www.ebi.ac.uk/about/terms-of-use/) request scientific attribution and impose no additional data-use restrictions beyond the original owners' terms. Preserve these source credits with distributed samples and reports. No invented software license is assigned to these scientific sources.

`data/raw/sources.json` records exact download URLs, byte sizes and SHA-256 checksums. `data/processed/manifest.json` records source identity, preprocessing, sampling, class counts, exclusions, audit results and derived-file hashes. The release is frozen rather than following a changing “latest” URL. The download is development-time work, not app startup work.

## Positions and strand

GTF positions are one-based inclusive. Preparation converts each exon to `[start-1,end)` and sorts its genomic intervals. For consecutive exons `[a,b)` and `[c,d)`, the intervening intron is `[b,c)`:

| Strand | Donor genomic two-base interval | Acceptor genomic two-base interval |
| --- | --- | --- |
| + | `[b,b+2)` | `[c-2,c)` |
| - | `[c-2,c)` | `[b,b+2)` |

On the minus strand, the genomic letters at these intervals are reverse-complemented before checking GT/AG. Shared boundaries across transcript isoforms are deduplicated. Noncanonical annotations are counted and excluded from the positive scope; they are also protected from negative sampling.

For a genomic motif interval `[p,p+2)` inside region `[L,R)`, the oriented sequence's zero-based motif start is `p-L` on + and `R-p-2` on -. The displayed motif position is that index plus one. A GT at displayed position 101 occupies bases 101 and 102; the donor boundary is immediately before base 101. An AG at position 199 occupies bases 199 and 200; the acceptor boundary is immediately after base 200. The motif position and splice junction are distinct quantities.

Raw uploaded DNA has no known genomic origin or strand metadata. Its positions are sequence-local. The application does not automatically analyse both strands; users must provide the oriented sequence they wish to inspect.

## Context and input rules

The model contract is 102 bases: 50 before the motif, the two-base motif at offsets 50 and 51, and 50 after it. A candidate is scoreable only if this full window exists and contains A/C/G/T. Edge candidates and contexts containing N remain identifiable as motif candidates, but must receive no score and a reason when prediction is integrated. No edge padding or replacement of unknown bases is performed.

The shared Python input utility accepts raw DNA or one FASTA record, strips whitespace, uppercases bases, permits A/C/G/T/N, rejects other letters, caps input at 100,000 bases, and requires at least 20 known bases. Sequences shorter than 102 bases can pass input checks but have no scoreable contexts. A FASTA header must precede the sequence. The frontend's existing QC remains until authoritative backend integration in Part 3/4; it is not yet connected to these Python rules.

## Labels, negatives and sampling

The three labels are donor, acceptor and non_site. Positive boundaries are the union of exon-adjacency annotations across transcripts belonging to selected protein-coding genes. Gene selection is deterministic using seed 20261006, with up to 400 genes.

Negative examples include GT motifs, AG motifs and ordinary positions inside each selected gene region. Any boundary annotated on the analysed strand anywhere in the comprehensive chr22 annotation is excluded from negative sampling. A negative means “not annotated in this release”, not “experimentally proven inactive”. Opposite-strand annotations are a separate prediction domain.

Each gene supplies up to `min(200,max(20,4*eligible_positive_count))` negative examples of each motif type, and up to 100 ordinary negatives. Reservoir sampling bounds memory. The sampler runs before window quality filtering; N-containing sampled windows are counted and discarded. This balance deliberately differs from genomic prevalence. Later evaluation must report performance among canonical motifs separately from ordinary positions and include full held-out demo-region pipeline evaluation. A high accuracy dominated by easy ordinary negatives would be misleading.

## Isolation and reproducibility

Gene spans are expanded by 50 bases at both ends. Overlapping spans, including opposite-strand genes, are joined into connected components. Components are deterministically shuffled and partitioned approximately 70/15/15 by component count. These percentages do not promise exact class or gene balance.

Exact duplicate contexts, including reverse-complement equivalents, are removed globally before fitting anything. All contexts with conflicting labels are excluded. Every retained context has explicit gene, genomic interval, group and split identity. Preparation fails if any genomic windows overlap across partitions, any context is duplicated, any positive motif is misaligned, or any split lacks a label.

This controls identical and overlapping sequence leakage. It does not establish complete homology independence between distant gene families; future broader studies should additionally group homologues and test other chromosomes.

Fit models and encoders on train only. Select thresholds and routing rules on validation only. Keep test for final evaluation. Four demo FASTA files and their labelled JSON metadata are drawn from test genes on both strands. Their DNA is already oriented for upload. Do not tune the model after observing demo/test prediction quality.

## Outputs

- `windows.jsonl`: training/evaluation rows with DNA windows and labels.
- `split_membership.json`: complete selected-gene membership, expanded region and split.
- `manifest.json`: counts, source hashes, contract, sampling policy, exclusions and audit.
- `demo_samples.json`: oriented genomic DNA plus known canonical boundary positions and provenance.
- `data/demo/REAL-*.fasta`: offline files compatible with the current upload flow. Existing UI analysis of these files is motif scanning only until model integration.

## Commands

```powershell
python scripts/download_reference.py
python scripts/prepare_dataset.py
python -m unittest discover -s tests -p "test_*.py" -v
```

The data scripts require Python 3.12 and no third-party packages. To verify deterministic regeneration, prepare again into a different folder and compare the manifest's file hashes. Source caches are excluded from Git; derived data and demo files are intended release artifacts. No trained model or accuracy figure is supplied by this part.

## Frozen preparation results: 6 October 2026

400 protein-coding genes form 304 genomic groups. There are 134,603 retained unique contexts, occupying about 59 MB including metadata. No cross-split genomic overlap, duplicate context or positive motif-alignment failure survived the audit.

| Split | Donor | Acceptor | Non-site | Total |
| --- | ---: | ---: | ---: | ---: |
| Train | 3,654 | 3,811 | 85,766 | 93,231 |
| Validation | 858 | 821 | 18,474 | 20,153 |
| Test | 900 | 918 | 19,401 | 21,219 |

Preparation excluded 134 noncanonical boundary occurrences, 1,119 duplicate context rows and 12 context rows with conflicting labels. Selected windows had no unknown-base exclusions in this run; the exclusion policy remains enforced by code and tests.

The four held-out examples are TBC1D22A (1,484 bases, +), NUP50 (1,624 bases, +), ARVCF (2,402 bases, -) and SF3A1 (2,402 bases, -). Minus-strand FASTA exports already follow the analysed strand. The files contain respectively 2, 5, 7 and 5 annotated canonical boundaries; some near their crop edges are deliberately marked unscoreable in the metadata. These annotation counts are not prediction or accuracy results.

Ten Python tests and seven JavaScript tests passed. An independent offline regeneration matched the complete manifest and all recorded output hashes, as recorded in `data/processed/verification.json`. Dataset fingerprint: `a884895b613c8923e41e1830c2d475377071272848f2fb4c9f24335f936c5464`.
