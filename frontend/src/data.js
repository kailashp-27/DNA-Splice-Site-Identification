const primarySites = [
  { position: 124, type: 'Donor', score: 0.96 },
  { position: 238, type: 'Acceptor', score: 0.94 },
  { position: 365, type: 'Donor', score: 0.91 },
  { position: 421, type: 'Acceptor', score: 0.88 },
  { position: 548, type: 'Donor', score: 0.86 },
  { position: 602, type: 'Acceptor', score: 0.84 },
  { position: 716, type: 'Donor', score: 0.82 },
  { position: 804, type: 'Acceptor', score: 0.79 },
  { position: 913, type: 'Donor', score: 0.76 },
  { position: 1038, type: 'Acceptor', score: 0.73 },
  { position: 1102, type: 'Donor', score: 0.63 },
  { position: 1165, type: 'Acceptor', score: 0.58 },
];

// Deterministic artificial DNA. No patient data or real gene annotation is used.
function syntheticSequence(length, sites, seed = 29) {
  let state = seed;
  const bases = Array.from({ length }, () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return 'ACGT'[state >>> 30];
  });
  for (const site of sites) {
    const context = site.type === 'Donor' ? 'CAGGTAAGT' : 'TTTTCAGG';
    const start = site.position - 1 - (site.type === 'Donor' ? 3 : 5);
    for (let i = 0; i < context.length; i++) bases[start + i] = context[i];
  }
  return bases.join('');
}

function makeSample(id, name, description, length, sites, seed, baselineMs, optimizedMs) {
  const sequence = syntheticSequence(length, sites, seed);
  return {
    id, name, description, sequence, source: 'Synthetic educational fixture', builtIn: true,
    sites: sites.map((site, index) => ({ ...site, id: `SS-${String(index + 1).padStart(3, '0')}`, motif: site.type === 'Donor' ? 'GT' : 'AG', route: site.score >= 0.8 ? 'Fast path' : 'Detailed path' })),
    benchmark: { baselineMs, optimizedMs, contextWidth: 21 },
  };
}

export const SAMPLES = [
  makeSample('SYN-001', 'Demo sequence 01', 'A balanced example with clear donor and acceptor candidates.', 1200, primarySites, 29, 186, 112),
  makeSample('SYN-002', 'Ambiguous sequence', 'Lower scores demonstrate uncertainty and threshold filtering.', 840, [
    { position: 112, type: 'Donor', score: 0.88 }, { position: 221, type: 'Acceptor', score: 0.81 },
    { position: 337, type: 'Donor', score: 0.74 }, { position: 442, type: 'Acceptor', score: 0.69 },
    { position: 596, type: 'Donor', score: 0.61 }, { position: 725, type: 'Acceptor', score: 0.53 },
  ], 71, 142, 98),
  { id: 'SYN-003', name: 'Motif-free control', description: 'An artificial control with no GT or AG motifs.', sequence: 'ACCT'.repeat(120), source: 'Synthetic educational fixture', builtIn: true, sites: [], benchmark: { baselineMs: 78, optimizedMs: 23, contextWidth: 21 } },
];

// Scores below are constructed fixtures, not the result of training a model.
export const VALIDATION_SAMPLES = [
  ...Array.from({ length: 88 }, (_, i) => ({ truth: true, score: 0.72 + (i % 26) / 100 })),
  ...Array.from({ length: 10 }, (_, i) => ({ truth: true, score: 0.42 + i * 0.025 })),
  ...Array.from({ length: 7 }, (_, i) => ({ truth: false, score: 0.71 + i * 0.025 })),
  ...Array.from({ length: 95 }, (_, i) => ({ truth: false, score: 0.08 + (i % 55) / 100 })),
];

export const NAV_ITEMS = [
  { id: 'analysis', label: 'Analyse', icon: 'Dna' },
  { id: 'algorithms', label: 'Compare', icon: 'ChartNoAxesCombined' },
  { id: 'accuracy', label: 'Validate', icon: 'Target' },
  { id: 'reports', label: 'Reports', icon: 'Files' },
];
