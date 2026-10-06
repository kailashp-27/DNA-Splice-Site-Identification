import { ArrowUpRight, ChevronLeft, ChevronRight, Search, SlidersHorizontal, Info, Dna } from 'lucide-react';
import { useMemo, useState } from 'react';

export function Badge({ children, tone = 'green', dot = false }) {
  return <span className={`badge badge-${tone}`}>{dot && <span className="status-dot" />}{children}</span>;
}

export function Panel({ title, eyebrow, children, action, className = '' }) {
  return <section className={`panel ${className}`}>
    {(title || action) && <div className="panel-heading"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h2>{title}</h2></div>{action}</div>}
    {children}
  </section>;
}

export function Note({ children }) {
  return <div className="note"><Info size={16} /><span>{children}</span></div>;
}

export function Metric({ label, value, unit, detail, icon: Icon, accent, children }) {
  return <div className={`metric-card ${accent ? 'metric-accent' : ''}`}>
    <div className="metric-top"><span>{label}</span><Icon size={19} /></div>
    <div className="metric-value">{value}<span>{unit}</span></div>
    <div className="metric-bottom"><span>{detail}</span>{children}</div>
  </div>;
}

export function Empty({ title, description, children }) {
  return <div className="empty-state"><span className="empty-icon"><Dna size={25} /></span><h3>{title}</h3><p>{description}</p>{children}</div>;
}

export function Landscape({ sample, selectedId, onSelect }) {
  const length = sample.sequence.length;
  const sites = sample.sites;
  const displayed = sites.length > 250 ? sites.filter((_, i) => i % Math.ceil(sites.length / 250) === 0) : sites;
  const x = (position) => 46 + position / length * 830;
  const y = (site) => 164 - (site.score ?? 0.5) * 120;
  return <div className="landscape">
    <div className="chart-legend"><span><i className="legend-dot donor" />Donor · GT</span><span><i className="legend-dot acceptor" />Acceptor · AG</span><span className="chart-label">{sample.builtIn ? 'Illustrative scores' : 'Unscored motifs'}</span></div>
    <svg viewBox="0 0 910 210" role="img" aria-label={`Candidate positions across ${length} bases. Donor sites in green and acceptor sites in purple.`}>
      <defs><linearGradient id="donorFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#65a994" stopOpacity="0.25" /><stop offset="100%" stopColor="#65a994" stopOpacity="0.02" /></linearGradient></defs>
      {[0, .25, .5, .75, 1].map((tick) => <g key={tick}><line x1="46" y1={164 - tick * 120} x2="876" y2={164 - tick * 120} stroke="#e8eeeb" strokeDasharray={tick === 0 ? undefined : '3 5'} /><text x="30" y={168 - tick * 120} textAnchor="end" className="axis-label">{sample.builtIn ? tick.toFixed(2) : tick === .5 ? 'Sites' : ''}</text></g>)}
      {displayed.map((site) => <g key={site.id} className="chart-site" role="button" tabIndex="0" aria-label={`${site.type} candidate at position ${site.position}`} onClick={() => onSelect(site)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(site); } }}>
        <title>{site.type} · position {site.position}{site.score != null ? ` · demo score ${site.score}` : ''}</title>
        <line x1={x(site.position)} x2={x(site.position)} y1="164" y2={y(site)} stroke={site.type === 'Donor' ? '#79b6a3' : '#b4a4cd'} strokeWidth="2" />
        <circle cx={x(site.position)} cy={y(site)} r={site.id === selectedId ? 6 : 4} fill={site.type === 'Donor' ? '#287960' : '#8a6ba8'} stroke="white" strokeWidth="2" />
        <rect x={x(site.position) - 10} y="25" width="20" height="150" fill="transparent" />
      </g>)}
      {[0, .2, .4, .6, .8, 1].map((tick) => <text key={tick} x={46 + tick * 830} y="192" textAnchor="middle" className="axis-label">{Math.round(length * tick).toLocaleString() || '1'}</text>)}
      <text x="461" y="208" textAnchor="middle" className="axis-label">Position in sample (bases)</text>
    </svg>
    {sites.length === 0 && <div className="chart-empty">{sample.analysisBlocked ? "Input checks prevent motif scanning." : "No canonical GT or AG candidates in this sample."}</div>}
    {sites.length > 250 && <p className="small-muted">Showing an evenly spaced preview of {displayed.length} out of {sites.length.toLocaleString()} motifs. Every motif is available in the table and export.</p>}
  </div>;
}

export function SiteTable({ sites, threshold, onSelect, compact = false, onViewAll, selectedId }) {
  const [search, setSearch] = useState('');
  const [type, setType] = useState('All types');
  const [page, setPage] = useState(0);
  const filtered = useMemo(() => sites.filter((site) => (site.score == null || site.score >= threshold) && (type === 'All types' || site.type === type) && `${site.id} ${site.position} ${site.motif} ${site.type}`.toLowerCase().includes(search.toLowerCase())).sort((a, b) => (b.score ?? 0) - (a.score ?? 0) || a.position - b.position), [sites, threshold, search, type]);
  const pageSize = compact ? 4 : 8;
  const maxPage = Math.max(0, Math.ceil(filtered.length / pageSize) - 1);
  const safePage = Math.min(page, maxPage);
  const rows = filtered.slice(safePage * pageSize, (safePage + 1) * pageSize);
  return <>
    {!compact && <div className="table-toolbar"><div className="search-field"><Search size={16} /><input aria-label="Search candidate sites" placeholder="Search position, ID or motif…" value={search} onChange={(e) => { setSearch(e.target.value); setPage(0); }} /></div><div className="select-wrap"><SlidersHorizontal size={15} /><select aria-label="Filter site type" value={type} onChange={(e) => { setType(e.target.value); setPage(0); }}><option>All types</option><option>Donor</option><option>Acceptor</option></select></div></div>}
    <div className="table-scroll"><table className="site-table"><thead><tr><th>Candidate</th><th>Position</th><th>Type</th><th>Demo score</th>{!compact && <th>Processing path</th>}<th><span className="sr-only">View</span></th></tr></thead><tbody>{rows.map((site) => <tr key={site.id} className={selectedId === site.id ? 'selected-row' : ''}><td><span className="site-id"><span className={`site-symbol ${site.type.toLowerCase()}`}>{site.motif}</span>{site.id}</span></td><td className="mono">{site.position.toLocaleString()} <span className="small-muted">bp</span></td><td><Badge tone={site.type === 'Donor' ? 'green' : 'purple'}>{site.type}</Badge></td><td>{site.score == null ? <span className="small-muted">Unscored</span> : <div className="score-cell"><span className="mono">{site.score.toFixed(2)}</span><span className="score-track"><span style={{ width: `${site.score * 100}%` }} /></span></div>}</td>{!compact && <td className="small-muted">{site.route}</td>}<td><button className="icon-button" aria-label={`Inspect ${site.id} at position ${site.position}`} onClick={() => onSelect(site)}><ArrowUpRight size={17} /></button></td></tr>)}</tbody></table></div>
    {!rows.length && <Empty title="No matching candidates" description={sites.length ? 'Lower the score threshold or adjust the filters to see more candidates.' : 'This sample contains no available candidate sites.'} />}
    <div className="table-footer"><span>{compact ? `${Math.min(4, filtered.length)} of ${filtered.length}` : `${filtered.length ? safePage * pageSize + 1 : 0}–${Math.min((safePage + 1) * pageSize, filtered.length)} of ${filtered.length}`} candidates</span>{compact ? <button className="text-button" onClick={onViewAll}>View all candidates <ArrowUpRight size={15} /></button> : <div className="pagination"><button className="icon-button" disabled={!safePage} aria-label="Previous candidate page" onClick={() => setPage(safePage - 1)}><ChevronLeft size={16} /></button><span>{safePage + 1} / {maxPage + 1}</span><button className="icon-button" disabled={safePage >= maxPage} aria-label="Next candidate page" onClick={() => setPage(safePage + 1)}><ChevronRight size={16} /></button></div>}</div>
  </>;
}

export function SequenceDetail({ sample, site }) {
  if (!site) return <Empty title="Select a candidate" description="Choose a point on the map or a row in the table to inspect its surrounding sequence." />;
  const index = site.position - 1;
  const start = Math.max(0, Math.min(index - 27, sample.sequence.length - 60));
  const context = sample.sequence.slice(start, start + 60);
  return <div className="sequence-detail"><div className="detail-heading"><div><span className="eyebrow">SELECTED CANDIDATE</span><h3>{site.id} <span className="small-muted">at {site.position.toLocaleString()} bp</span></h3></div><Badge tone={site.type === 'Donor' ? 'green' : 'purple'}>{site.type} · {site.motif}</Badge></div><div className="sequence-context"><span className="context-position mono">{start + 1}</span><div className="base-grid">{[...context].map((base, offset) => <span key={offset} title={`Position ${start + offset + 1}`} className={start + offset === index || start + offset === index + 1 ? `base-highlight ${site.type.toLowerCase()}` : ''}>{base}</span>)}</div><span className="context-position mono">{start + context.length}</span></div><div className="detail-facts"><div><span>Coordinate convention</span><strong>1-based motif start</strong></div><div><span>Score source</span><strong>{site.score == null ? 'No model score' : 'Hardcoded demo fixture'}</strong></div><div><span>Biological confirmation</span><strong>Not available</strong></div></div><p className="small-muted">The highlighted {site.motif} is a sequence clue. Its surrounding bases help distinguish a possible splice boundary from an ordinary occurrence of the same letters.</p></div>;
}
