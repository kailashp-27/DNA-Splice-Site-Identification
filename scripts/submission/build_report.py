"""Build the final report and scientific figures from frozen result artifacts.

Run with the Codex bundled Python (reportlab), not the application environment.
"""
import html
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF, renderSVG

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/submission"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(exist_ok=True)
evaluation = json.loads((ROOT / "results/model-evaluation.json").read_text())
benchmark = json.loads((ROOT / "results/algorithm-verification.json").read_text())
model = json.loads((ROOT / "models/ecosplice-v1/manifest.json").read_text())
GREEN = colors.HexColor("#236b4d")
INK = colors.HexColor("#20382e")
PALE = colors.HexColor("#edf5ef")
styles = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=25, leading=30, spaceAfter=14, textColor=colors.black),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=18, leading=22, spaceAfter=12, textColor=colors.black),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12, leading=16, spaceBefore=12, spaceAfter=6, textColor=colors.black),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10.4, leading=15, spaceAfter=8, textColor=INK),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8.6, leading=12, spaceAfter=7, textColor=INK),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8.4, leading=11, spaceAfter=9, textColor=INK),
}
story, markdown = [], []


def heading(text, title=False):
    story.append(Paragraph(html.escape(text), styles["title" if title else "h1"]))
    markdown.append(("# " if title else "## ") + text + "\n")


def sub(text):
    story.append(Paragraph(html.escape(text), styles["h2"]))
    markdown.append("### " + text + "\n")


def para(text, small=False):
    story.append(Paragraph(html.escape(text), styles["small" if small else "body"]))
    markdown.append(text + "\n")


def table(rows, widths=None):
    converted = [[Paragraph(html.escape(str(v)), styles["small"]) for v in row] for row in rows]
    t = Table(converted, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6e9e7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7f6")]),
        ("GRID", (0, 0), (-1, -1), .5, colors.HexColor("#d9d9d9")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([t, Spacer(1, 9)])
    markdown.append("| " + " | ".join(map(str, rows[0])) + " |\n|" + " --- |" * len(rows[0]) + "\n" +
                    "\n".join("| " + " | ".join(map(str, row)) + " |" for row in rows[1:]) + "\n")


def code(text):
    story.append(Preformatted(text, styles["code"]))
    markdown.append("```text\n" + text + "\n```\n")


def page():
    story.append(PageBreak())


def diagram():
    d = Drawing(475, 245)
    def box(x, y, w, label, detail):
        d.add(Rect(x, y, w, 56, fillColor=PALE, strokeColor=GREEN, strokeWidth=1))
        d.add(String(x + w/2, y + 34, label, textAnchor="middle", fontName="Helvetica-Bold", fontSize=11, fillColor=INK))
        d.add(String(x + w/2, y + 16, detail, textAnchor="middle", fontName="Helvetica", fontSize=8.5, fillColor=INK))
    def arrow(x1, y1, x2, y2):
        d.add(Line(x1, y1, x2, y2, strokeColor=GREEN, strokeWidth=1.2))
        if x1 == x2:
            d.add(Polygon([x2, y2, x2-4, y2+7, x2+4, y2+7], fillColor=GREEN, strokeColor=GREEN))
        else:
            d.add(Polygon([x2, y2, x2-7, y2-4, x2-7, y2+4], fillColor=GREEN, strokeColor=GREEN))
    box(0, 180, 200, "React dashboard", "DNA / FASTA and saved results")
    box(275, 180, 200, "FastAPI service", "Validation and local API")
    box(275, 90, 200, "Analysis engine", "Three methods and saved NumPy models")
    box(0, 0, 200, "SQLite history", "Scientific snapshots and comparisons")
    box(275, 0, 200, "Report renderer", "CSV / JSON / printable HTML")
    arrow(200, 208, 275, 208)
    arrow(375, 180, 375, 146)
    arrow(375, 90, 375, 56)
    arrow(100, 28, 275, 28)
    d.add(Line(275, 118, 100, 118, strokeColor=GREEN, strokeWidth=1.2))
    arrow(100, 118, 100, 56)
    d.add(String(235, 228, "localhost HTTP", textAnchor="middle", fontSize=8.5, fillColor=INK))
    renderSVG.drawToFile(d, str(OUT / "architecture.svg"))
    return d


def bar_plot(name, categories, data, labels, maximum, unit):
    d = Drawing(475, 200)
    chart = VerticalBarChart()
    chart.x, chart.y, chart.width, chart.height = 42, 45, 423, 116
    chart.data = data
    chart.categoryAxis.categoryNames = categories
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 9
    chart.valueAxis.valueMin, chart.valueAxis.valueMax = 0, maximum
    chart.valueAxis.valueStep = maximum / 5
    chart.valueAxis.labels.fontSize = 8
    palette = [GREEN, colors.HexColor("#75a88a"), colors.HexColor("#8a79a1")]
    for i in range(len(data)):
        chart.bars[i].fillColor = palette[i]
        chart.bars[i].strokeColor = None
    chart.groupSpacing, chart.barSpacing = 12, 2
    d.add(chart)
    d.add(String(42, 181, unit, fontName="Helvetica-Bold", fontSize=10, fillColor=INK))
    for i, label in enumerate(labels):
        x = 45 + i * 135
        d.add(Rect(x, 8, 10, 10, fillColor=palette[i], strokeColor=None))
        d.add(String(x + 15, 9, label, fontSize=9, fillColor=INK))
    renderPDF.drawToFile(d, str(FIG / (name + ".pdf")))
    renderSVG.drawToFile(d, str(FIG / (name + ".svg")))
    return d


heading("EcoSplice final project report", title=True)
para("Local DNA splice boundary prediction and measured algorithm comparison. Release 1.0.0. Prepared 9 October 2026.", small=True)
sub("Abstract and implemented scope")
para("EcoSplice is a local React, Python and SQLite application that predicts possible canonical GT donor and AG acceptor boundaries from DNA context. A reproducible chromosome 22 dataset supplies annotated sites and ordinary occurrences. Saved logistic models provide genuine predictions. Three operational methods compare exhaustive scoring, candidate filtering and cheaper preliminary scoring with detailed escalation. The application measures computation and work counts, preserves completed runs and exports consistent reports.")
para("Detailed held-out canonical-candidate F1 is 0.7987 for donors and 0.7173 for acceptors. Adaptive F1 is 0.7858 and 0.7238 while avoiding 80.77 percent of detailed evaluations. Both the saving and the donor quality loss are reported. Outputs identify possible boundaries; complete intron pairing, sequence removal and tissue-specific decisions require additional work.")
sub("Local application architecture")
story.append(diagram())
story.append(Spacer(1, 8))
markdown.append("![Local application architecture](architecture.svg)\n")
para("One loopback Python process serves the built React interface and FastAPI endpoints. Python owns authoritative input checks, saved model inference and timing. SQLite stores original sequence, scientific settings, predictions and attached comparisons. A shared report renderer selects all or filtered candidates from the saved snapshot. Separate development scripts prepare data and train; ordinary startup never calls them.")

page()
heading("Dataset and model preparation")
para("The frozen annotation is GENCODE human release 49 for GRCh38.p14. The sequence is UCSC hg38 primary chromosome 22, corresponding to NC_000022.11. Only the primary chromosome is used; alternate contigs and patches are excluded. Source URLs, checksums and terms remain in the dataset documentation and manifest. Small real samples ship with attribution [1-3].")
table([["Partition", "Donor", "Acceptor", "Non site", "Total"], ["Train",3654,3811,85766,93231], ["Validation",858,821,18474,20153], ["Test",900,918,19401,21219]], [115,80,80,100,100])
para("The preparation selects 400 protein-coding genes in 304 connected genomic groups and retains 134,603 unique 102-base windows. Positives come from annotated exon adjacency. GT/AG and ordinary negative positions avoid every same-strand boundary in the comprehensive annotation, including annotations outside selected training genes. A negative means unannotated in this release, not experimentally proven inactive.")
sub("Leakage controls and coordinates")
para("Gene spans expanded by 50 bases form connected components when they overlap. Entire components stay within one seeded train, validation or test partition. Global duplicate removal includes reverse-complement equivalents. Audits check overlapping cross-split windows, duplicates and positive motif alignment. Distant gene-family homology independence has not been established.")
para("GTF one-based inclusive exon coordinates become zero-based half-open intervals during preparation. Minus-strand DNA is reverse-complemented into the annotated direction. The application displays one-based motif starts in the supplied sequence: GT at 101 occupies 101-102, with the donor boundary before 101; AG at 199 occupies 199-200, with the acceptor boundary after 200. User DNA remains in its supplied direction.")
sub("Saved classifiers and fixed settings")
table([["Scorer", "Context", "Features", "Donor threshold", "Acceptor threshold"], ["Preliminary", "22 bases", "Single bases", "0.36", "0.31"], ["Detailed", "102 bases", "Bases and adjacent pairs", "0.41", "0.44"]], [92,70,133,90,90])
para("Training fits three-class logistic regression on train only. Validation chooses scorer thresholds and adaptive routing. The preliminary decisive ranges are donor score at most 0.18 or at least 0.52, and acceptor score at most 0.0775 or at least 0.655. Remaining candidates reach the detailed scorer. Numeric NumPy coefficient archives and a manifest ship with model ecosplice-v1-64223ad070d6. Independent retraining produced byte-identical weights and manifest.")
para("Softmax scores reflect the sampled training class balance. No fitted calibration transform establishes biological probability. The interface therefore calls them model scores. Complete A/C/G/T contexts are required; unknown or cropped contexts receive no invented padding or score.")

page()
heading("Algorithms and complexity")
para("All methods validate the same input, retain the same canonical candidate domain and stream inference in batches of at most 512 windows by default. Incomplete or N-containing windows remain visible with a reason and no score. Ordinary eligible positions really receive detailed scoring in the exhaustive baseline.")
sub("Exhaustive baseline")
code("scan canonical motifs for the shared output list\nfor each possible two-base start in DNA:\n    extract a complete ACGT context when eligible\n    send eligible contexts in bounded batches to detailed\n    retain scores only for GT donor or AG acceptor\napply each candidate type's detailed threshold")
sub("Candidate filtering")
code("scan DNA once for GT and AG\nfor each canonical motif:\n    extract its eligible complete ACGT context\n    score bounded batches using the SAME detailed model\n    apply the SAME detailed threshold\nretain unscoreable motifs with their reason")
sub("Adaptive processing")
code("scan DNA once for GT and AG\nfor each eligible candidate batch:\n    score the central 22 bases with preliminary\n    finalize decisive low or high preliminary cases\n    send only uncertain cases to detailed\n    use the final scorer's threshold and record route\nretain unscoreable motifs with their reason")
sub("Work and space")
para("Let n be length, k canonical motifs, e all eligible contexts, q eligible canonical contexts, m uncertain candidates, w detailed width, l preliminary width, B batch size and c classes. Context extraction/checking and coefficient summation contribute width-dependent work.")
table([["Method", "Detailed calls", "Preliminary calls", "Variable width work"], ["Exhaustive", "e", "0", "O(nw + ecw)"], ["Filtered", "q", "0", "O(n + kw + qcw)"], ["Adaptive", "m", "q", "O(n + kw + qcl + mcw)"]], [100,80,90,205])
para("Fixed widths, models and classes make every method O(n) in the worst case. Filtering improves the amount of expensive work rather than the asymptotic class. Additional working/output memory is O(k + Bcw), plus fixed coefficients; storing the input adds O(n). Peak batch windows is a work counter, not measured RAM. Baseline and filtered canonical scores agree within 1e-12 in real-region and maximum-length checks.")

page()
heading("Held out evaluation and adaptive tradeoffs")
para("Evaluation uses frozen test groups after validation selects settings. Per-type canonical-candidate metrics evaluate only that motif domain; ordinary non-motif positions do not inflate splice detection metrics. The donor domain contains 7,497 candidates with 900 annotated donors. The acceptor domain contains 7,523 with 918 annotated acceptors. These supports are separate from all 21,219 sampled test windows.")
rows = [["Method", "Type", "Precision", "Recall", "F1"]]
for method in ("preliminary", "detailed", "adaptive"):
    for kind in ("donor", "acceptor"):
        metrics = evaluation["test"][method][kind]["canonical_candidates"]
        rows.append([method.capitalize(), kind.capitalize(), *(f"{metrics[key]:.4f}" for key in ("precision", "recall", "f1"))])
table(rows, [110,95,90,90,90])
plot = bar_plot("test_f1", ["Donor", "Acceptor"], [[evaluation["test"][m][k]["canonical_candidates"]["f1"] for k in ("donor","acceptor")] for m in ("detailed","adaptive")], ["Detailed", "Adaptive"], 1, "Held-out canonical-candidate F1")
story.append(plot)
markdown.append("![Held out F1](figures/test_f1.svg)\n")
para("Detailed donor confusion counts are TP 712, FP 171, FN 188, TN 6,426. Detailed acceptor counts are TP 637, FP 221, FN 281, TN 6,384. Precision is TP/(TP+FP), recall is TP/(TP+FN), and F1 is 2TP/(2TP+FP+FN). Full matrices, threshold curves and reliability bins remain in model-evaluation.json.")
para("Adaptive uses 2,888 detailed calls instead of 15,020, avoiding 12,132 calls or 80.77 percent. Preliminary calls are additional work. Donor F1 falls by 0.0129 on test, exceeding the allowed validation selection loss of 0.005. Acceptor F1 rises by 0.0065. These results remain unchanged without tuning on test. Four complete cropped demo regions have a separate pipeline evaluation that includes unscoreable annotated edges as misses. Arbitrary uploaded FASTA supplies no known answers.")

page()
heading("Measured computation and estimated energy")
para("The frozen reference experiment loads the model before timing, excludes one warm-up per method, then performs five fresh computations per method/input in shuffled order using batch size 512. It records raw totals, median, min/max, IQR and stages for validation, scanning, context preparation, preliminary/detailed inference and other computation. Inference includes feature encoding. HTTP/UI transfer, serialization and SQLite writes are outside computation timing.")
para("Recorded hardware is Windows 11, AMD64 Family 25 Model 68 Stepping 1, 16 logical CPUs, Python 3.12.10 and NumPy 2.2.6. The table reports earlier frozen observations on that laptop. Fresh comparisons may differ with load and timing variation.")
names = ["TBC1D22A", "NUP50", "ARVCF", "SF3A1", "Motif free synthetic", "Motif rich synthetic"]
rows = [["Input", "Bases", "Exhaustive ms", "Filtered ms", "Adaptive ms"]]
for name, item in zip(names, benchmark["inputs"]):
    rows.append([name, f'{item["length"]:,}', *(f'{item["results"][m]["median_ms"]:.3f}' for m in ("exhaustive","filtered","adaptive"))])
table(rows, [137,65,91,91,91])
plot = bar_plot("real_region_runtime", names[:4], [[item["results"][m]["median_ms"] for item in benchmark["inputs"][:4]] for m in ("exhaustive","filtered","adaptive")], ["Exhaustive", "Filtered", "Adaptive"], 20, "Five-repeat median computation in milliseconds")
story.append(plot)
markdown.append("![Real region median runtime](figures/real_region_runtime.svg)\n")
para("The motif-rich synthetic 100,000-base input has 49,950 eligible candidates and 50 unscoreable edge motifs. Exhaustive performs 99,899 detailed evaluations. Synthetic controls have no biological truth or accuracy claim. Differences on tiny motif-free filtered/adaptive timings can lie within variation. The product displays negative reductions if an optimized method runs slower.")
sub("Energy assumptions")
para("Estimated energy in joules = assumed power in watts multiplied by measured milliseconds / 1000. At a visible 15 W assumption, the frozen motif-rich medians imply 12.024 J exhaustive, 6.755 J filtered and 3.069 J adaptive. Equal assumed power makes estimated energy reduction follow runtime reduction. These values are computation estimates, not measured laptop power or battery consumption. Each run preserves its actual user assumption.")

page()
heading("Finished application and release verification")
sub("Input and failure handling")
para("Users paste DNA or upload a single FASTA/TXT record up to 1 MB. The authoritative backend permits A/C/G/T/N, requires 20 called bases and caps DNA at 100,000 bases. It rejects empty/invalid input, extra records and oversized bodies. Missing model, unavailable service and analysis failures have explicit states. A valid motif-free input succeeds with an empty candidate list. Short, edge and unknown-base contexts stay unscored. Failed real analysis never substitutes sample predictions.")
sub("Dashboard and history")
para("Analyse links candidate tables to sequence context and shows genuine scores/routes. Compare reruns the selected stored DNA under all three methods for 3-7 repetitions and attaches timings, work, quality differences and estimated energy. Validate shows frozen held-out metrics and descriptive threshold tradeoffs. Reports reopens, renames and deletes local runs. CSV, JSON and print select the same saved candidate set; filtering leaves full-run measurements clearly identified.")
para("SQLite scientific snapshots preserve normalized DNA, one-based coordinate convention, scorer/model identity, thresholds, input hashes, stage measurements and power assumptions across restarts. Comparisons attach without rewriting original predictions. React generation and abort guards reject late replies after input changes, including transports that ignore cancellation. Server computation already started can still finish and save after Stop waiting.")
sub("Local launch and packaging")
para("One-time setup creates a private Python environment, installs a complete exact runtime lock and builds React with its npm lockfile. start-ecosplice.cmd starts one loopback service at http://127.0.0.1:8765. A prebuilt release ZIP needs Python 3.12 but no Node.js. Neither normal launch nor inference needs internet, genomic downloads, training or accounts. Helpful startup checks cover missing files/dependencies and occupied ports. A file-hash manifest accompanies the ZIP; user history and DNA are excluded.")
sub("Verification evidence and limits")
para("The final automated suite covers coordinates, labels/splits, output alignment, real adaptive routing, baseline parity, input/errors, concurrency, persistence, reports, comparison provenance and production static routing. The earlier desktop/phone browser checks cover actual uploads/downloads, restart/reopen and 100,000-base UI operation with bounded batches. A fresh isolated environment and extracted-package HTTP workflow verify normal application paths while outbound sockets are denied. The OS is not physically disconnected by the test.")
para("Final browser checks verify the concise green interface, progress guide, real ARVCF analysis/comparison, history after reload and actual FASTA download. Phone help at 390 by 844 pixels fits without body overflow. All 49 Python and 14 JavaScript tests pass. One earlier memory-constrained repeated test failed during concurrent QA, then passed with the QA backend stopped. Evidence remains in ignored QA folders and the release documentation.")

page()
heading("Limitations references and reproduction")
sub("Scientific limitations and future work")
para("This is a sampled chromosome 22 study with canonical motifs and a small context classifier. It does not establish genome-wide, species-wide, tissue-specific or clinical performance. Negative annotations can be incomplete. Overlap/duplicate isolation does not guarantee separation of distant homologues. Score calibration, broader independent datasets and gene-family grouping would strengthen future evaluation.")
para("Future work includes complete intron pairing, variant effects, cryptic-site investigation, probability calibration and broader biological testing. Quantization, Jetson/NPU work, cloud offloading and federated learning remain proposals. The delivered application runs local CPU inference. Estimated energy should be complemented by measured power before making device-level efficiency claims.")
sub("Artifact identity and reproducibility")
para("Model ecosplice-v1-64223ad070d6 and dataset gencode49-grch38-chr22-v1 have frozen settings. Dataset fingerprint: a884895b613c8923e41e1830c2d475377071272848f2fb4c9f24335f936c5464.", small=True)
para("Development utilities reproduce download, preparation, training and algorithm verification. Frozen manifests preserve historical hashes instead of rewriting them when files move. Source reproduction needs genomic caches or one development-time download; the professor's demonstration uses the bundled model and four small labelled regions.")
code("python scripts/data/download_reference.py\npython scripts/data/prepare_dataset.py\npython -m pip install -r scripts/models/requirements.txt\npython scripts/models/train_models.py\npython scripts/models/verify_algorithms.py\npython scripts/package_release.py")
sub("Sources and attribution")
references = [
    "[1] GENCODE. Human release 49, GRCh38.p14 comprehensive annotation. https://www.gencodegenes.org/human/release_49.html",
    "[2] UCSC Genome Browser. hg38 primary chromosome sequence downloads. https://hgdownload.soe.ucsc.edu/goldenPath/hg38/chromosomes/",
    "[3] GENCODE data access and source terms. https://www.gencodegenes.org/pages/data_access.html and https://www.ebi.ac.uk/about/terms-of-use/",
    "[4] scikit-learn documentation. Probability calibration. https://scikit-learn.org/stable/modules/calibration.html",
    "[5] EcoSplice frozen artifacts. data/processed/manifest.json, models/ecosplice-v1/manifest.json, results/model-evaluation.json, results/algorithm-verification.json and results/model-reproducibility.json.",
]
for reference in references:
    para(reference, small=True)
para("GENCODE describes its data as open access. UCSC distributes the referenced chromosome files for public use. Preserve scientific attribution and the original source terms with redistributed samples. No new software licence is assigned to the scientific sources. Online source pages were checked on 9 October 2026; the application uses the frozen release, not a changing latest download.", small=True)
sub("Demonstration materials")
para("The editable PowerPoint explains scope, architecture, data, algorithms and measured tradeoffs. DEMO_SCRIPT.md provides a four-minute sequence. VIVA_NOTES.md explains biology, classifier scores, complexity, thresholds, evaluation, energy and persistence in beginner language. REPORT_SOURCE.md retains editable report text, and figures are available as vector SVG/PDF.")


def footer(canvas, doc):
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#607268"))
    canvas.drawString(60, 32, "EcoSplice 1.0.0   Final project report   9 October 2026")
    canvas.drawRightString(A4[0] - 60, 32, str(doc.page))


document = SimpleDocTemplate(str(OUT / "EcoSplice_Report.pdf"), pagesize=A4, rightMargin=60, leftMargin=60,
                             topMargin=45, bottomMargin=52, title="EcoSplice final project report", author="EcoSplice project")
document.build(story, onFirstPage=footer, onLaterPages=footer)
(OUT / "REPORT_SOURCE.md").write_text("\n".join(markdown), encoding="utf-8")
print("Built report PDF, editable Markdown, architecture SVG and scientific figure SVG/PDF files.")
