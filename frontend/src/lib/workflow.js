// Guidance follows completed work, including a reopened run. Visiting a page
// never marks a measurement or export as complete.
export function workflowState({ loaded, valid, run, ready, busy, view }) {
  return {
    completed: [loaded && valid, !!run, !!run?.comparison, false],
    disabled: [false, !loaded || !!busy, !run || !!busy, !run],
    hint: busy ? 'Working… You can stop waiting above.'
      : !loaded ? 'Start with a sample, pasted DNA, or a FASTA file.'
        : !valid ? 'Check your input before analysing.'
          : !run && !ready ? 'Reconnect the local service to analyse.'
            : !run ? 'Choose a method below, then Run analysis.'
              : view === 'reports' ? 'Choose all or filtered results, then download CSV / JSON or print.'
                : !run.comparison && view === 'algorithms' ? 'Choose repetitions, then Measure all three methods.'
                  : !run.comparison ? 'Results are saved. Open Compare to measure all three methods.'
                : 'Comparison saved. Open Reports to download or print your results.',
  };
}
