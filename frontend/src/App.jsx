import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowDownToLine, ArrowUpRight, BookOpen, ChartNoAxesCombined, CheckCheck, ChevronRight, Dna, Files, FlaskConical, Leaf, Plus, ShieldCheck, Target, X } from 'lucide-react';
import { NAV_ITEMS, SAMPLES } from './data.js';
import { csvForSites, energyEstimate, inspectSequence, scanMotifs } from './lib/analysis.js';
import { Accuracy, Algorithms, Guide, NewAnalysis, Quality, Reports } from './pages.jsx';
import { InputActions, InputBar, SequenceWorkspace, Workflow } from './workspace.jsx';

const icons = { Dna, ChartNoAxesCombined, Target, Files };
const titles = { analysis: 'Explore your sequence.', quality: 'Start with good input.', algorithms: 'Compare analysis methods.', accuracy: 'Put predictions to the test.', reports: 'Keep a record of your findings.', guide: 'Understand every step.' };
const subtitles = { analysis: 'Follow the bases, find a candidate, and inspect its surrounding DNA.', quality: 'Check the alphabet, base composition, and unknown characters in your DNA.', algorithms: 'See how candidate filtering changes the work, runtime, and estimated energy.', accuracy: 'Explore precision, recall, and the effect of changing a demonstration score threshold.', reports: 'Export candidates, assumptions, and the details behind this analysis.', guide: 'Understand splice boundaries, analysis methods, and how to read your results.' };
const labels = { analysis: 'Analyse', quality: 'Analyse', algorithms: 'Compare', accuracy: 'Validate', reports: 'Reports', guide: 'Help & methods' };

export default function App() {
  const [view, setView] = useState('analysis');
  const [sample, setSample] = useState(SAMPLES[0]);
  const [selectedId, setSelectedId] = useState(SAMPLES[0].sites[0].id);
  const [threshold, setThreshold] = useState(0.7);
  const [power, setPower] = useState(8);
  const [carbon, setCarbon] = useState(0.7);
  const [modal, setModal] = useState(null);
  const [toast, setToast] = useState('');
  const [downloads, setDownloads] = useState([]);
  const [runTime, setRunTime] = useState(new Date());
  const [runId, setRunId] = useState('RUN-001');
  const runCounter = useRef(1);
  const quality = useMemo(() => inspectSequence(sample.sequence), [sample]);
  const rawMotifs = useMemo(() => quality.canAnalyze ? scanMotifs(sample.sequence) : [], [sample, quality.canAnalyze]);
  const baseline = sample.benchmark?.baselineMs;
  const optimized = sample.benchmark?.optimizedMs;
  const saved = baseline ? 1 - optimized / baseline : 0;
  const energy = optimized != null ? energyEstimate(optimized, power) : null;
  const isAnalysis = view === 'analysis' || view === 'quality';
  const activeNav = view === 'quality' ? 'analysis' : view;

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(''), 4000);
    return () => clearTimeout(timer);
  }, [toast]);
  useEffect(() => {
    document.title = `EcoSplice · ${labels[view]}`;
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [view]);

  const openInput = (mode = 'sample') => setModal(mode === true ? 'sample' : mode);
  const inspect = (site) => setSelectedId(site.id);
  const load = (next) => {
    runCounter.current += 1;
    setRunId(`RUN-${String(runCounter.current).padStart(3, '0')}`);
    setSample(next); setSelectedId(next.sites[0]?.id || ''); setRunTime(new Date()); setModal(null);
    setView(inspectSequence(next.sequence).canAnalyze ? 'analysis' : 'quality');
    setToast(`${next.name} loaded.`);
  };
  const report = () => ({
    project: 'EcoSplice', runId, generatedAt: new Date().toISOString(), sequenceName: sample.name, source: sample.source,
    coordinateConvention: '1-based position of the first base of the GT or AG motif; sample coordinates only',
    quality: { length: quality.length, baseCounts: quality.counts, gcPercent: quality.gc, invalidSymbols: quality.invalid, canAnalyze: quality.canAnalyze },
    candidates: sample.sites, scoreThreshold: threshold,
    scoreSource: sample.builtIn ? 'Constructed demonstration scores; no trained model or biological ground truth' : 'Canonical motif scan only; no prediction scores',
    benchmark: sample.benchmark ? { ...sample.benchmark, source: 'Hardcoded illustrative runtime snapshot; not a measurement', assumedPowerWatts: power, estimatedOptimizedEnergyJ: energy, assumedCarbonKgPerKWh: carbon, estimatedOptimizedCarbonGrams: energy / 3600000 * carbon * 1000 } : null,
    scope: 'Forward sequence, canonical GT/AG motifs. No strand, transcript, variant-effect or clinical interpretation.',
  });
  const download = (kind) => {
    const name = `ecosplice-${runId.toLowerCase()}.${kind}`;
    const content = kind === 'csv' ? csvForSites(sample.sites, sample.name) : JSON.stringify(report(), null, 2);
    const blob = new Blob([content], { type: kind === 'csv' ? 'text/csv;charset=utf-8' : 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url; anchor.download = name;
    document.body.appendChild(anchor); anchor.click(); anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    setDownloads((previous) => [{ name, format: kind.toUpperCase(), time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }), sample: sample.name, size: blob.size }, ...previous].slice(0, 20));
    setToast(`${name} download prepared.`);
  };
  const common = { sample, threshold, setThreshold, selectedId, inspect, quality, rawMotifs, setView, setModal: openInput, openInput, power, setPower, carbon, setCarbon, energy, baseline, optimized, saved, runTime, runId, download, downloads, report };

  return <div className="app-shell redesigned">
    <aside className="sidebar">
      <button className="brand" onClick={() => setView('analysis')} aria-label="EcoSplice analysis workspace"><span className="brand-mark"><Dna size={27} strokeWidth={1.6} /></span><span>Eco<span className="brand-light">Splice</span><small>THE SEQUENCE LAB</small></span></button>
      <span className="nav-label">ANALYSIS</span>
      <nav aria-label="Main navigation">{NAV_ITEMS.map((item, index) => { const Icon = icons[item.icon]; return <button key={item.id} className={`nav-item ${activeNav === item.id ? 'active' : ''}`} onClick={() => setView(item.id)} aria-current={activeNav === item.id ? 'page' : undefined}><Icon size={20} strokeWidth={1.6} /><span>{item.label}</span><small>{String(index + 1).padStart(2, '0')}</small></button>; })}</nav>
      <div className="sidebar-sample"><span className="eyebrow">CURRENT SAMPLE</span><div><span className="status-dot" /><strong>{sample.name}</strong></div><p className="mono">{sample.id} · {sample.sequence.length.toLocaleString()} bp</p><span>{sample.builtIn ? 'Synthetic educational data' : 'Loaded in this session'}</span></div>
      <div className="sidebar-bottom"><button className={`help-link ${view === 'guide' ? 'active' : ''}`} onClick={() => setView('guide')}><BookOpen size={18} />Help & methods <ArrowUpRight size={15} /></button></div>
    </aside>
    <div className="main-shell">
      <header className="topbar"><div className="breadcrumbs"><span className="lab-icon"><FlaskConical size={15} /></span>EcoSplice <ChevronRight size={13} /><span>{labels[view]}</span></div><button className="header-help" onClick={() => setView('guide')}><BookOpen size={15} />Help & methods</button></header>
      <main className={`main-content ${isAnalysis ? 'analysis-content' : ''}`}>
        <div className="page-heading"><div><div className="page-eyebrow"><span className="tiny-square" />{isAnalysis ? 'SEQUENCE ANALYSIS' : view === 'algorithms' ? 'ENERGY & ALGORITHMS' : view === 'accuracy' ? 'MODEL EVALUATION' : 'ECOSPLICE'}</div><h1>{titles[view]}</h1><p>{subtitles[view]}</p></div>{isAnalysis ? <InputActions openInput={openInput} /> : <div className="heading-actions">{view !== 'guide' && <button className="button secondary" onClick={() => download('csv')}><ArrowDownToLine size={16} />Export results</button>}<button className="button primary" onClick={() => openInput('sample')}><Plus size={16} />Load sequence</button></div>}</div>
        {isAnalysis && <><Workflow quality={quality} view={view} setView={setView} openInput={openInput} /><InputBar sample={sample} quality={quality} runId={runId} load={load} openInput={openInput} /><div className="analysis-tabs" role="tablist" aria-label="Analysis view"><button role="tab" aria-selected={view === 'analysis'} className={view === 'analysis' ? 'active' : ''} onClick={() => setView('analysis')}><Dna size={17} />Sequence explorer<span>{sample.sites.length}</span></button><button role="tab" aria-selected={view === 'quality'} className={view === 'quality' ? 'active' : ''} onClick={() => setView('quality')}><ShieldCheck size={17} />Data quality{quality.canAnalyze ? <CheckCheck size={14} /> : <span className="quality-alert-dot" />}</button><button className="analysis-export" onClick={() => download('csv')}><ArrowDownToLine size={15} />Export candidates</button></div></>}
        {view === 'analysis' && <SequenceWorkspace key={runId} {...common} />}
        {view === 'quality' && <Quality {...common} />}
        {view === 'accuracy' && <Accuracy {...common} />}
        {view === 'algorithms' && <Algorithms {...common} />}
        {view === 'reports' && <Reports {...common} />}
        {view === 'guide' && <Guide />}
        <footer className="page-footer"><span><Dna size={15} />EcoSplice · DNA splice site analysis</span><span><span className="status-dot" />{sample.builtIn ? 'Synthetic data · illustrative scores & timing' : 'Local input · motif candidates only'}</span></footer>
      </main>
    </div>
    {modal && <NewAnalysis onClose={() => setModal(null)} onLoad={load} currentId={sample.id} initialMode={modal} />}
    {toast && <div className="toast" role="status"><CheckCheck size={18} />{toast}<button className="icon-button" aria-label="Dismiss notification" onClick={() => setToast('')}><X size={15} /></button></div>}
  </div>;
}
