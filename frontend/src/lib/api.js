const base = (import.meta.env?.VITE_API_BASE || '').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(message, code = 'service_unavailable') { super(message); this.code = code; }
}

export async function request(path, { body, signal, method = 'GET' } = {}) {
  let response;
  try {
    response = await fetch(`${base}/api${path}`, {
      method, signal, ...(body === undefined ? {} : { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError('The local analysis service is unavailable. Start the backend and retry.');
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const problem = payload?.error;
    const detail = problem?.details?.map((item) => `${item.field.replace(/^body\./, '')}: ${item.message}`).join(' ');
    throw new ApiError(problem ? `${problem.message}${detail ? ` ${detail}` : ''}` : 'The local analysis service did not respond correctly. Check that the backend is running.', problem?.code);
  }
  if (response.status === 204 || method === 'HEAD') return null;
  try { return await response.json(); }
  catch { throw new ApiError('The local service returned an unreadable response. Retry the request.'); }
}

// Abort reduces unnecessary transfer; the generation check also rejects late
// responses from a server/mock that already completed or ignores cancellation.
export class LatestRequest {
  generation = 0;
  controller = null;
  cancel() { this.generation++; this.controller?.abort(); this.controller = null; }
  begin() {
    this.cancel();
    const id = this.generation;
    this.controller = new AbortController();
    return { id, signal: this.controller.signal, isCurrent: () => id === this.generation };
  }
}

export function exportQuery(format, scope, filters) {
  const query = new URLSearchParams({ format, scope });
  if (scope === 'filtered') {
    if (filters.type !== 'All') query.set('type', filters.type.toLowerCase());
    if (filters.minScore != null) query.set('min_score', String(filters.minScore));
    if (filters.predictedOnly) query.set('predicted_only', 'true');
    if (filters.query.trim()) query.set('query', filters.query.trim());
  }
  return query.toString();
}

export const exportUrl = (id, format, scope, filters) => `${base}/api/runs/${encodeURIComponent(id)}/export?${exportQuery(format, scope, filters)}`;
export const sampleFastaUrl = (id = 'REAL-003') => `${base}/api/samples/${encodeURIComponent(id)}/fasta`;

export function sampleFromRun(run) {
  return { id: run.input_provenance.id || 'CUSTOM', name: run.analysis.input.name, sequence: run.input_sequence,
    source: run.input_provenance.source, builtIn: !!run.input_provenance.id, sample_id: run.input_provenance.id,
    sites: run.analysis.candidates.map((site) => ({ ...site, position: site.position1, type: site.type === 'donor' ? 'Donor' : 'Acceptor' })) };
}

export function filterSites(sites, filters) {
  const query = filters.query.trim().toLowerCase();
  return sites.filter((site) => (filters.type === 'All' || site.type === filters.type)
    && (filters.minScore == null || (site.score != null && site.score >= filters.minScore))
    && (!filters.predictedOnly || site.predicted)
    && `${site.id} ${site.position} ${site.motif} ${site.type}`.toLowerCase().includes(query));
}

export const DEFAULT_FILTERS = { type: 'All', minScore: null, query: '', predictedOnly: false };
export const METHOD_NAMES = { exhaustive: 'Exhaustive baseline', filtered: 'Candidate filtering', adaptive: 'Adaptive processing' };
export const ROUTE_NAMES = { fast: 'Fast path', detailed: 'Detailed path', unscored: 'Unscored' };
