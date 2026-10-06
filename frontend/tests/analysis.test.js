import test from 'node:test';
import assert from 'node:assert/strict';
import { SAMPLES, VALIDATION_SAMPLES } from '../src/data.js';
import { parseSequence, inspectSequence, scanMotifs, metricsFromPredictions, energyEstimate, csvForSites } from '../src/lib/analysis.js';

test('single FASTA parsing normalizes whitespace and preserves invalid characters for QC', () => {
  assert.deepEqual(parseSequence('>demo description\nac gt\nNNX'), { name: 'demo', sequence: 'ACGTNNX' });
  assert.throws(() => parseSequence('>first\nACGT\n>second\nAAAA'), /multiple sequences/);
  assert.throws(() => parseSequence(' \n '), /Add a DNA sequence/);
  assert.throws(() => parseSequence('A'.repeat(100_001)), /100,000/);
});

test('QC uses called bases for GC and reports invalid positions without silently removing them', () => {
  const result = inspectSequence('ACGTNNX');
  assert.equal(result.gc, 50);
  assert.equal(result.counts.N, 2);
  assert.deepEqual(result.invalid, [{ base: 'X', position: 7 }]);
  assert.equal(result.canAnalyze, false);
  assert.equal(inspectSequence('ACGT'.repeat(5)).canAnalyze, true);
  assert.equal(inspectSequence('N'.repeat(30)).canAnalyze, false);
});

test('motif scan preserves overlapping motifs with 1-based positions and supplies no fabricated scores', () => {
  const sites = scanMotifs('AGTAG');
  assert.deepEqual(sites.map(({ position, type }) => [position, type]), [[1, 'Acceptor'], [2, 'Donor'], [4, 'Acceptor']]);
  assert.ok(sites.every((site) => site.score === null));
  assert.deepEqual(scanMotifs('ACCTACCT'), []);
});

test('every hardcoded candidate matches its motif in the synthetic sequence', () => {
  for (const sample of SAMPLES) {
    for (const site of sample.sites) assert.equal(sample.sequence.slice(site.position - 1, site.position + 1), site.motif, `${sample.id} ${site.id}`);
  }
  assert.equal(scanMotifs(SAMPLES[2].sequence).length, 0);
});

test('threshold metrics count mistakes and handle empty-positive predictions', () => {
  const metrics = metricsFromPredictions(VALIDATION_SAMPLES, .7);
  assert.deepEqual({ tp: metrics.tp, fp: metrics.fp, fn: metrics.fn, tn: metrics.tn }, { tp: 88, fp: 7, fn: 10, tn: 95 });
  assert.equal(metrics.accuracy, .915);
  assert.ok(Math.abs(metrics.f1 - 176 / 193) < 1e-12);
  const empty = metricsFromPredictions(VALIDATION_SAMPLES, 1);
  assert.equal(empty.precision, 0);
  assert.equal(empty.f1, 0);
});

test('energy uses seconds and CSV escapes names and records missing scores', () => {
  assert.equal(energyEstimate(112, 8), .896);
  const csv = csvForSites(scanMotifs('GT'), '=danger,"name"');
  assert.ok(csv.includes('"\'=danger,""name"""'));
  assert.ok(csv.includes('"Not available"'));
  assert.ok(csv.includes('1-based motif start'));
});
