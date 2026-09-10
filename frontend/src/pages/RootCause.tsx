import { useEffect, useState } from 'react';
import { fetchLatest, type MLLatest } from '../api';

export default function RootCause() {
    const [latest, setLatest] = useState<MLLatest | null>(null);

    useEffect(() => {
        const poll = async () => {
            try {
                setLatest(await fetchLatest());
            } catch (e) {
                // ignore
            }
        };
        poll();
        const int = setInterval(poll, 3000);
        return () => clearInterval(int);
    }, []);

    const rcaStatus = latest?.root_cause?.status || 'WAITING FOR REAL TELEMETRY';

    return (
        <div className="flex-col gap-4">
            <div className="flex items-center justify-between">
                <div className="title">Root Cause Analysis</div>
                <div className="badge badge-amber">{rcaStatus.replace(/_/g, ' ').toUpperCase()}</div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16 }}>
                <div className="card" style={{ minHeight: 500, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-base)' }}>
                    {latest?.root_cause?.service ? (
                        <div style={{ padding: 24, border: '2px dashed var(--brand-red)', borderRadius: 8, textAlign: 'center' }}>
                            <div style={{ fontSize: 32, fontWeight: 700, color: 'var(--brand-red)' }}>{latest.root_cause.service}</div>
                            <div className="text-small text-muted mt-2">Identified Graph Culprit</div>
                        </div>
                    ) : (
                        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                            <div style={{ marginBottom: 12 }}>Waiting for real topology data</div>
                            <div className="text-small">No mock service relationships will be rendered.</div>
                        </div>
                    )}
                </div>

                <div className="card flex-col gap-4">
                    <div className="title" style={{ fontSize: 14 }}>ROOT CAUSE</div>
                    <hr style={{ borderColor: 'var(--border-subtle)', margin: '4px 0' }} />

                    <div className="flex-col gap-4">
                        <div style={{ padding: 12, background: 'var(--bg-base)', border: '1px solid var(--border-focus)', borderRadius: 4 }}>
                            <div className="text-small text-muted">Probable Service</div>
                            <div style={{ color: latest?.root_cause?.service ? 'var(--brand-red)' : 'var(--text-main)', fontWeight: 600 }}>
                                {latest?.root_cause?.service || '—'}
                            </div>
                        </div>
                        <div style={{ padding: 12, background: 'var(--bg-base)', border: '1px solid var(--border-focus)', borderRadius: 4 }}>
                            <div className="text-small text-muted">Analysis Status</div>
                            <div style={{ color: 'var(--text-main)', fontWeight: 600 }}>
                                {rcaStatus}
                            </div>
                        </div>
                    </div>

                    <div className="title" style={{ fontSize: 14, marginTop: 16 }}>MODEL 2 (GNN)</div>
                    <div className="flex-col gap-2 text-small">
                        <div className="flex justify-between">
                            <span className="text-muted">Node Features</span>
                            <span style={{ fontFamily: 'monospace' }}>20</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-muted">Edge Features</span>
                            <span style={{ fontFamily: 'monospace' }}>2</span>
                        </div>
                    </div>

                    {latest?.root_cause?.missing_requirements && (
                        <div style={{ marginTop: 16, padding: 12, border: '1px solid rgba(244, 177, 65, 0.3)', background: 'rgba(244, 177, 65, 0.05)', borderRadius: 4 }}>
                            <div style={{ color: 'var(--brand-amber)', fontSize: 12, fontWeight: 600, marginBottom: 8 }}>MISSING DEPENDENCIES</div>
                            <ul style={{ fontSize: 11, color: 'var(--text-muted)', margin: 0, paddingLeft: 16 }}>
                                {latest.root_cause.missing_requirements.map(m => (
                                    <li key={m}>{m}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
