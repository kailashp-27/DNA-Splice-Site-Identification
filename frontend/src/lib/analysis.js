export const MAX_SEQUENCE_LENGTH = 100_000;

// Preserve unknown symbols so the quality report can explain them to the user.
export function parseSequence(raw) {
  const lines = raw.trim().split(/\r?\n/);
  const headers = lines.filter((line) => line.trim().startsWith('>'));
  if (headers.length > 1) throw new Error('Please upload one FASTA record at a time. This file contains multiple sequences.');
  const sequence = lines.filter((line) => !line.trim().startsWith('>')).join('').replace(/\s/g, '').toUpperCase();
  if (!sequence) throw new Error('Add a DNA sequence before continuing.');
  if (sequence.length > MAX_SEQUENCE_LENGTH) throw new Error('This preview supports sequences up to 100,000 bases. Please use a shorter sample.');
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

export function metricsFromPredictions(samples, threshold = 0.7) {
  const matrix = { tp: 0, fp: 0, fn: 0, tn: 0 };
  for (const sample of samples) {
    const predicted = sample.score >= threshold;
    matrix[sample.truth ? (predicted ? 'tp' : 'fn') : (predicted ? 'fp' : 'tn')]++;
  }
  const precision = matrix.tp / (matrix.tp + matrix.fp) || 0;
  const recall = matrix.tp / (matrix.tp + matrix.fn) || 0;
  return { ...matrix, precision, recall, f1: 2 * precision * recall / (precision + recall) || 0, accuracy: (matrix.tp + matrix.tn) / samples.length || 0 };
}

export function energyEstimate(runtimeMs, powerWatts) {
  return runtimeMs / 1000 * powerWatts;
}

export function csvForSites(sites, sampleName) {
  const escape = (value) => {
    let text = String(value ?? '');
    // Spreadsheet applications may execute cells starting with these characters.
    if (/^[=+\-@]/.test(text)) text = `'${text}`;
    return `"${text.replaceAll('"', '""')}"`;
  };
  return [
    ['Sample', 'Site ID', 'Position (1-based motif start)', 'Type', 'Motif', 'Demonstration score (not probability)', 'Route'],
    ...sites.map((site) => [sampleName, site.id, site.position, site.type, site.motif, site.score == null ? 'Not available' : site.score.toFixed(2), site.route]),
  ].map((row) => row.map(escape).join(',')).join('\r\n');
}
