"""Coordinate and leakage checks; tiny test DNA is not scientific evidence."""
from pathlib import Path
import json
import unittest

from ecosplice.sequence import (context_at, genomic_motif_start, local_motif_start,
                                parse_sequence, reverse_complement, transcript_boundaries)
from scripts.prepare_dataset import assign_groups, audit_rows

ROOT = Path(__file__).resolve().parents[1]


class CoordinateTests(unittest.TestCase):
    def test_plus_exon_adjacency_and_alignment(self):
        dna = "A" * 100 + "GT" + "C" * 96 + "AG" + "A" * 100
        boundaries = transcript_boundaries([(0, 100), (200, 300)], "+", "gene", "tx")
        self.assertEqual([(b.kind, b.motif_start0) for b in boundaries], [("donor", 100), ("acceptor", 198)])
        for b in boundaries:
            self.assertEqual(context_at(dna, b.motif_start0)[50:52], {"donor": "GT", "acceptor": "AG"}[b.kind])

    def test_minus_strand_and_roundtrip(self):
        oriented = "A" * 100 + "GT" + "C" * 96 + "AG" + "A" * 100
        genomic = reverse_complement(oriented)
        boundaries = transcript_boundaries([(0, 100), (200, 300)], "-", "gene", "tx")
        self.assertEqual([(b.kind, b.motif_start0) for b in boundaries], [("donor", 198), ("acceptor", 100)])
        for b in boundaries:
            local = local_motif_start(b.motif_start0, 0, 300, "-")
            self.assertEqual(genomic_motif_start(local, 0, 300, "-"), b.motif_start0)
            self.assertEqual(reverse_complement(genomic)[local:local + 2], {"donor": "GT", "acceptor": "AG"}[b.kind])
        self.assertEqual(local_motif_start(1198, 1000, 1300, "-"), 100)
        self.assertEqual(genomic_motif_start(100, 1000, 1300, "-"), 1198)

    def test_edges_and_unknown_bases(self):
        self.assertEqual(len(context_at("A" * 102, 50)), 102)
        self.assertIsNone(context_at("A" * 102, 49))
        self.assertIsNone(context_at("A" * 102, 51))
        self.assertIsNone(context_at("A" * 50 + "N" + "A" * 51, 50))
        self.assertIsNone(context_at("ACGT" * 5, 10))

    def test_invalid_input_and_fasta(self):
        self.assertEqual(parse_sequence(">sample\nacgt acgt\n" + "ACGT" * 3)["sequence"], "ACGT" * 5)
        for raw in ("", ">one\n" + "A" * 20 + "\n>two\n" + "C" * 20, "A" * 19, "A" * 20 + "X", "A" * 20 + "\n>late", "N" * 25, "A" * 100001):
            with self.assertRaises(ValueError):
                parse_sequence(raw)

    def test_shared_transcript_exons_are_deduplicated(self):
        boundaries = transcript_boundaries([(0, 100), (0, 100), (200, 300)], "+", "g", "t")
        self.assertEqual(len(boundaries), 2)
        self.assertEqual(transcript_boundaries([(0, 100), (90, 200)], "+", "g", "t"), [])

    def test_overlapping_opposite_strand_genes_share_split(self):
        genes = [{"id": str(i), "region_start0": a, "region_end0": b, "strand": strand} for i, (a, b, strand) in enumerate([(0, 100, "+"), (80, 200, "-"), (190, 250, "+"), (250, 300, "+")])]
        groups = assign_groups(genes)
        self.assertEqual(len(groups), 2)
        self.assertEqual(len({g["group_id"] for g in genes[:3]}), 1)
        self.assertEqual(len({g["split"] for g in genes[:3]}), 1)

    def test_audit_rejects_duplicates_and_cross_split_overlap(self):
        def row(sequence, split, pos):
            return {"context": sequence, "split": split, "group_id": split, "genomic_motif_start0": pos, "label": "non_site"}
        duplicate = row("A" * 102, "train", 100)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            audit_rows([duplicate, {**duplicate, "split": "test", "group_id": "test"}])
        with self.assertRaisesRegex(ValueError, "overlap"):
            audit_rows([duplicate, row("C" * 102, "test", 110)])


@unittest.skipUnless((ROOT / "data/processed/manifest.json").exists(), "Run prepare_dataset.py for real-data checks")
class RealDatasetTests(unittest.TestCase):
    @unittest.skipUnless((ROOT / "data/raw/chr22.fa.gz").exists(), "Reference cache is optional in packaged release")
    def test_windows_match_reference_on_both_strands(self):
        from scripts.prepare_dataset import read_genome
        genome = read_genome(ROOT / "data/raw/chr22.fa.gz")
        with (ROOT / "data/processed/windows.jsonl").open(encoding="utf-8") as source:
            for line in source:
                row = json.loads(line)
                pos = row["genomic_motif_start0"]
                expected = genome[pos - 50:pos + 52]
                if row["strand"] == "-":
                    expected = reverse_complement(expected)
                self.assertEqual(row["context"], expected, row["id"])

    def test_full_dataset_isolated_and_aligned(self):
        rows = [json.loads(line) for line in (ROOT / "data/processed/windows.jsonl").read_text().splitlines()]
        audit_rows(rows)
        manifest = json.loads((ROOT / "data/processed/manifest.json").read_text())
        self.assertEqual(sum(sum(c.values()) for c in manifest["counts"].values()), len(rows))
        from scripts.prepare_dataset import digest_file
        for filename, checksum in manifest["files"].items():
            self.assertEqual(digest_file(ROOT / "data/processed" / filename), checksum)

    def test_demo_positions_and_held_out_membership(self):
        demos = json.loads((ROOT / "data/processed/demo_samples.json").read_text())
        membership = {g["id"]: g for g in json.loads((ROOT / "data/processed/split_membership.json").read_text())}
        self.assertEqual({d["genomic_region"]["strand"] for d in demos}, {"+", "-"})
        self.assertEqual(len(demos), 4)
        for demo in demos:
            self.assertEqual(membership[demo["gene_id"]]["split"], "test")
            region = demo["genomic_region"]
            self.assertEqual(len(demo["sequence"]), region["end0"] - region["start0"])
            self.assertTrue(demo["annotations"])
            for boundary in demo["annotations"]:
                index = boundary["position1"] - 1
                self.assertEqual(demo["sequence"][index:index + 2], {"donor": "GT", "acceptor": "AG"}[boundary["type"]])
                self.assertEqual(genomic_motif_start(index, region["start0"], region["end0"], region["strand"]), boundary["genomic_motif_start0"])


if __name__ == "__main__":
    unittest.main()
