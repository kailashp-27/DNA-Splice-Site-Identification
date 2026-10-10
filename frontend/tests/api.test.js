import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { ApiError, DEFAULT_FILTERS, LatestRequest, exportQuery, filterSites, request, sampleFromRun } from '../src/lib/api.js';

test('new input invalidates a late response even when transport ignores abort', async () => {
  const gate = new LatestRequest();
  const old = gate.begin();
  let complete;
  const delayed = new Promise((resolve) => { complete = resolve; });
  const received = delayed.then(() => old.isCurrent() ? 'old run' : 'ignored');
  const next = gate.begin();
  assert.equal(old.signal.aborted, true);
  complete();
  assert.equal(await received, 'ignored');
  assert.equal(next.isCurrent(), true);
  gate.cancel();
  assert.equal(next.isCurrent(), false);
});

test('network failures and server failures produce readable errors without sample fallback', async (context) => {
  context.mock.method(globalThis, 'fetch', async () => { throw new TypeError('connection refused'); });
  await assert.rejects(request('/analyses'), /local analysis service is unavailable/);
  context.mock.restoreAll();
  context.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({ error: { code: 'model_unavailable', message: 'Saved model missing.' } }), { status: 503 }));
  await assert.rejects(request('/analyses'), (error) => error instanceof ApiError && error.code === 'model_unavailable' && error.message === 'Saved model missing.');
});

test('aborting a request stays distinct from a service failure', async (context) => {
  context.mock.method(globalThis, 'fetch', async () => { throw new DOMException('aborted', 'AbortError'); });
  await assert.rejects(request('/runs'), (error) => error.name === 'AbortError');
});

test('download availability checks accept HEAD without parsing an empty body', async (context) => {
  let sent;
  context.mock.method(globalThis, 'fetch', async (url, options) => {
    sent = { url, options };
    return new Response(null, { status: 200, headers: { 'Content-Disposition': 'attachment; filename="run.csv"' } });
  });
  assert.equal(await request('/runs/saved/export?format=csv', { method: 'HEAD' }), null);
  assert.equal(sent.options.method, 'HEAD');
  assert.equal(sent.options.body, undefined);
});

test('analysis POST retains the request identity and no-threshold-override contract', async (context) => {
  let sent;
  context.mock.method(globalThis, 'fetch', async (url, options) => { sent = { url, options }; return new Response(JSON.stringify({ id: 'saved' })); });
  assert.deepEqual(await request('/analyses', { method: 'POST', body: { sequence: 'ACGT'.repeat(30), method: 'adaptive', client_request_id: 'new-input' } }), { id: 'saved' });
  assert.equal(sent.url, '/api/analyses');
  assert.equal(sent.options.headers['Content-Type'], 'application/json');
  assert.equal(JSON.parse(sent.options.body).client_request_id, 'new-input');
  assert.equal(Object.hasOwn(JSON.parse(sent.options.body), 'threshold'), false);
});

test('all exports omit filters and filtered exports explicitly include search/type/score/decision', () => {
  const filters = { type: 'Acceptor', minScore: .4, predictedOnly: true, query: ' C-108 ' };
  assert.equal(exportQuery('json', 'all', filters), 'format=json&scope=all');
  const query = new URLSearchParams(exportQuery('csv', 'filtered', filters));
  assert.equal(query.get('type'), 'acceptor');
  assert.equal(query.get('min_score'), '0.4');
  assert.equal(query.get('query'), 'C-108');
  assert.equal(query.get('predicted_only'), 'true');
});

test('real run adapter keeps coordinates, scorer, routes and annotation provenance', () => {
  const demos = JSON.parse(fs.readFileSync(new URL('../../data/processed/demo_samples.json', import.meta.url)));
  const demo = demos[2];
  const annotation = demo.annotations[0];
  const run = { input_sequence: demo.sequence, input_provenance: demo,
    analysis: { input: { name: demo.name }, candidates: [{ id: `C-${annotation.position1}`, position1: annotation.position1, type: annotation.type,
      motif: annotation.type === 'donor' ? 'GT' : 'AG', score: null, scorer: null, route: 'unscored', unavailable_reason: 'sequence_edge', predicted: false }] } };
  const sample = sampleFromRun(run);
  const site = sample.sites[0];
  assert.equal(sample.sample_id, demo.id);
  assert.equal(sample.sequence.slice(site.position - 1, site.position + 1), site.motif);
  assert.equal(site.route, 'unscored');
  assert.equal(site.score, null);
  assert.equal(site.unavailable_reason, 'sequence_edge');
});

test('score filtering excludes unavailable scores without changing original decisions', () => {
  const sites = [{ id: 'C-1', position: 1, type: 'Donor', motif: 'GT', score: null, predicted: false },
    { id: 'C-102', position: 102, type: 'Acceptor', motif: 'AG', score: .5, predicted: true },
    { id: 'C-120', position: 120, type: 'Acceptor', motif: 'AG', score: .3, predicted: false }];
  const saved = structuredClone(sites);
  assert.equal(filterSites(sites, DEFAULT_FILTERS).length, 3);
  assert.deepEqual(filterSites(sites, { ...DEFAULT_FILTERS, minScore: 0 }).map((site) => site.id), ['C-102', 'C-120']);
  assert.deepEqual(filterSites(sites, { ...DEFAULT_FILTERS, type: 'Acceptor', query: '102', predictedOnly: true }), [sites[1]]);
  assert.deepEqual(sites, saved);
});
