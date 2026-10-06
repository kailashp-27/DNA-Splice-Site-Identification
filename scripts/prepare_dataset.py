"""Prepare a frozen chr22 dataset with stdlib only; reruns work offline."""
from pathlib import Path
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import random
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ecosplice.sequence import (FLANK, CONTEXT_WIDTH, context_at, reverse_complement,
                                local_motif_start, genomic_motif_start, transcript_boundaries)

SEED = 20261006


def digest_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rank(value):
    return hashlib.sha256(f"{SEED}:{value}".encode()).hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_annotation(path):
    genes, transcripts = {}, {}
    with gzip.open(path, "rt", encoding="utf-8") as source:
        for line in source:
            if not line.startswith("chr22\t"):
                continue
            fields = line.rstrip().split("\t")
            if fields[2] not in ("gene", "exon"):
                continue
            attrs = dict(re.findall(r'(\w+) "([^\"]*)"', fields[8]))
            start, end, strand = int(fields[3]) - 1, int(fields[4]), fields[6]
            if fields[2] == "gene":
                genes[attrs["gene_id"]] = {"id": attrs["gene_id"], "name": attrs.get("gene_name", attrs["gene_id"]), "type": attrs["gene_type"], "start0": start, "end0": end, "strand": strand}
            else:
                transcript = transcripts.setdefault(attrs["transcript_id"], {"gene_id": attrs["gene_id"], "strand": strand, "exons": []})
                if transcript["strand"] != strand or transcript["gene_id"] != attrs["gene_id"]:
                    raise ValueError("Inconsistent transcript annotation.")
                transcript["exons"].append((start, end))
    return genes, transcripts


def read_genome(path):
    with gzip.open(path, "rt", encoding="ascii") as source:
        if next(source).strip() != ">chr22":
            raise ValueError("Expected chr22 FASTA.")
        chunks = []
        for line in source:
            if line.startswith(">"):
                raise ValueError("Expected one chromosome in the reference FASTA.")
            chunks.append(line.strip())
    genome = "".join(chunks).upper()
    if len(genome) != 50_818_468 or set(genome) - set("ACGTN"):
        raise ValueError("Reference does not match the GRCh38 chromosome 22 length/alphabet.")
    return genome


def assign_groups(genes):
    """Connected components of expanded genomic gene spans, regardless of strand."""
    groups, group_end = [], -1
    for gene in sorted(genes, key=lambda g: (g["region_start0"], g["region_end0"], g["id"])):
        if not groups or gene["region_start0"] >= group_end:
            groups.append([])
            group_end = gene["region_end0"]
        else:
            group_end = max(group_end, gene["region_end0"])
        groups[-1].append(gene)
    ordered = sorted(groups, key=lambda group: rank(",".join(sorted(g["id"] for g in group))))
    for index, group in enumerate(ordered):
        fraction = index / len(ordered)
        split = "train" if fraction < .70 else "validation" if fraction < .85 else "test"
        group_id = "G-" + hashlib.sha256(",".join(sorted(g["id"] for g in group)).encode()).hexdigest()[:12]
        for gene in group:
            gene.update(group_id=group_id, split=split)
    return groups


def audit_rows(rows):
    seen, groups, intervals = {}, {}, []
    for row in rows:
        key = min(row["context"], reverse_complement(row["context"]))
        if key in seen:
            raise ValueError("Duplicate context survived deduplication.")
        seen[key] = row["split"]
        if groups.setdefault(row["group_id"], row["split"]) != row["split"]:
            raise ValueError("Genomic group leaks across splits.")
        offset = row["genomic_motif_start0"]
        start, end = offset - FLANK, offset + 2 + FLANK
        intervals.append((start, end, row["split"]))
        motif = row["context"][FLANK:FLANK + 2]
        if len(row["context"]) != CONTEXT_WIDTH or set(row["context"]) - set("ACGT"):
            raise ValueError("Invalid model context.")
        if row["label"] in ("donor", "acceptor") and motif != {"donor": "GT", "acceptor": "AG"}[row["label"]]:
            raise ValueError("Positive boundary motif is misaligned.")
    furthest = {}
    for start, end, split in sorted(intervals):
        if any(limit > start for other, limit in furthest.items() if other != split):
            raise ValueError("Genomic windows overlap across splits.")
        furthest[split] = max(furthest.get(split, -1), end)
    for split in ("train", "validation", "test"):
        labels = {r["label"] for r in rows if r["split"] == split}
        if labels != {"donor", "acceptor", "non_site"}:
            raise ValueError(f"Missing class in {split}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-genes", type=int, default=400)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "processed")
    args = parser.parse_args()
    if args.max_genes < 20:
        parser.error("Use at least 20 genes for three partitions.")
    raw = ROOT / "data" / "raw"
    annotation = raw / "gencode.v49.annotation.gtf.gz"
    fasta = raw / "chr22.fa.gz"
    sources = json.loads((raw / "sources.json").read_text())
    for record in sources["files"]:
        if digest_file(raw / record["file"]) != record["sha256"]:
            raise ValueError("Raw input checksum differs from recorded source.")
    print("Reading chr22 sequence and GENCODE exons...", flush=True)
    genome = read_genome(fasta)
    genes, transcripts = read_annotation(annotation)
    # All annotated gene/transcript types protect the negative pool, not only the selected training genes.
    annotated, gene_boundaries = defaultdict(set), defaultdict(set)
    for tid, tx in sorted(transcripts.items()):
        for b in transcript_boundaries(tx["exons"], tx["strand"], tx["gene_id"], tid):
            annotated[(b.strand, b.motif_start0)].add(b.kind)
            gene_boundaries[b.gene_id].add((b.motif_start0, b.kind))
    selected = sorted((g for g in genes.values() if g["type"] == "protein_coding" and gene_boundaries[g["id"]]), key=lambda g: rank(g["id"]))[:args.max_genes]
    for g in selected:
        g.update(region_start0=max(0, g["start0"] - FLANK), region_end0=min(len(genome), g["end0"] + FLANK))
    groups = assign_groups(selected)
    rows, excluded, negative_pool_counts = [], Counter(), Counter()
    print(f"Extracting contexts from {len(selected)} genes in {len(groups)} groups...", flush=True)
    for gene in sorted(selected, key=lambda g: g["id"]):
        lo, hi, strand = gene["region_start0"], gene["region_end0"], gene["strand"]
        sequence = genome[lo:hi]
        if strand == "-":
            sequence = reverse_complement(sequence)
        positives = []

        def make_row(index, label, kind):
            context = context_at(sequence, index)
            if context is None:
                excluded["edge_window" if index < FLANK or index + 2 + FLANK > len(sequence) else "unknown_window"] += 1
                return None
            pos = genomic_motif_start(index, lo, hi, strand)
            identity = f"chr22:{strand}:{pos}:{label}"
            return {"id": hashlib.sha256(identity.encode()).hexdigest()[:20], "chromosome": "chr22", "strand": strand, "genomic_motif_start0": pos, "genomic_motif_end0": pos + 2, "gene_id": gene["id"], "gene_name": gene["name"], "group_id": gene["group_id"], "split": gene["split"], "label": label, "negative_kind": kind, "context": context, "local_position1": index + 1}

        for pos, label in sorted(gene_boundaries[gene["id"]]):
            index = local_motif_start(pos, lo, hi, strand)
            if sequence[index:index + 2] != {"donor": "GT", "acceptor": "AG"}[label]:
                excluded["noncanonical_boundary"] += 1
                continue
            row = make_row(index, label, None)
            if row:
                positives.append(row)
        rows.extend(positives)
        # Reservoir sampling bounds memory while scanning each gene once. Selection ignores split/model results.
        limit = min(200, max(20, 4 * len(positives)))
        pools, counts = {k: [] for k in ("donor_motif", "acceptor_motif", "ordinary")}, Counter()
        rng = random.Random(int(rank(gene["id"])[:16], 16))
        for index in range(FLANK, len(sequence) - FLANK - 1):
            pos = genomic_motif_start(index, lo, hi, strand)
            if (strand, pos) in annotated:
                continue
            motif = sequence[index:index + 2]
            kind = "donor_motif" if motif == "GT" else "acceptor_motif" if motif == "AG" else "ordinary"
            counts[kind] += 1
            cap = 100 if kind == "ordinary" else limit
            pool = pools[kind]
            if len(pool) < cap:
                pool.append(index)
            else:
                slot = rng.randrange(counts[kind])
                if slot < cap:
                    pool[slot] = index
        for kind, pool in pools.items():
            negative_pool_counts[kind] += counts[kind]
            for index in sorted(pool):
                row = make_row(index, "non_site", kind)
                if row:
                    rows.append(row)
    # Remove repeated sequence windows including reverse complements. Conflicting labels are excluded entirely.
    by_context = defaultdict(list)
    for row in rows:
        by_context[min(row["context"], reverse_complement(row["context"]))].append(row)
    unique = []
    for duplicates in by_context.values():
        if len({row["label"] for row in duplicates}) > 1:
            excluded["conflicting_context_rows"] += len(duplicates)
        else:
            unique.append(sorted(duplicates, key=lambda r: (r["gene_id"], r["genomic_motif_start0"], r["label"]))[0])
            excluded["duplicate_context_rows"] += len(duplicates) - 1
    rows = sorted(unique, key=lambda r: (r["split"], r["gene_id"], r["genomic_motif_start0"], r["label"]))
    audit_rows(rows)
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    with (out / "windows.jsonl").open("w", encoding="utf-8", newline="\n") as output:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True) + "\n")
    membership = [{k: g[k] for k in ("id", "name", "strand", "region_start0", "region_end0", "group_id", "split")} for g in sorted(selected, key=lambda g: g["id"])]
    write_json(out / "split_membership.json", membership)
    demos = []
    for strand in ("+", "-"):
        choices = [r for r in rows if r["split"] == "test" and r["strand"] == strand and r["label"] == "donor"]
        used = set()
        for row in choices:
            if row["gene_id"] in used:
                continue
            used.add(row["gene_id"])
            center = row["genomic_motif_start0"]
            lo, hi = max(0, center - 1200), min(len(genome), center + 1202)
            # Keep demo DNA wholly inside its held-out gene's assigned region.
            gene = genes[row["gene_id"]]
            lo, hi = max(lo, gene["region_start0"]), min(hi, gene["region_end0"])
            sequence = genome[lo:hi]
            if strand == "-":
                sequence = reverse_complement(sequence)
            labels = []
            for (s, pos), kinds in sorted(annotated.items()):
                if s == strand and lo <= pos < hi - 1:
                    index = local_motif_start(pos, lo, hi, strand)
                    for kind in sorted(kinds):
                        if sequence[index:index + 2] == {"donor": "GT", "acceptor": "AG"}[kind]:
                            labels.append({"position1": index + 1, "type": kind, "genomic_motif_start0": pos, "scorable": context_at(sequence, index) is not None})
            demos.append({"id": f"REAL-{len(demos) + 1:03}", "name": gene["name"], "gene_id": row["gene_id"], "group_id": row["group_id"], "split": "test", "source": "GENCODE v49 / GRCh38 chr22", "genomic_region": {"chromosome": "chr22", "start0": lo, "end0": hi, "strand": strand}, "sequence": sequence, "annotations": sorted(labels, key=lambda b: b["position1"]), "annotation_scope": "Canonical boundaries in all GENCODE v49 chr22 transcripts on the analysed strand; absent labels mean unannotated, not proven inactive."})
            if len(used) == 2:
                break
    write_json(out / "demo_samples.json", demos)
    demo_dir = ROOT / "data" / "demo"
    demo_dir.mkdir(exist_ok=True)
    for demo in demos:
        sequence = demo["sequence"]
        text = f'>{demo["id"]} {demo["name"]} GENCODE_v49_GRCh38 oriented_strand={demo["genomic_region"]["strand"]}\n'
        text += "\n".join(sequence[i:i + 80] for i in range(0, len(sequence), 80)) + "\n"
        (demo_dir / (demo["id"] + ".fasta")).write_text(text, encoding="ascii")
    manifest = {"schema_version": 1, "dataset_id": "gencode49-grch38-chr22-v1", "seed": SEED, "assembly": "GRCh38 primary chromosome 22 (NC_000022.11); GENCODE v49 release GRCh38.p14", "sources": sources, "context": {"flank": FLANK, "width": CONTEXT_WIDTH, "motif_offset0": FLANK, "edge_policy": "Exclude incomplete windows", "unknown_policy": "Exclude windows containing N"}, "selection": {"gene_type": "protein_coding", "max_genes": args.max_genes, "genes": len(selected), "negative_sampling": "Per gene: min(200,max(20,4*eligible positives)) of each GT/AG kind, plus 100 ordinary positions; reservoirs sampled before window QC", "positive_labels": "Union of canonical exon-adjacency boundaries across transcripts", "negative_exclusion": "All chr22 GENCODE transcript boundaries on the analysed strand, including noncanonical boundaries"}, "split_policy": "70/15/15% of deterministically shuffled connected genomic gene-span groups; counts are not balanced by label", "groups": len(groups), "counts": {s: dict(Counter(r["label"] for r in rows if r["split"] == s)) for s in ("train", "validation", "test")}, "negative_counts": {s: dict(Counter(r["negative_kind"] for r in rows if r["split"] == s and r["label"] == "non_site")) for s in ("train", "validation", "test")}, "strand_counts": dict(Counter(r["strand"] for r in rows)), "excluded": dict(excluded), "audit": {"cross_split_genomic_overlap": 0, "duplicate_contexts_including_reverse_complements": 0, "misaligned_positive_motifs": 0, "all_classes_present_in_every_split": True}, "files": {name: digest_file(out / name) for name in ("windows.jsonl", "split_membership.json", "demo_samples.json")}, "limits": ["One chromosome and sampled negatives; not a genome-wide or clinical validation dataset.", "Overlapping intervals and duplicate windows are controlled; distant homologous genes may remain related.", "Sampled class balance differs from natural prevalence. Scores must not be called calibrated probabilities without evaluation.", "Noncanonical boundaries are excluded from positive scope; no intron pairing or variant effects.", "Demo examples belong to test groups. Do not tune models after inspecting their predictions."]}
    manifest["negative_pool_counts_before_sampling"] = dict(negative_pool_counts)
    manifest["preparation_code_sha256"] = {
        "scripts/prepare_dataset.py": digest_file(Path(__file__)),
        "ecosplice/sequence.py": digest_file(ROOT / "ecosplice" / "sequence.py"),
    }
    manifest["dataset_fingerprint"] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    write_json(out / "manifest.json", manifest)
    print(json.dumps({"windows": len(rows), "counts": manifest["counts"], "excluded": manifest["excluded"], "demos": len(demos)}, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(f"Dataset preparation failed: {error}") from error
