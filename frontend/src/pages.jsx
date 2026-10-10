import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Download, Check, CheckCheck, CircleHelp, Dna, FlaskConical, LoaderCircle, ShieldCheck, Target, Upload, X } from 'lucide-react';
import { inspectSequence, parseSequence } from './lib/analysis.js';
import { LatestRequest, sampleFastaUrl } from './lib/api.js';
import { Badge, Empty, Metric, Panel } from './components.jsx';

export { Accuracy } from './validation-page.jsx';
export { Algorithms } from './comparison-page.jsx';
export { Reports } from './reports-page.jsx';
export { Guide } from './guide-page.jsx';
const format = (value) => Number(value).toLocaleString('en-IN');

export function Quality({ sample, quality, rawMotifs, openInput, setView, run }) {
  const checks = [
    { name: 'Sequence is present', detail: `${format(quality.length)} characters loaded`, pass: quality.length > 0 },
    { name: 'DNA alphabet', detail: quality.invalid.length ? `${quality.invalid.length} unsupported symbols found` : 'Contains only A, C, G, T or N', pass: !quality.invalid.length },
    { name: 'Minimum usable length', detail: 'At least 20 called bases are required', pass: quality.counts.A + quality.counts.C + quality.counts.G + quality.counts.T >= 20 },
    { name: 'Unknown bases', detail: quality.counts.N ? `${quality.counts.N} N bases; affected contexts remain unscored` : 'No unknown N bases', pass: !quality.counts.N, warning: true },
  ];
  return <>
    <div className="quality-banner"><span className="quality-banner-icon"><ShieldCheck size={27} /></span><div><h2>{quality.canAnalyze ? 'Input ready' : 'Check input'}</h2><p>{sample.name} · {sample.source}</p></div><Badge tone={quality.canAnalyze ? 'green' : 'amber'}>{quality.canAnalyze ? 'Input checks passed' : 'Action needed'}</Badge></div>
    <div className="metrics-grid"><Metric label="Called bases" value={quality.completeness.toFixed(1)} unit="%" detail="A, C, G and T / all characters" icon={CheckCheck} /><Metric label="GC content" value={quality.gc.toFixed(1)} unit="%" detail="G and C / called bases" icon={Dna} /><Metric label="Unknown bases" value={quality.counts.N} unit="N" detail="N indicates an unknown base" icon={CircleHelp} /><Metric label="Unsupported symbols" value={quality.invalid.length} unit="" detail="Symbols outside A, C, G, T and N" icon={ShieldCheck} /></div>
    <div className="two-column"><Panel title="Input checks" eyebrow="VALIDATION"><div className="checks-list">{checks.map((check) => <div className="check-row" key={check.name}><span className={`check-indicator ${check.pass ? 'pass' : 'warn'}`}>{check.pass ? <Check size={16} /> : <CircleHelp size={16} />}</span><div><strong>{check.name}</strong><span>{check.detail}</span></div><Badge tone={check.pass ? 'green' : 'amber'}>{check.pass ? 'Pass' : check.warning ? 'Review' : 'Fix'}</Badge></div>)}</div></Panel><Panel title="Base composition" eyebrow="SEQUENCE CONTENT"><div className="composition-bar">{Object.entries(quality.counts).map(([base, count]) => count > 0 && <span key={base} className={`composition-${base}`} style={{ width: `${count / quality.length * 100}%` }} title={`${base}: ${count}`} />)}</div><div className="composition-list">{Object.entries(quality.counts).map(([base, count]) => <div key={base}><span><i className={`base-dot composition-${base}`} /><strong className="mono">{base}</strong></span><span className="mono">{format(count)}</span><span className="small-muted">{(count / Math.max(1, quality.length) * 100).toFixed(1)}%</span></div>)}</div></Panel></div>
    {quality.invalid.length > 0 && <Panel title="Unsupported symbols"><p className="panel-description">Correct these positions in your source sequence and load it again. Symbols stay visible in this input check.</p><div className="invalid-symbols">{quality.invalid.slice(0, 24).map((item) => <Badge key={item.position} tone="amber">{item.base} at {item.position}</Badge>)}{quality.invalid.length > 24 && <span>+{quality.invalid.length - 24} more</span>}</div><button className="button secondary" onClick={() => openInput('custom')}>Load corrected sequence</button></Panel>}
    <details className="provenance-details"><summary>What these checks mean</summary><div className="explanation-grid"><div><Dna size={22} /><h3>Valid input</h3><p>Alphabet and length checks tell us whether analysis can start. GC content describes the sequence; it is not a quality grade.</p></div><div><Target size={22} /><h3>{quality.canAnalyze ? `${format(rawMotifs.length)} raw motifs` : 'Motif scan pending'}</h3><p>Every GT and AG occurrence is counted separately. Full 102-base contexts with only A/C/G/T can be scored. {run ? `${run.analysis.work.unscored_candidates} candidates were unscored in the completed run.` : 'Run analysis for model scores.'}</p></div><div><FlaskConical size={22} /><h3>Format checks only</h3><p>A DNA string has no sequencing quality scores. Read-level quality checks require FASTQ data, outside this scope.</p></div></div></details>
    <button className="button primary" onClick={() => setView('analysis')} disabled={!quality.canAnalyze}>Go to analysis <ArrowRight size={16} /></button>
  </>;
}

export function NewAnalysis({ onClose, onLoad, currentId, initialMode = 'sample', samples }) {
  const [mode, setMode] = useState(initialMode === 'sample' ? 'sample' : 'custom');
  const [choice, setChoice] = useState(samples.some((sample) => sample.id === currentId) ? currentId : samples[0]?.id || '');
  const [raw, setRaw] = useState('');
  const [fileName, setFileName] = useState('');
  const [fileReading, setFileReading] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const inputRef = useRef(null);
  const headingRef = useRef(null);
  const dialogRef = useRef(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  const [fileGate] = useState(() => new LatestRequest());
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    const previousFocus = document.activeElement;
    headingRef.current?.focus();
    const handler = (event) => {
      if (event.key === 'Escape') closeRef.current();
      if (event.key !== 'Tab') return;
      const nodes = [...dialogRef.current.querySelectorAll('a[href], button:not(:disabled), input:not([type="file"]):not(:disabled), textarea:not(:disabled)')];
      const first = nodes[0], last = nodes[nodes.length - 1];
      if (event.shiftKey && (document.activeElement === first || document.activeElement === headingRef.current)) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener('keydown', handler);
    const oldOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => { alive.current = false; fileGate.cancel(); document.removeEventListener('keydown', handler); document.body.style.overflow = oldOverflow; previousFocus?.focus(); };
  }, [fileGate]);

  const readFile = async (file) => {
    if (!file) return;
    const ticket = fileGate.begin();
    setRaw(''); setFileName(''); setError(''); setFileReading(true);
    if (file.size > 1_000_000) { setError('Choose a FASTA/TXT file no larger than 1 MB.'); setFileReading(false); return; }
    try {
      const text = await file.text();
      if (ticket.isCurrent() && alive.current) { setRaw(text); setFileName(file.name); setError(''); }
    } catch { if (ticket.isCurrent() && alive.current) setError('This file could not be read. Try a plain text or FASTA file.'); }
    finally { if (ticket.isCurrent() && alive.current) setFileReading(false); }
  };
  const submit = async () => {
    let next;
    if (mode === 'sample') next = { sample_id: choice };
    else {
      try {
        const parsed = parseSequence(raw);
        const quality = inspectSequence(parsed.sequence);
        if (quality.invalid.length) throw new Error(`Unsupported DNA symbols: ${[...new Set(quality.invalid.map((item) => item.base))].join(', ')}`);
        if (!quality.canAnalyze) throw new Error('Provide at least 20 known A/C/G/T bases.');
        next = { id: 'CUSTOM', name: parsed.name === 'Custom sequence' && fileName ? fileName : parsed.name,
          source: fileName ? `Uploaded file: ${fileName}` : 'Pasted DNA', sequence: parsed.sequence, raw, sites: [], builtIn: false };
      } catch (problem) { setError(problem.message); return; }
    }
    setBusy(true); setError('');
    const loaded = await onLoad(next);
    if (alive.current) { setBusy(false); if (!loaded) setError('Sequence could not be loaded. Check the local service and retry.'); }
  };
  return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}><div className="modal" ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <div className="modal-heading"><div><span className="eyebrow">SEQUENCE INPUT</span><h2 id="modal-title" ref={headingRef} tabIndex="-1">Load DNA</h2><p>Select a sample, paste DNA, or upload a file.</p></div><button className="icon-button" onClick={onClose} aria-label="Close new analysis"><X size={20} /></button></div>
    <div className="modal-tabs" role="tablist" aria-label="Input mode"><button role="tab" aria-selected={mode === 'sample'} className={mode === 'sample' ? 'active' : ''} onClick={() => { setMode('sample'); setError(''); }}><FlaskConical size={16} />Real samples</button><button role="tab" aria-selected={mode === 'custom'} className={mode === 'custom' ? 'active' : ''} onClick={() => { setMode('custom'); setError(''); }}><Upload size={16} />Your sequence</button></div>
    {mode === 'sample' ? <div className="sample-options">{samples.length ? samples.map((sample) => <label key={sample.id} className={`sample-option ${choice === sample.id ? 'selected' : ''}`}><input type="radio" name="sample" value={sample.id} checked={choice === sample.id} onChange={() => setChoice(sample.id)} /><span className="option-icon"><Dna size={21} /></span><div><strong>{sample.name}</strong><p>{sample.source} · {sample.genomic_region.strand} strand, oriented input</p><small>{format(sample.length)} bases · {sample.annotated_boundaries} annotated boundaries · held-out test gene</small></div><span className="radio-visual">{choice === sample.id && <Check size={12} />}</span></label>) : <Empty title="Real samples unavailable" description="Connect to the local backend, or paste your own DNA for input checks." />}</div> : <div className="custom-input"><label className="input-label" htmlFor="sequence-input">DNA sequence or single-record FASTA</label><textarea id="sequence-input" value={raw} onChange={(event) => { fileGate.cancel(); setFileReading(false); setRaw(event.target.value); setFileName(''); setError(''); }} placeholder={'>my_sample\nACGTACCTGTAAGT…'} spellCheck="false" /><div className="upload-zone"><input ref={inputRef} aria-label="Upload DNA file" type="file" accept=".fa,.fasta,.fna,.txt" className="sr-only" onChange={(event) => readFile(event.target.files?.[0])} /><Upload size={19} /><span>{fileName || 'FASTA or TXT · one record · up to 100,000 bases'}</span><button className="button secondary small" onClick={() => inputRef.current?.click()}>Choose file</button></div><p className="small-muted">A/C/G/T/N · 20 called bases minimum · 1 MB maximum. Uploaded DNA has no accuracy labels.</p></div>}
    <a className="sample-download" href={sampleFastaUrl()} download><Download size={15} />Download test FASTA · ARVCF</a>
    {error && <div className="form-error" role="alert">{error}</div>}
    <div className="modal-footer"><span><ShieldCheck size={15} />Analysis and history stay on this laptop</span><button className="button primary" disabled={busy || fileReading || (mode === 'sample' && !choice)} onClick={submit}>{busy ? <LoaderCircle size={16} className="spin" /> : <ArrowRight size={16} />}{busy ? 'Loading sequence…' : 'Load sequence'}</button></div>
  </div></div>;
}
