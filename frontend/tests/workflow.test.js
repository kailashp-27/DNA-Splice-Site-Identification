import test from 'node:test';
import assert from 'node:assert/strict';
import { workflowState } from '../src/lib/workflow.js';

test('guide unlocks completed work and restores a saved comparison', () => {
  const empty = workflowState({ loaded: false, valid: false, ready: true });
  assert.deepEqual(empty.completed, [false, false, false, false]);
  assert.deepEqual(empty.disabled, [false, true, true, true]);
  const input = workflowState({ loaded: true, valid: true, ready: true });
  assert.match(input.hint, /Run analysis/);
  assert.deepEqual(input.completed, [true, false, false, false]);
  const reopened = workflowState({ loaded: true, valid: true, run: { comparison: {} }, ready: false });
  assert.deepEqual(reopened.completed, [true, true, true, false]);
  assert.equal(reopened.disabled[3], false);
  assert.match(reopened.hint, /Reports/);
});

test('invalid DNA, offline service and pending work give actionable guidance', () => {
  assert.match(workflowState({ loaded: true, valid: false }).hint, /Check your input/);
  assert.match(workflowState({ loaded: true, valid: true, ready: false }).hint, /Reconnect/);
  const pending = workflowState({ loaded: true, valid: true, run: {}, busy: 'comparison' });
  assert.equal(pending.disabled[2], true);
  assert.equal(pending.completed[2], false);
  assert.match(pending.hint, /Working/);
});
