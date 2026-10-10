import { useRef, useState } from 'react';
import { ArrowUpRight, Download, FileJson, FileText, Printer } from 'lucide-react';
import { Badge, Empty, Note, Panel, ResourceState } from './components.jsx';
import { filterSites, METHOD_NAMES, request } from './lib/api.js';
import { useResource } from './useWorkspace.js';

export function Reports({ run, sample, filters, download, exportBusy, reopen, updateRunName, clearRun, notify, printUrl }) {
  const [page, setPage] = useState(0);
  const [scope, setScope] = useState('all');
  const [rename, setRename] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState('');
  const [actionBusy, setActionBusy] = useState('');
  const [actionError, setActionError] = useState('');
  const currentId = useRef(run?.id);
  currentId.current = run?.id;
  const history = useResource(`/runs?limit=10&offset=${page * 10}`);
  const selectedCount = run ? scope === 'all' ? sample.sites.length : filterSites(sample.sites, filters).length : 0;
  const saveName = async () => {
    setActionBusy(rename.id); setActionError('');
    try {
      const updated = await request(`/runs/${encodeURIComponent(rename.id)}`, { method: 'PATCH', body: { name: rename.name.trim() } });
      updateRunName(updated.id, updated.name, updated.updated_at);
      setRename(null); history.retry(); notify('Run renamed.');
    } catch (problem) { setActionError(problem.message); }
    finally { setActionBusy(''); }
  };
  const deleteRun = async (id) => {
    setActionBusy(id); setActionError('');
    try {
      await request(`/runs/${encodeURIComponent(id)}`, { method: 'DELETE' });
      if (currentId.current === id) clearRun();
      setConfirmDelete('');
      if (history.data.runs.length === 1 && page > 0) setPage(page - 1); else history.retry();
      notify('Run deleted. Downloads are kept.');
    } catch (problem) { setActionError(problem.message); }
    finally { setActionBusy(''); }
  };
  return <>
    <Panel title="Export the active saved run" eyebrow={run?.name || 'REOPEN A RUN BELOW'}><div className="selection-controls"><label>Export scope<select aria-label="Report export scope" value={scope} onChange={(event) => setScope(event.target.value)}><option value="all">All candidates</option><option value="filtered">Filtered candidates</option></select></label><span className="small-muted">{selectedCount.toLocaleString()} candidate rows · saved settings and measurements</span></div>{scope === 'filtered' && <p className="panel-description">Current explorer filters: {filters.type}, minimum score {filters.minScore ?? 'any'}, {filters.predictedOnly ? 'predicted boundaries only' : 'all decisions'}, search “{filters.query || 'none'}”. Filters change rows, not prediction decisions, measurements or accuracy.</p>}</Panel>
    <div className="report-cards"><button className="export-card" disabled={!run || exportBusy} onClick={() => download('csv', scope)}><span className="export-icon"><FileText size={27} /></span><Badge tone="neutral">CSV</Badge><h2>Candidate results</h2><p>Candidate scores, routes, and settings.</p><span className="export-action">Download CSV <Download size={17} /></span></button><button className="export-card" disabled={!run || exportBusy} onClick={() => download('json', scope)}><span className="export-icon purple"><FileJson size={27} /></span><Badge tone="neutral">JSON</Badge><h2>Complete run record</h2><p>DNA, predictions, settings, and comparison.</p><span className="export-action">Download JSON <Download size={17} /></span></button>{run ? <a className="export-card" href={printUrl(scope)} target="_blank" rel="noreferrer"><span className="export-icon amber"><Printer size={27} /></span><Badge tone="neutral">PRINT / PDF</Badge><h2>Readable report</h2><p>Print or save as PDF. Same export scope.</p><span className="export-action">Open print report <ArrowUpRight size={17} /></span></a> : <button className="export-card" disabled><span className="export-icon amber"><Printer size={27} /></span><h2>Readable report</h2><p>Reopen or analyse a run first.</p></button>}</div>
    {run && <details className="provenance-details"><summary>Run settings & provenance</summary><Panel title="Active run provenance" eyebrow={run.id} action={<Badge tone="green">Saved in SQLite</Badge>}><div className="provenance-grid"><div><span>Run name</span><strong>{run.name}</strong></div><div><span>Created</span><strong>{new Date(run.created_at).toLocaleString()}</strong></div><div><span>Input source</span><strong>{run.input_provenance.source}</strong></div><div><span>Sequence / candidates</span><strong>{run.analysis.input.length.toLocaleString()} bases / {run.analysis.candidates.length.toLocaleString()}</strong></div><div><span>Model / method</span><strong>{run.analysis.model_id}<br />{METHOD_NAMES[run.analysis.method]}</strong></div><div><span>Power assumption / estimated energy</span><strong>{run.energy.assumed_power_watts} W / {run.energy.estimated_joules.toPrecision(4)} J</strong></div><div><span>Coordinates</span><strong>{run.analysis.coordinate_convention}</strong></div><div><span>Repeated comparison</span><strong>{run.comparison ? `${run.comparison.repeats} trials per method, saved ${new Date(run.comparison.created_at).toLocaleString()}` : 'Not measured for this run'}</strong></div></div><Note>Exports derive from this run's saved model/settings, including any attached comparison. Changing analysis controls does not rewrite it. Scores are not calibrated probabilities; energy is estimated from measured computation.</Note><details className="provenance-details"><summary>Input and model fingerprints</summary><p className="mono">Input SHA-256: {run.analysis.input.sha256}<br />Dataset: {run.analysis.dataset_fingerprint}<br />Model manifest SHA-256: {run.measurement.model_manifest_sha256}</p></details></Panel></details>}
    <Panel title="Saved runs" eyebrow="SURVIVES RESTART" action={<button className="button secondary small" disabled={history.busy} onClick={history.retry}>Refresh history</button>}><ResourceState {...history} />{actionError && <div className="form-error" role="alert">{actionError}</div>}{history.data && (history.data.runs.length ? <><div className="history-list">{history.data.runs.map((item) => <article key={item.id} className={`history-row ${item.id === run?.id ? 'active' : ''}`}><div className="history-identity">{rename?.id === item.id ? <label>Run name<input aria-label="Rename saved run" maxLength={120} value={rename.name} onChange={(event) => setRename({ ...rename, name: event.target.value })} /></label> : <><strong>{item.name}</strong><span>{new Date(item.created_at).toLocaleString()} · {item.input.length.toLocaleString()} bases · {METHOD_NAMES[item.method]}</span><small className="mono">{item.model_id} · {item.id.slice(0, 8)}</small></>}</div><div className="history-actions">{rename?.id === item.id ? <><button className="button primary small" disabled={!!actionBusy || !rename.name.trim()} onClick={saveName}>Save name</button><button className="button secondary small" onClick={() => setRename(null)}>Cancel</button></> : confirmDelete === item.id ? <><button className="button secondary small" disabled={!!actionBusy} onClick={() => deleteRun(item.id)}>Confirm delete</button><button className="button secondary small" onClick={() => setConfirmDelete('')}>Cancel</button></> : <><button className="button primary small" disabled={!!actionBusy} onClick={() => reopen(item.id)}>Reopen</button><button className="button secondary small" disabled={!!actionBusy} onClick={() => { setRename({ id: item.id, name: item.name }); setConfirmDelete(''); }}>Rename</button><button className="button secondary small" disabled={!!actionBusy} onClick={() => { setConfirmDelete(item.id); setRename(null); }}>Delete</button></>}</div></article>)}</div><div className="table-footer"><span>{history.data.total.toLocaleString()} saved runs</span><div className="pagination"><button className="button secondary small" disabled={!page} onClick={() => setPage(page - 1)}>Previous</button><span>{page + 1} / {Math.max(1, Math.ceil(history.data.total / 10))}</span><button className="button secondary small" disabled={(page + 1) * 10 >= history.data.total} onClick={() => setPage(page + 1)}>Next</button></div></div></> : <Empty title="No saved runs yet" description="Completed runs save automatically and survive restart." />)}</Panel>
  </>;
}
