# Four minute EcoSplice demonstration

## Before the professor arrives

Complete setup once, start `start-ecosplice.cmd`, and open http://127.0.0.1:8765. Keep the presentation ready. Close unrelated heavy applications if convenient because timings vary with background load. Disconnect internet if demonstrating offline operation. Use the bundled **ARVCF** sample for known annotation labels. Never train or download references during the demonstration.

## 0 to 40 seconds

Say: “EcoSplice predicts possible donor and acceptor boundaries from DNA context. A GT or AG is a candidate, and the saved model helps distinguish annotated-like sites from ordinary occurrences. The application runs on this laptop.”

Open New analysis and select the real ARVCF sample. Explain that this minus-strand sample is already oriented in the direction being analysed. Choose Adaptive processing, name the run “Professor demonstration”, retain the visible power assumption, and run.

## 40 to 100 seconds

Show the candidate map, sequence context and table. Select a scored candidate, then an edge candidate if available. Say: “Positions count from one and refer to the first letter of the motif. A score needs 50 bases on each side. Edge or unknown contexts remain visible with an explanation. Scores describe this trained classifier and are not calibrated biological probabilities.”

Show the actual final scorer and processing route. Say: “The preliminary model handles decisive cases. Only uncertain cases reach the more detailed model.”

## 100 to 160 seconds

Open Compare, select three repeats to keep the demonstration short, and measure. Show median and variation, detailed work avoided, quality differences and assumed watts. Say: “Exhaustive scoring examines every eligible position. Filtering uses the same detailed model only at GT and AG, so those predictions agree. Adaptive can change predictions because it sometimes uses the cheaper model. All methods remain linear with fixed context width. The savings come from fewer expensive evaluations.”

Explain: “Estimated joules equal assumed watts multiplied by computation seconds. The laptop's actual power consumption was not measured.” Do not promise that every measurement will match a slide's earlier laptop benchmark.

## 160 to 205 seconds

Open Validate. Show the frozen held-out metrics and confusion matrices. Say: “Training uses one split, thresholds and routing use validation, and these results use held-out test groups. Detailed F1 is about 0.799 for donors and 0.717 for acceptors. Adaptive avoids about 80.8 percent of detailed test evaluations, with a donor F1 drop. This is one chromosome's sampled evaluation.”

Mention that uploading the same FASTA produces predictions without automatically granting annotation labels. Show that rule in Help if needed.

## 205 to 240 seconds

Open Reports, rename/reopen the saved run, and export JSON or CSV. Show the all/filtered choice. Open the printable report and use Print / Save as PDF if time permits. Say: “SQLite keeps the sequence, model settings, predictions and measured comparison after restart. Exports read the same saved run.”

## If something interrupts the demonstration

An occupied port: stop the previous EcoSplice terminal, or launch `start-ecosplice.cmd --port 8766` and open its printed address. An unavailable service: start the terminal, then Retry connection. A slow comparison: wait for its real measurement or stop waiting and reopen history after it finishes. The presentation and frozen experiment remain available for discussing results. Never substitute a successful sample output for failed real analysis.
