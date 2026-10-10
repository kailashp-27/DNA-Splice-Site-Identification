# Test EcoSplice yourself

Setup is prepared on the development laptop. For another laptop, follow [LOCAL_RELEASE.md](LOCAL_RELEASE.md) once.

## Start

1. Double-click `start-ecosplice.cmd` in the project folder. Keep its terminal open.
2. Open **http://127.0.0.1:8765**. If the port is occupied, run `start-ecosplice.cmd --port 8766` and open the printed address.
3. Follow the app's **Load → Analyse → Compare → Export** guide. Check marks represent completed input, analysis and comparison; visiting a page does not complete a measurement.

## Upload test: about five minutes

1. Click **Upload FASTA → Choose file**. Select `data/demo/EcoSplice_test.fasta`, then **Load sequence**. You can also download this real ARVCF file from the input dialog or Help & methods.
2. Expect **2,402 bases**. Choose **Candidate filtering**, name the run `My upload test`, leave assumed power at **15 W**, and click **Run analysis**.
3. Expect **349 candidates**, including **10 unscored** edge contexts. Select a row: the motif, one-based position and surrounding DNA should agree. Scores are model scores, not probabilities. Most motifs are not predicted boundaries.
4. Open **Compare**, choose **3 repetitions**, then **Measure all three methods**. Expect three measured rows with medians, variation, work counts and estimated energy. Exhaustive and filtered predictions should agree. Adaptive can change predictions. Timings vary with your laptop's workload; there is no required speedup.
5. Open **Validate**. The independent test evaluation is available; your upload's accuracy is unavailable because it has no accompanying labels. To test annotated input metrics, use **Try a sample → ARVCF**, then analyse again.
6. Open **Reports**. Download **CSV** and **JSON**; open the print report and use **Print → Save as PDF**. Check the run name, model ID, candidate positions, export count and power assumption agree. JSON includes the DNA and saved comparison.
7. Return to Analyse, select **Acceptor** and **Predicted only** filters. In Reports choose **Filtered candidates** and export again. CSV, JSON and print output should have matching selected counts; full-run measurements stay unchanged.
8. Rename the saved run. Close the browser, stop the terminal with **Ctrl+C**, launch again, then **Reports → Reopen**. The run and comparison should remain. Delete only a disposable test run; downloaded files remain separate.

## Quick error checks

| Test | Expected result |
| --- | --- |
| Paste `ACGTXACGTACGTACGTACGTACGT` | Unsupported-symbol error; no substitute predictions |
| Paste `ACGT` or submit empty input | Minimum-length / empty-input error |
| Paste `AAAAAAAAAAAAAAAAAAAA` | Valid run with no GT/AG candidates |
| Upload a FASTA with two `>` records | Single-record error |
| Use DNA containing N near a GT/AG context | Affected candidates remain unscored with a reason |
| Change DNA while analysis/comparison is pending | The old response never replaces the new input; completed server work may still appear in history |
| Stop the server, then retry a request | Readable service error; relaunch and Retry connection |
| Reduce browser width to about 390 pixels | Navigation and workflow stay usable, without body overflow; wide tables can scroll within their panel |

The sample is genuine reference DNA in the orientation expected by the model. It is a demonstration of possible boundaries, not a clinical interpretation or a complete intron prediction.
