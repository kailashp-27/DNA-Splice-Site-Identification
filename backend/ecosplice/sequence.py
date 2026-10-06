"""Shared DNA/coordinate contract. Internal coordinates are zero-based half-open."""
from dataclasses import dataclass
import re

FLANK = 50
CONTEXT_WIDTH = 2 * FLANK + 2
MAX_SEQUENCE_LENGTH = 100_000


def reverse_complement(sequence):
    return sequence.translate(str.maketrans("ACGTNacgtn", "TGCANtgcan"))[::-1]


def parse_sequence(raw):
    lines = [line.strip() for line in raw.strip().splitlines() if line.strip()]
    headers = [i for i, line in enumerate(lines) if line.startswith(">")]
    if len(headers) > 1:
        raise ValueError("Upload one FASTA record at a time.")
    if headers and headers[0] != 0:
        raise ValueError("The FASTA header must appear before the DNA sequence.")
    sequence = re.sub(r"\s+", "", "".join(line for line in lines if not line.startswith(">"))).upper()
    if not sequence:
        raise ValueError("Add a DNA sequence before continuing.")
    if len(sequence) > MAX_SEQUENCE_LENGTH:
        raise ValueError("Sequences may contain at most 100,000 bases.")
    invalid = sorted(set(sequence) - set("ACGTN"))
    if invalid:
        raise ValueError("Unsupported DNA symbols: " + ", ".join(invalid))
    if sum(sequence.count(base) for base in "ACGT") < 20:
        raise ValueError("Provide at least 20 known A/C/G/T bases.")
    return {"name": lines[0][1:].split()[0] if headers and lines[0][1:].strip() else "Custom sequence", "sequence": sequence}


def context_at(sequence, motif_start0, flank=FLANK):
    """Return a full called window or None. Do not invent bases at sequence ends."""
    start, end = motif_start0 - flank, motif_start0 + 2 + flank
    if start < 0 or end > len(sequence):
        return None
    context = sequence[start:end]
    return context if set(context) <= set("ACGT") else None


def local_motif_start(genomic_start0, region_start0, region_end0, strand):
    """genomic_start0 is the lower coordinate of the two-base genomic interval."""
    if strand not in ("+", "-"):
        raise ValueError("Strand must be + or -.")
    if not region_start0 <= genomic_start0 < region_end0 - 1:
        raise ValueError("Motif must be inside the region.")
    return genomic_start0 - region_start0 if strand == "+" else region_end0 - genomic_start0 - 2


def genomic_motif_start(local_start0, region_start0, region_end0, strand):
    if strand not in ("+", "-"):
        raise ValueError("Strand must be + or -.")
    if not 0 <= local_start0 < region_end0 - region_start0 - 1:
        raise ValueError("Motif must be inside the region.")
    return region_start0 + local_start0 if strand == "+" else region_end0 - local_start0 - 2


@dataclass(frozen=True)
class Boundary:
    motif_start0: int
    strand: str
    kind: str
    gene_id: str
    transcript_id: str


def transcript_boundaries(exons, strand, gene_id, transcript_id):
    """Exons are genomic [start,end). Deduplicate exon intervals before adjacency."""
    if strand not in ("+", "-"):
        raise ValueError("Strand must be + or -.")
    ordered = sorted(set(exons))
    result = []
    for left, right in zip(ordered, ordered[1:]):
        intron_start, intron_end = left[1], right[0]
        if intron_end - intron_start < 2:
            continue
        donor, acceptor = (intron_start, intron_end - 2) if strand == "+" else (intron_end - 2, intron_start)
        result.extend([Boundary(donor, strand, "donor", gene_id, transcript_id), Boundary(acceptor, strand, "acceptor", gene_id, transcript_id)])
    return result
