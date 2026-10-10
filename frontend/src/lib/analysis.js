export const MAX_SEQUENCE_LENGTH = 100_000;

// Preserve unknown symbols so the quality report can explain them to the user.
export function parseSequence(raw) {
  const lines = raw.trim().split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const headers = lines.filter((line) => line.trim().startsWith('>'));
  if (headers.length > 1) throw new Error('Please upload one FASTA record at a time. This file contains multiple sequences.');
  if (headers.length && !lines[0].startsWith('>')) throw new Error('The FASTA header must appear before the DNA sequence.');
  const sequence = lines.filter((line) => !line.trim().startsWith('>')).join('').replace(/\s/g, '').toUpperCase();
  if (!sequence) throw new Error('Add a DNA sequence before continuing.');
  if (sequence.length > MAX_SEQUENCE_LENGTH) throw new Error('Sequences may contain at most 100,000 bases.');
  return { name: headers[0]?.trim().slice(1).split(/\s+/)[0] || 'Custom sequence', sequence };
}

export function inspectSequence(sequence) {
  const counts = { A: 0, C: 0, G: 0, T: 0, N: 0 };
  const invalid = [];
  [...sequence].forEach((base, index) => {
    if (Object.hasOwn(counts, base)) counts[base]++;
    else invalid.push({ base, position: index + 1 });
  });
  const called = counts.A + counts.C + counts.G + counts.T;
  return {
    counts, invalid, length: sequence.length,
    gc: called ? ((counts.G + counts.C) / called) * 100 : 0,
    completeness: sequence.length ? (called / sequence.length) * 100 : 0,
    canAnalyze: invalid.length === 0 && called >= 20,
  };
}

// This scanner finds canonical motifs only. It does not predict biological use.
export function scanMotifs(sequence) {
  const sites = [];
  for (let index = 0; index < sequence.length - 1; index++) {
    const motif = sequence.slice(index, index + 2);
    if (motif === 'GT' || motif === 'AG') {
      sites.push({ id: `C-${String(sites.length + 1).padStart(3, '0')}`, position: index + 1, type: motif === 'GT' ? 'Donor' : 'Acceptor', motif, score: null, route: 'Motif scan' });
    }
  }
  return sites;
}
