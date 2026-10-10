import { useCallback, useEffect, useState } from 'react';
import { LatestRequest, request, sampleFromRun } from './lib/api.js';

export function useWorkspace() {
  const [service, setService] = useState({ status: 'checking', samples: [], message: '' });
  const [draft, setDraft] = useState(null);
  const [run, setRun] = useState(null);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState('');
  const [serviceGate] = useState(() => new LatestRequest());
  const [workGate] = useState(() => new LatestRequest());

  const refreshService = useCallback(async () => {
    const ticket = serviceGate.begin();
    setService((previous) => ({ ...previous, status: 'checking', message: '' }));
    const [health, samples] = await Promise.allSettled([
      request('/health', { signal: ticket.signal }), request('/samples', { signal: ticket.signal }),
    ]);
    if (!ticket.isCurrent()) return;
    if (health.status === 'rejected') {
      setService({ status: 'offline', samples: [], message: health.reason.message });
    } else {
      const flags = health.value;
      setService({ status: flags.status, health: flags, samples: samples.status === 'fulfilled' ? samples.value.samples : [],
        message: !flags.model_ready ? 'The saved prediction model is unavailable. Saved runs can still be reopened.'
          : !flags.history_ready ? 'Local history is unavailable. Check the backend terminal and restart it.'
            : samples.status === 'rejected' ? samples.reason.message : '' });
    }
  }, [serviceGate]);

  useEffect(() => {
    refreshService();
    return () => { serviceGate.cancel(); workGate.cancel(); };
  }, [refreshService, serviceGate, workGate]);

  const cancel = useCallback(() => { workGate.cancel(); setBusy(null); }, [workGate]);
  const activateRun = useCallback((next) => { setRun(next); setDraft(sampleFromRun(next)); }, []);
  const updateRunName = useCallback((id, name, updatedAt) => {
    setRun((previous) => previous?.id === id ? { ...previous, name, updated_at: previous.updated_at > updatedAt ? previous.updated_at : updatedAt } : previous);
  }, []);
  const recordProblem = (ticket, problem) => {
    if (!ticket.isCurrent() || problem.name === 'AbortError') return;
    setError(problem.message);
    if (problem.code === 'service_unavailable') refreshService();
  };

  const loadInput = async (input) => {
    const ticket = workGate.begin();
    setBusy('input'); setError(''); setRun(null);
    try {
      let next = input;
      if (input.sample_id) {
        const sample = await request(`/samples/${encodeURIComponent(input.sample_id)}`, { signal: ticket.signal });
        next = { id: sample.id, name: sample.name, sequence: sample.sequence, source: sample.source,
          builtIn: true, sample_id: sample.id, sites: [] };
      }
      if (!ticket.isCurrent()) return false;
      setDraft(next);
      return true;
    } catch (problem) {
      recordProblem(ticket, problem);
      return false;
    } finally { if (ticket.isCurrent()) setBusy(null); }
  };

  const startAnalysis = async (options) => {
    if (!draft) return;
    const ticket = workGate.begin();
    const correlation = `${Date.now()}-${ticket.id}`;
    setBusy('analysis'); setError(''); setRun(null);
    try {
      const next = await request('/analyses', { method: 'POST', signal: ticket.signal,
        body: { ...(draft.sample_id ? { sample_id: draft.sample_id } : { sequence: draft.raw || draft.sequence }),
          ...options, client_request_id: correlation } });
      if (!ticket.isCurrent()) return;
      if (next.client_request_id !== correlation) throw new Error('Analysis response could not be matched to this request. Reopen it from saved history.');
      activateRun(next);
    } catch (problem) {
      recordProblem(ticket, problem);
    } finally { if (ticket.isCurrent()) setBusy(null); }
  };

  const openRun = async (id) => {
    const ticket = workGate.begin();
    setBusy('reopen'); setError(''); setRun(null); setDraft(null);
    try {
      const next = await request(`/runs/${encodeURIComponent(id)}`, { signal: ticket.signal });
      if (ticket.isCurrent()) { activateRun(next); return true; }
    } catch (problem) {
      recordProblem(ticket, problem);
    } finally { if (ticket.isCurrent()) setBusy(null); }
    return false;
  };

  const compareRun = async (repeats) => {
    if (!run) return;
    const ticket = workGate.begin();
    setBusy('comparison'); setError('');
    try {
      const next = await request(`/runs/${encodeURIComponent(run.id)}/comparison`, { method: 'POST', body: { repeats }, signal: ticket.signal });
      if (ticket.isCurrent()) activateRun(next);
    } catch (problem) {
      recordProblem(ticket, problem);
    } finally { if (ticket.isCurrent()) setBusy(null); }
  };

  return { service, draft, run, busy, error, setError, loadInput, startAnalysis, openRun, compareRun,
    cancel, refreshService, updateRunName, clearRun: () => { cancel(); setRun(null); setDraft(null); } };
}

export function useResource(path) {
  const [resource, setResource] = useState({ data: null, error: '', busy: true });
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setResource({ data: null, error: '', busy: true });
    request(path, { signal: controller.signal }).then((data) => {
      if (active) setResource({ data, error: '', busy: false });
    }).catch((problem) => {
      if (active && problem.name !== 'AbortError') setResource({ data: null, error: problem.message, busy: false });
    });
    return () => { active = false; controller.abort(); };
  }, [path, revision]);
  return { ...resource, retry: () => setRevision((previous) => previous + 1) };
}
