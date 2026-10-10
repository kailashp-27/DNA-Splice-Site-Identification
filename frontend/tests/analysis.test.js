import test from 'node:test';
import assert from 'node:assert/strict';
import { parseSequence, inspectSequence, scanMotifs } from '../src/lib/analysis.js';

test('single FASTA parsing normalizes whitespace and preserves invalid characters for QC', () => {
  assert.deepEqual(parseSequence('>demo description\nac gt\nNNX'), { name: 'demo', sequence: 'ACGTNNX' });
  assert.throws(() => parseSequence('>first\nACGT\n>second\nAAAA'), /multiple sequences/);
  assert.throws(() => parseSequence('ACGT\n>late\nACGT'), /header must appear/);
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
