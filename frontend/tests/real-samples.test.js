import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { parseSequence, inspectSequence, scanMotifs } from '../src/lib/analysis.js';

const metadata = new URL('../../data/processed/demo_samples.json', import.meta.url);

test('real held-out FASTA files preserve annotated coordinates through the React input utilities', { skip: !existsSync(metadata) }, () => {
  const samples = JSON.parse(readFileSync(metadata, 'utf8'));
  assert.equal(samples.length, 4);
  for (const sample of samples) {
    const fasta = readFileSync(new URL(`../../data/demo/${sample.id}.fasta`, import.meta.url), 'utf8');
    const parsed = parseSequence(fasta);
    assert.equal(parsed.sequence, sample.sequence);
    assert.equal(parsed.name, sample.id);
    assert.equal(inspectSequence(parsed.sequence).canAnalyze, true);
    const motifs = scanMotifs(parsed.sequence);
    assert.ok(motifs.every((site) => site.score === null));
    for (const annotation of sample.annotations) {
      assert.ok(motifs.some((site) => site.position === annotation.position1 && site.type.toLowerCase() === annotation.type), `${sample.id}: ${annotation.type} ${annotation.position1}`);
    }
  }
});
