import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowRight, ArrowUpRight, Check, ChevronLeft, ChevronRight, CircleHelp, Clock3, Dna, FileUp, FlaskConical, Leaf, LocateFixed, Search, ShieldCheck, SlidersHorizontal, Sparkles, TextCursorInput, Zap } from 'lucide-react';
import { Badge, Empty } from './components.jsx';
import { SAMPLES } from './data.js';

const number = (value) => value.toLocaleString('en-IN');

export function InputBar({ sample, quality, runId, load, openInput }) {
  return <section className="input-bar" aria-label="Active sequence">
    <div className="input-identity"><span className="input-dna-icon"><Dna size={25} strokeWidth={1.7} /></span><div><label htmlFor="active-sample">ACTIVE SEQUENCE</label><div className="sample-select"><select id="active-sample" value={sample.builtIn ? sample.id : 'CUSTOM'} onChange={(event) => { const next = SAMPLES.find((item) => item.id === event.target.value); if (next) load(next); }}>{!sample.builtIn && <option value="CUSTOM">{sample.name}</option>}{SAMPLES.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></div></div></div>
    <div className="input-meta"><span><b className="mono">{number(sample.sequence.length)}</b> bases</span><span><b className="mono">{quality.gc.toFixed(1)}%</b> GC</span><Badge tone={quality.canAnalyze ? 'green' : 'amber'} dot>{quality.canAnalyze ? 'Input checked' : 'Review input'}</Badge></div>
    <div className="input-run"><span className="mono">{runId}</span><small>{sample.builtIn ? 'SYNTHETIC SAMPLE' : 'LOCAL INPUT'}</small></div>
    <button className="input-add icon-button" aria-label="Load another sequence" onClick={() => openInput('sample')}><FileUp size={19} /></button>
  </section>;
}

export function InputActions({ openInput }) {
  return <div className="input-actions"><button className="button primary" onClick={() => openInput('sample')}><FlaskConical size={17} />Try a sample</button><button className="button secondary" onClick={() => openInput('custom')}><TextCursorInput size={17} />Paste DNA</button><button className="button secondary" onClick={() => openInput('upload')}><FileUp size={17} />Upload FASTA</button></div>;
}

export function Workflow({ quality, view, setView, openInput }) {
  const steps = [{ label: 'Load sequence', action: () => openInput('sample'), completed: true }, { label: 'Check input', action: () => setView('quality'), completed: quality.canAnalyze, active: view === 'quality' }, { label: 'Inspect candidates', action: () => setView('analysis'), active: view === 'analysis' }, { label: 'Compare methods', action: () => setView('algorithms'), active: view === 'algorithms' }];
  return <nav className="workflow" aria-label="Analysis workflow">{steps.map((step, index) => <button key={step.label} className={`workflow-step ${step.active ? 'current' : ''} ${step.completed ? 'completed' : ''}`} onClick={step.action}><span>{step.completed && !step.active ? <Check size={12} /> : String(index + 1).padStart(2, '0')}</span>{step.label}{index < steps.length - 1 && <ChevronRight size={14} className="step-arrow" />}</button>)}</nav>;
}

export function SequenceWorkspace({ sample, selectedId, inspect, threshold, setThreshold, quality, optimized, energy, openInput, setView }) {
  const [query, setQuery] = useState('');
  const [type, setType] = useState('All');
  const [page, setPage] = useState(0);
  const [help, setHelp] = useState(false);
  const [regionRequest, setRegionRequest] = useState(null);
  const [jump, setJump] = useState('');
  const filtered = useMemo(() => sample.sites.filter((site) => (site.score == null || site.score >= threshold) && (type === 'All' || site.type === type) && `${site.id} ${site.position} ${site.motif} ${site.type}`.toLowerCase().includes(query.toLowerCase())).sort((a, b) => (b.score ?? 0) - (a.score ?? 0) || a.position - b.position), [sample, threshold, type, query]);
  const site = filtered.find((candidate) => candidate.id === selectedId) || filtered[0];
  const hasScores = sample.builtIn;
  const pageSize = 6;
  const maxPage = Math.max(0, Math.ceil(filtered.length / pageSize) - 1);
  const currentPage = Math.min(page, maxPage);
  const pageRows = filtered.slice(currentPage * pageSize, (currentPage + 1) * pageSize);

  useEffect(() => {
    if (site) setPage(Math.max(0, Math.floor(filtered.findIndex((candidate) => candidate.id === site.id) / pageSize)));
  }, [site?.id, filtered]);

  const select = (candidate) => {
    inspect(candidate);
    setRegionRequest({ position: candidate.position, nonce: Date.now() });
    setPage(Math.floor(filtered.findIndex((item) => item.id === candidate.id) / pageSize));
  };
  const filterType = (next) => { setType(next); setPage(0); setRegionRequest(null); };
  const goToPosition = (event) => {
    event.preventDefault();
    const position = Number(jump);
    if (Number.isInteger(position) && position >= 1 && position <= sample.sequence.length) {
      const candidate = filtered.find((item) => item.position === position || item.position + 1 === position);
      if (candidate) select(candidate);
      else setRegionRequest({ position, nonce: Date.now() });
    }
  };

  return <>
    <section className="sequence-workbench">
      <div className="workbench-heading"><div><span className="eyebrow">01 / SEQUENCE EXPLORER</span><h2>A closer look at every base</h2></div><button className={`explain-button ${help ? 'active' : ''}`} aria-expanded={help} onClick={() => setHelp(!help)}><CircleHelp size={16} />Read this view</button></div>
      {help && <div className="viewer-explanation"><strong>Read from left to right.</strong> Each letter is a DNA base. Green marks a donor candidate (possible intron start); purple marks an acceptor candidate (possible intron end). Click a marker or a highlighted pair of letters to inspect it. Positions refer to this sample, starting at 1.</div>}
      <div className="map-caption"><span>WHOLE SEQUENCE</span><div><span><i className="legend-dot donor" />Donor · GT</span><span><i className="legend-dot acceptor" />Acceptor · AG</span><span className="map-count">{number(filtered.length)} shown / {number(sample.sites.length)} candidates</span></div></div>
      <PositionMap sample={sample} sites={filtered} selectedId={site?.id} onSelect={select} />
      <div className="sequence-toolbar"><div><Dna size={16} /><strong>DNA sequence</strong><span>5′ → 3′</span></div><form className="position-jump" onSubmit={goToPosition}><label htmlFor="jump-position">Go to base</label><input id="jump-position" aria-label="Go to base position" inputMode="numeric" type="number" min="1" max={sample.sequence.length} value={jump} placeholder={site ? String(site.position) : '1'} onChange={(event) => setJump(event.target.value)} /><button className="icon-button" aria-label="Go to entered base position"><ArrowRight size={15} /></button></form></div>
      <BaseViewer sample={sample} sites={filtered} site={site} request={regionRequest} onSelect={select} />
      <div className="viewer-footnote"><span><span className="status-dot" />{sample.builtIn ? 'Selected candidates from a synthetic sample' : quality.canAnalyze ? 'Canonical motifs scanned from your input' : 'Input checks prevent motif scanning'}</span><span>Sample coordinates · 1-based</span></div>
    </section>

    <div className="results-heading"><div><span className="eyebrow">02 / CANDIDATE INSPECTION</span><h2>Follow a possible splice boundary</h2></div><span className="small-muted">Select a row to highlight it in the sequence.</span></div>
    <div className="inspection-layout">
      <section className="candidate-panel">
        <div className="candidate-tabs" role="group" aria-label="Candidate type">{['All', 'Donor', 'Acceptor'].map((kind) => <button key={kind} className={type === kind ? 'active' : ''} aria-pressed={type === kind} onClick={() => filterType(kind)}>{kind === 'All' ? 'All candidates' : `${kind}s`}<span>{number(sample.sites.filter((item) => (item.score == null || item.score >= threshold) && (kind === 'All' || item.type === kind)).length)}</span></button>)}</div>
        <div className="candidate-controls"><div className="search-field"><Search size={16} /><input aria-label="Search candidate sites" placeholder="Search ID, position or motif" value={query} onChange={(event) => { setQuery(event.target.value); setPage(0); setRegionRequest(null); }} /></div>{hasScores && <label className="inline-threshold"><SlidersHorizontal size={15} /><span>Score ≥</span><input type="number" aria-label="Candidate score threshold" min="0" max="1" step="0.01" value={threshold} onChange={(event) => { setThreshold(Math.max(0, Math.min(1, Number(event.target.value)))); setRegionRequest(null); }} /></label>}</div>
        <div className="table-scroll"><table className="linked-table"><thead><tr><th>Candidate</th><th>Position</th><th>Type</th><th>{hasScores ? 'Demo score' : 'Score'}</th><th><span className="sr-only">Inspect candidate</span></th></tr></thead><tbody>{pageRows.map((candidate) => <tr key={candidate.id} className={site?.id === candidate.id ? 'selected' : ''} aria-selected={site?.id === candidate.id} onClick={() => select(candidate)}><td><span className={`table-motif ${candidate.type.toLowerCase()}`}>{candidate.motif}</span><strong className="mono">{candidate.id}</strong></td><td><span className="mono">{number(candidate.position)}</span><small>bp</small></td><td><span className={`type-label ${candidate.type.toLowerCase()}`}><i />{candidate.type}</span></td><td>{candidate.score == null ? <span className="unscored-label">Unscored</span> : <span className="table-score"><b className="mono">{candidate.score.toFixed(2)}</b><i><span style={{ width: `${candidate.score * 100}%` }} /></i></span>}</td><td><button className="icon-button" aria-label={`Inspect ${candidate.id} at position ${candidate.position}`} onClick={(event) => { event.stopPropagation(); select(candidate); }}><ArrowUpRight size={17} /></button></td></tr>)}</tbody></table></div>
        {!filtered.length && <Empty title={quality.canAnalyze ? 'No candidates in this view' : 'Check your input first'} description={quality.canAnalyze ? sample.sites.length ? 'Adjust the threshold, type filter, or search to see more candidates.' : 'This sequence has no canonical GT or AG motifs.' : 'Review the Data quality tab to resolve unsupported symbols or a short sequence.'}>{!quality.canAnalyze && <button className="button secondary" onClick={() => setView('quality')}>Review input</button>}</Empty>}
        <div className="table-footer"><span>{filtered.length ? currentPage * pageSize + 1 : 0}–{Math.min((currentPage + 1) * pageSize, filtered.length)} of {number(filtered.length)} candidates</span><div className="pagination"><button className="icon-button" aria-label="Previous candidate page" disabled={!currentPage} onClick={() => setPage(currentPage - 1)}><ChevronLeft size={16} /></button><span>{currentPage + 1} / {maxPage + 1}</span><button className="icon-button" aria-label="Next candidate page" disabled={currentPage >= maxPage} onClick={() => setPage(currentPage + 1)}><ChevronRight size={16} /></button></div></div>
      </section>
      <CandidateInspector sample={sample} site={site} recenter={() => site && setRegionRequest({ position: site.position, nonce: Date.now() })} />
    </div>

    <section className="analysis-cost-strip"><span className="cost-strip-icon"><Leaf size={23} /></span><div className="cost-strip-intro"><strong>Every computation has a cost.</strong><span>Explore the energy trade-off in Compare.</span></div><div><span>Demo runtime</span><strong>{optimized ?? '—'} <small>{optimized != null ? 'ms' : ''}</small></strong></div><div><span>Estimated energy</span><strong>{energy == null ? '—' : energy.toFixed(2)} <small>{energy != null ? 'J' : ''}</small></strong></div><button className="text-button" onClick={() => setView('algorithms')}>Compare methods <ArrowUpRight size={17} /></button></section>
    <p className="sample-method-note">{sample.builtIn ? 'Demo scores and runtime are constructed examples. A highlighted motif suggests a possible site; biological use has not been confirmed.' : 'Your sequence stays in this browser session. GT/AG scanning identifies motif candidates; no prediction model or probability is applied.'}</p>
  </>;
}

function PositionMap({ sample, sites, selectedId, onSelect }) {
  const length = sample.sequence.length;
  let displayed = sites;
  if (sites.length > 160) {
    displayed = sites.filter((_, index) => index % Math.ceil(sites.length / 160) === 0);
    const selected = sites.find((site) => site.id === selectedId);
    if (selected && !displayed.some((site) => site.id === selectedId)) displayed = [...displayed, selected];
  }
  return <div className="position-map">
    {['Donor', 'Acceptor'].map((type) => <div className={`map-lane ${type.toLowerCase()}`} key={type}><span className="lane-label">{type === 'Donor' ? 'GT' : 'AG'}</span><div className="lane-track"><div className="lane-baseline" />{displayed.filter((site) => site.type === type).map((site) => <button key={site.id} className={`map-marker ${site.id === selectedId ? 'selected' : ''}`} aria-label={`${site.type} candidate at position ${site.position}`} aria-pressed={site.id === selectedId} title={`${site.id} · ${site.type} at ${site.position}${site.score != null ? ` · demo score ${site.score.toFixed(2)}` : ''}`} style={{ left: `${(site.position - 1) / Math.max(1, length - 1) * 100}%` }} onClick={() => onSelect(site)}><i /><span>{site.id === selectedId ? number(site.position) : ''}</span></button>)}</div></div>)}
    <div className="map-axis"><span className="lane-label">bp</span><div>{[0, .25, .5, .75, 1].map((fraction) => <span key={fraction}>{number(Math.max(1, Math.round(1 + fraction * (length - 1))))}</span>)}</div></div>
    {!sites.length && <span className="map-empty">{sample.analysisBlocked ? 'Scan pending input checks' : 'No candidates match the current view'}</span>}
    {sites.length > 160 && <p className="map-preview-note">Position map shows a spaced preview of {number(displayed.length)} candidates. All {number(sites.length)} are available below.</p>}
  </div>;
}

function BaseViewer({ sample, sites, site, request, onSelect }) {
  const element = useRef(null);
  const [columns, setColumns] = useState(40);
  const [start, setStart] = useState(0);
  const length = sample.sequence.length;
  const span = columns * 3;
  const maxStart = Math.max(0, length - span);
  const safeStart = Math.min(start, maxStart);
  const end = Math.min(length, safeStart + span);
  const bases = sample.sequence.slice(safeStart, end);
  const nearSites = useMemo(() => {
    const map = new Map();
    for (const candidate of sites) if (candidate.position <= end && candidate.position + 1 >= safeStart + 1) {
      map.set(candidate.position, candidate);
      if (!map.has(candidate.position + 1)) map.set(candidate.position + 1, candidate);
    }
    if (site && site.position <= end && site.position + 1 >= safeStart + 1) { map.set(site.position, site); map.set(site.position + 1, site); }
    return map;
  }, [sites, site, safeStart, end]);
  useEffect(() => {
    const observer = new ResizeObserver(([entry]) => {
      const available = entry.contentRect.width - 82;
      setColumns(available >= 800 ? 40 : available >= 560 ? 30 : available >= 360 ? 20 : 10);
    });
    if (element.current) observer.observe(element.current);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    const position = request?.position ?? site?.position ?? 1;
    setStart(Math.max(0, Math.min(maxStart, Math.floor((position - 1 - columns / 2) / columns) * columns)));
  }, [request, site?.id, sample.id, columns, maxStart]);
  const selectedVisible = site && site.position >= safeStart + 1 && site.position <= end;
  return <div className="base-viewer" ref={element}>
    <div className="base-ruler"><span>LOCAL CONTEXT</span><span className="mono">{number(safeStart + 1)} — {number(end)} <small>bp</small></span>{site && !selectedVisible && <button className="text-button" onClick={() => setStart(Math.max(0, Math.min(maxStart, site.position - 1 - columns)))}>Jump to selection <LocateFixed size={13} /></button>}</div>
    <div className="dna-rows">{Array.from({ length: Math.ceil(bases.length / columns) }, (_, row) => <div className="dna-row" key={row}><span className="dna-row-position mono">{String(safeStart + row * columns + 1).padStart(6, '0')}</span><div className="nucleotide-row" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>{[...bases.slice(row * columns, (row + 1) * columns)].map((base, index) => {
      const position = safeStart + row * columns + index + 1;
      const candidate = nearSites.get(position);
      const selected = candidate && candidate.id === site?.id;
      const className = `nucleotide base-${base} ${candidate ? `motif-${candidate.type.toLowerCase()}` : ''} ${selected ? 'is-selected' : ''}`;
      return candidate ? <button key={position} className={className} onClick={() => onSelect(candidate)} aria-label={`Select ${candidate.type.toLowerCase()} ${candidate.id} at base ${position}`} aria-pressed={!!selected} title={`${base} · base ${position} · ${candidate.type} ${candidate.id}`}>{base}<i /></button> : <span className={className} key={position} title={`${base} · base ${position}`}>{base}</span>;
    })}</div><span className="dna-row-end mono">{number(Math.min(end, safeStart + (row + 1) * columns))}</span></div>)}</div>
    <div className="base-viewer-bottom"><div className="base-key">{['A', 'C', 'G', 'T'].map((base) => <span key={base}><i className={`base-${base}`}>{base}</i></span>)}<span>DNA bases</span></div><div className="context-navigation"><button className="icon-button" aria-label="Previous sequence region" disabled={safeStart === 0} onClick={() => setStart(Math.max(0, safeStart - span))}><ChevronLeft size={16} /></button><span>{number(bases.length)} bases in view</span><button className="icon-button" aria-label="Next sequence region" disabled={end === length} onClick={() => setStart(Math.min(maxStart, safeStart + span))}><ChevronRight size={16} /></button></div></div>
  </div>;
}

function CandidateInspector({ sample, site, recenter }) {
  if (!site) return <aside className="candidate-inspector inspector-empty"><span className="eyebrow">SELECTED CANDIDATE</span><Empty title="An open space for discovery" description="Select a candidate from the map or results table to inspect its DNA context." /></aside>;
  const index = site.position - 1;
  const left = sample.sequence.slice(Math.max(0, index - 6), index);
  const right = sample.sequence.slice(index + 2, index + 8);
  const donor = site.type === 'Donor';
  return <aside className={`candidate-inspector ${site.type.toLowerCase()}`} aria-label="Selected candidate details" aria-live="polite">
    <div className="inspector-heading"><span className="eyebrow">SELECTED CANDIDATE</span><span className="mono">{site.id}</span></div>
    <div className="inspector-identity"><span className="inspector-motif">{site.motif}</span><div><Badge tone={donor ? 'green' : 'purple'}>{site.type} candidate</Badge><h3>Position <b className="mono">{number(site.position)}</b> <small>bp</small></h3></div></div>
    <p className="inspector-description">{donor ? 'A possible start boundary of an intron.' : 'A possible end boundary of an intron.'}</p>
    <div className="inspector-context mono"><span>{left || '·'}</span><strong>{site.motif}</strong><span>{right || '·'}</span></div>
    <div className="inspector-score"><div><span>{site.score == null ? 'Prediction score' : 'Demonstration score'}</span><strong>{site.score == null ? 'Not available' : site.score.toFixed(2)}{site.score != null && <small> / 1.00</small>}</strong></div>{site.score != null && <div className="inspector-score-track"><span style={{ width: `${site.score * 100}%` }} /></div>}<p>{site.score == null ? 'This input receives motif scanning only.' : 'A constructed score used to explore the interface.'}</p></div>
    <div className="inspector-evidence"><span><ShieldCheck size={16} />Biological confirmation</span><strong>Not established</strong></div>
    <div className="inspector-route"><span>{site.route === 'Fast path' ? <Zap size={16} /> : <SlidersHorizontal size={16} />}{site.route}</span><small>{sample.builtIn ? 'Illustrative processing decision' : 'Forward sequence · GT/AG only'}</small></div>
    <button className="button secondary full-width" onClick={recenter}><LocateFixed size={16} />Centre this site in the sequence</button>
  </aside>;
}

export function ProcessingSketch({ ratio, optimized = false }) {
  const count = Math.max(0, Math.min(40, Math.round(ratio * 40)));
  return <div className={`processing-sketch ${optimized ? 'optimized' : ''}`}><div aria-hidden="true">{Array.from({ length: 40 }, (_, index) => <i key={index} className={Math.floor((index + 1) * count / 40) > Math.floor(index * count / 40) ? 'processed' : ''} />)}</div><span>{optimized ? 'Fraction of positions with a canonical motif' : 'Every position receives detailed analysis'} · schematic</span></div>;
}
