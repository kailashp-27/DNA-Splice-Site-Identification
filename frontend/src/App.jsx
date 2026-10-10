import { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowDownToLine, ArrowUpRight, BookOpen, ChartNoAxesCombined, CheckCheck, ChevronRight, Dna, Files, FlaskConical, LoaderCircle, Plus, ShieldCheck, Target, X } from 'lucide-react';
import { NAV_ITEMS } from './data.js';
import { inspectSequence, scanMotifs } from './lib/analysis.js';
import { DEFAULT_FILTERS, METHOD_NAMES, exportQuery, exportUrl, request } from './lib/api.js';
import { Accuracy, Algorithms, Guide, NewAnalysis, Quality, Reports } from './pages.jsx';
import { InputActions, InputBar, SequenceWorkspace, Workflow } from './workspace.jsx';
import { Empty, Note } from './components.jsx';
import { useWorkspace } from './useWorkspace.js';

const icons = { Dna, ChartNoAxesCombined, Target, Files };
const titles = { analysis: 'Analyse DNA', quality: 'Check input', algorithms: 'Compare methods', accuracy: 'Model validation', reports: 'Saved runs & exports', guide: 'Help & methods' };
const subtitles = { analysis: 'Find possible GT / AG splice boundaries.', quality: 'Review bases and input limits.', algorithms: 'Measured runtime, work, quality, and estimated energy.', accuracy: 'Results on independent labelled test data.', reports: 'Reopen, rename, download, or print.', guide: 'A quick start, with details when you need them.' };
const labels = { analysis: 'Analyse', quality: 'Analyse', algorithms: 'Compare', accuracy: 'Validate', reports: 'Reports', guide: 'Help & methods' };
const EMPTY_SAMPLE = { id: 'EMPTY', name: 'No sequence loaded', sequence: '', sites: [], source: 'Local workspace' };

export default function App() {
  const workspace = useWorkspace();
  const { service, draft, run, busy, error } = workspace;
  const [view, setView] = useState('analysis');
  const [selectedId, setSelectedId] = useState('');
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [method, setMethod] = useState('filtered');
  const [power, setPower] = useState(15);
  const [name, setName] = useState('');
  const [modal, setModal] = useState(null);
  const [toast, setToast] = useState('');
  const [exportBusy, setExportBusy] = useState(false);
  const sample = draft || EMPTY_SAMPLE;
  const quality = useMemo(() => inspectSequence(sample.sequence), [sample.sequence]);
  const rawMotifs = useMemo(() => quality.canAnalyze ? scanMotifs(sample.sequence) : [], [sample.sequence, quality.canAnalyze]);
  const isAnalysis = view === 'analysis' || view === 'quality';
  const activeNav = view === 'quality' ? 'analysis' : view;
  const canStart = !!draft && quality.canAnalyze && !busy && service.status === 'ready';

  useEffect(() => {
    setFilters(DEFAULT_FILTERS);
    setSelectedId(run?.analysis.candidates.find((site) => site.predicted)?.id || '');
  }, [run?.id, sample.sequence]);
  useEffect(() => { setName(draft?.name?.slice(0, 120) || ''); }, [draft?.sequence]);
  useEffect(() => {
    if (!run) return;
    setName(run.name); setMethod(run.analysis.method); setPower(run.energy.assumed_power_watts);
  }, [run?.id, run?.name, run?.analysis.method, run?.energy.assumed_power_watts]);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(''), 5000);
    return () => clearTimeout(timer);
  }, [toast]);
  useEffect(() => { document.title = `EcoSplice · ${labels[view]}`; window.scrollTo({ top: 0, behavior: 'instant' }); }, [view]);

  const openInput = (mode = 'sample') => setModal(mode === true ? 'sample' : mode);
  const closeInput = useCallback(() => { if (busy === 'input') workspace.cancel(); setModal(null); }, [busy, workspace.cancel]);
  const load = async (next) => {
    if (await workspace.loadInput(next)) {
      setModal(null); setView('analysis'); setToast('Sequence loaded. Ready to analyse.');
      return true;
    }
    return false;
  };
  const reopen = async (id) => {
    if (await workspace.openRun(id)) { setView('analysis'); setToast('Saved run reopened.'); }
  };
  const start = () => workspace.startAnalysis({ method, assumed_power_watts: power, ...(name.trim() ? { name: name.trim() } : {}) });
  const download = async (format, scope = 'all') => {
    if (!run || exportBusy) return;
    const originalId = run.id;
    setExportBusy(true); workspace.setError('');
    try {
      const path = `/runs/${encodeURIComponent(originalId)}/export?${exportQuery(format, scope, filters)}`;
      // Check availability before asking the browser to stream the attachment.
      // HTTP downloads also work in browsers that restrict blob URLs.
      await request(path, { method: 'HEAD' });
      const anchor = document.createElement('a');
      anchor.href = exportUrl(originalId, format, scope, filters); anchor.download = `ecosplice-${originalId}-${scope}.${format}`;
      document.body.appendChild(anchor); anchor.click(); anchor.remove();
      setToast(`${scope === 'all' ? 'All candidates' : 'Filtered candidates'} download requested from the saved run.`);
    } catch (problem) { workspace.setError(problem.message); }
    finally { setExportBusy(false); }
  };
  const common = { sample, run, quality, rawMotifs, filters, setFilters, selectedId,
    inspect: (site) => setSelectedId(site.id), setView, openInput, download, exportBusy };

  return <div className="app-shell redesigned">
    <aside className="sidebar">
      <button className="brand" onClick={() => setView('analysis')} aria-label="EcoSplice analysis workspace"><span className="brand-mark"><Dna size={27} strokeWidth={1.6} /></span><span>Eco<span className="brand-light">Splice</span><small>LOCAL DNA ANALYSIS</small></span></button>
      <span className="nav-label">ANALYSIS</span>
      <nav aria-label="Main navigation">{NAV_ITEMS.map((item, index) => { const Icon = icons[item.icon]; return <button key={item.id} className={`nav-item ${activeNav === item.id ? 'active' : ''}`} onClick={() => setView(item.id)} aria-current={activeNav === item.id ? 'page' : undefined}><Icon size={20} strokeWidth={1.6} /><span>{item.label}</span><small>{String(index + 1).padStart(2, '0')}</small></button>; })}</nav>
      <div className="sidebar-sample"><span className="eyebrow">CURRENT SEQUENCE</span><div><span className="status-dot" /><strong>{sample.name}</strong></div><p className="mono">{sample.sequence.length.toLocaleString()} bp</p><span>{run ? 'Saved locally' : draft ? 'Ready for analysis' : 'Load DNA to begin'}</span></div>
      <div className="sidebar-bottom"><button className={`help-link ${view === 'guide' ? 'active' : ''}`} onClick={() => setView('guide')}><BookOpen size={18} />Help & methods <ArrowUpRight size={15} /></button></div>
    </aside>
    <div className="main-shell">
      <header className="topbar"><div className="breadcrumbs"><span className="lab-icon"><FlaskConical size={15} /></span>EcoSplice <ChevronRight size={13} /><span>{labels[view]}</span></div><button className="header-help" onClick={() => setView('guide')}><BookOpen size={15} />Help & methods</button></header>
      <main className={`main-content ${isAnalysis ? 'analysis-content' : ''}`}>
        <div className="page-heading"><div><div className="page-eyebrow"><span className="tiny-square" />{isAnalysis ? 'SEQUENCE ANALYSIS' : view === 'algorithms' ? 'ENERGY & ALGORITHMS' : view === 'accuracy' ? 'MODEL EVALUATION' : 'ECOSPLICE'}</div><h1>{titles[view]}</h1><p>{subtitles[view]}</p></div>{isAnalysis ? <InputActions openInput={openInput} /> : <div className="heading-actions">{view !== 'guide' && <button className="button secondary" disabled={!run || exportBusy} onClick={() => download('csv')}><ArrowDownToLine size={16} />Export all results</button>}<button className="button primary" onClick={() => openInput('sample')}><Plus size={16} />Load sequence</button></div>}</div>
        {service.status !== 'ready' || service.message ? <div className="service-state" role="status"><span>{service.status === 'checking' ? 'Connecting to the local analysis service…' : service.message}</span><button className="button secondary small" onClick={workspace.refreshService} disabled={service.status === 'checking'}>Retry connection</button></div> : null}
        {error && <div className="form-error" role="alert">{error}<button className="icon-button" aria-label="Dismiss error" onClick={() => workspace.setError('')}><X size={15} /></button></div>}
        {busy && <div className="service-state" role="status"><LoaderCircle size={17} className="spin" /><span>{busy === 'comparison' ? 'Measuring all three methods. Long sequences can take several seconds…' : busy === 'analysis' ? 'Scoring DNA and saving the completed run…' : busy === 'reopen' ? 'Reopening the saved run…' : 'Loading your sequence…'}</span><button className="button secondary small" onClick={workspace.cancel}>Stop waiting</button></div>}
        <Workflow draft={draft} quality={quality} run={run} ready={service.status === 'ready'} busy={busy} view={view} setView={setView} openInput={openInput} />
        {isAnalysis && draft && <><InputBar sample={sample} quality={quality} runId={run?.id} samples={service.samples} load={load} openInput={openInput} /><div className="run-controls"><label>Method<select aria-label="Analysis method" value={method} onChange={(event) => setMethod(event.target.value)}>{Object.entries(METHOD_NAMES).map(([id, title]) => <option key={id} value={id}>{title}</option>)}</select></label><label>Run name<input aria-label="Run name" value={name} maxLength={120} onChange={(event) => setName(event.target.value)} /></label><label>Assumed power (W)<input aria-label="Analysis assumed power in watts" type="number" min="0" max="500" step="0.1" value={power} onChange={(event) => setPower(Math.max(0, Math.min(500, Number(event.target.value))))} /></label><button className="button primary" disabled={!canStart} onClick={start}>{busy === 'analysis' ? <LoaderCircle size={17} className="spin" /> : <FlaskConical size={17} />}{run ? 'Analyse as new run' : 'Run analysis'}</button></div><div className="analysis-tabs" role="tablist" aria-label="Analysis view"><button role="tab" aria-selected={view === 'analysis'} className={view === 'analysis' ? 'active' : ''} onClick={() => setView('analysis')}><Dna size={17} />Sequence explorer<span>{sample.sites.length}</span></button><button role="tab" aria-selected={view === 'quality'} className={view === 'quality' ? 'active' : ''} onClick={() => setView('quality')}><ShieldCheck size={17} />Data quality{quality.canAnalyze ? <CheckCheck size={14} /> : null}</button><button className="analysis-export" disabled={!run || exportBusy} onClick={() => download('csv')}><ArrowDownToLine size={15} />Export all candidates</button></div></>}
        {view === 'analysis' && (run ? <SequenceWorkspace key={run.id} {...common} /> : <Empty title={draft ? 'Ready to analyse' : 'Load a sequence to begin'} description={draft ? 'Choose Run analysis. Results save automatically.' : 'Try a sample or upload a FASTA file.'}>{draft ? <button className="button primary" disabled={!canStart} onClick={start}>Run analysis</button> : <button className="button primary" onClick={() => openInput('sample')}>Try a real sample</button>}</Empty>)}
        {view === 'quality' && (draft ? <Quality {...common} /> : <Empty title="No input loaded" description="Load a sequence to review its base composition." />)}
        {view === 'accuracy' && <Accuracy run={run} />}
        {view === 'algorithms' && <Algorithms {...common} comparing={busy === 'comparison'} compareRun={workspace.compareRun} canCompare={!!run && !busy && service.status === 'ready'} />}
        {view === 'reports' && <Reports {...common} reopen={reopen} updateRunName={workspace.updateRunName} clearRun={workspace.clearRun} notify={setToast} printUrl={(scope) => run ? exportUrl(run.id, 'html', scope, filters) : ''} />}
        {view === 'guide' && <Guide openInput={openInput} setView={setView} run={run} />}
        {run && isAnalysis && <Note>{METHOD_NAMES[run.analysis.method]} · {run.analysis.model_id} · saved at {new Date(run.created_at).toLocaleString()}. Control changes apply to a new run.</Note>}
        <footer className="page-footer"><span><Dna size={15} />EcoSplice · DNA splice site analysis</span><span><span className="status-dot" />{run ? 'Real predictions · local saved run' : service.status === 'ready' ? 'Local service ready' : 'Local service needs attention'}</span></footer>
      </main>
    </div>
    {modal && <NewAnalysis onClose={closeInput} onLoad={load} currentId={sample.id} initialMode={modal} samples={service.samples} />}
    {toast && <div className="toast" role="status"><CheckCheck size={18} />{toast}<button className="icon-button" aria-label="Dismiss notification" onClick={() => setToast('')}><X size={15} /></button></div>}
  </div>;
}
