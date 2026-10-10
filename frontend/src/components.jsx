import { Dna, Info, LoaderCircle } from 'lucide-react';

export function Badge({ children, tone = 'green', dot = false }) {
  return <span className={`badge badge-${tone}`}>{dot && <span className="status-dot" />}{children}</span>;
}
export function Panel({ title, eyebrow, children, action, className = '' }) {
  return <section className={`panel ${className}`}>
    {(title || action) && <div className="panel-heading"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h2>{title}</h2></div>{action}</div>}
    {children}
  </section>;
}
export function Note({ children }) { return <div className="note"><Info size={16} /><span>{children}</span></div>; }
export function Metric({ label, value, unit, detail, icon: Icon, accent, children }) {
  return <div className={`metric-card ${accent ? 'metric-accent' : ''}`}><div className="metric-top"><span>{label}</span><Icon size={19} /></div><div className="metric-value">{value}<span>{unit}</span></div><div className="metric-bottom"><span>{detail}</span>{children}</div></div>;
}
export function Empty({ title, description, children }) {
  return <div className="empty-state"><span className="empty-icon"><Dna size={25} /></span><h3>{title}</h3><p>{description}</p>{children}</div>;
}
export function ResourceState({ busy, error, retry }) {
  if (busy) return <div className="service-state" role="status"><LoaderCircle size={17} className="spin" />Loading measured results…</div>;
  if (error) return <div className="form-error" role="alert"><span>{error}</span><button className="button secondary small" onClick={retry}>Retry</button></div>;
  return null;
}
