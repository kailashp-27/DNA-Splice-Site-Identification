# EcoSplice submission materials

Prepared 9 October 2026 for the completed local application.

- `EcoSplice_Report.pdf`: final report describing the actual implementation, architecture, pseudocode, data, evaluation, measured benchmarks and limitations.
- `REPORT_SOURCE.md`: editable report content and source references.
- `EcoSplice_Presentation.pptx`: editable presentation with native charts, tables, architecture and speaker notes.
- `ARCHITECTURE.md` and `architecture.svg`: system diagram and explanation.
- `DEMO_SCRIPT.md`: a four-minute offline demonstration with a fallback for an occupied port.
- `VIVA_NOTES.md`: beginner explanations and likely questions with precise answers.
- `figures/`: scientific evaluation and benchmark plots, derived from frozen JSON results.

All metrics come from the saved model/evaluation artifacts. Runtime examples are observations on the recorded laptop, not performance guarantees. Full held-out window evaluation differs from cropped demo-region accuracy. Adaptive processing can change predictions. Energy is a constant-power estimate from measured time. No hardware acceleration, variant-effect model or cloud inference is implemented.

Start the application with `start-ecosplice.cmd` after one-time setup. Show the live software alongside the presentation. The reference data websites need internet only if you deliberately open their links.
