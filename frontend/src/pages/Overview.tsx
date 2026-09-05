import { useEffect, useState } from 'react';
import { fetchStatus, fetchLatest, type MLStatus, type MLLatest } from '../api';

export default function Overview() {
    const [status, setStatus] = useState<MLStatus | null>(null);
    const [latest, setLatest] = useState<MLLatest | null>(null);

    useEffect(() => {
        const poll = async () => {
            try {
                setStatus(await fetchStatus());
                setLatest(await fetchLatest());
            } catch (e) {
                // Handle error gracefully
            }
        };
        poll();
        const int = setInterval(poll, 3000);
        return () => clearInterval(int);
    }, []);

    const badgeClass = (s?: string) => {
        if (!s) return 'badge-muted';
        if (s.includes('ready') || s.includes('loaded') || s.includes('normal') || s.includes('completed')) return 'badge-green';
        if (s.includes('anomaly') || s.includes('failed')) return 'badge-red';
        return 'badge-amber';
    };

    return (
        <div className="flex-col gap-4">
            <div className="grid-cols-4">
                <div className="card flex-col justify-between">
                    <div className="subtitle">TELEMETRY</div>
                    <div className="title" style={{ marginTop: 10 }}>
                        <span className={`badge ${badgeClass(status?.telemetry)}`}>{status?.telemetry?.replace('_', ' ') || 'UNKNOWN'}</span>
                    </div>
                </div>
                <div className="card flex-col justify-between">
                    <div className="subtitle">MODEL 1</div>
                    <div className="title" style={{ marginTop: 10 }}>
                        <span className={`badge ${badgeClass(status?.model1)}`}>{status?.model1?.toUpperCase() || 'UNKNOWN'}</span>
                    </div>
                </div>
                <div className="card flex-col justify-between">
                    <div className="subtitle">MODEL 2</div>
                    <div className="title" style={{ marginTop: 10 }}>
                        <span className={`badge ${badgeClass(status?.model2)}`}>{status?.model2?.toUpperCase() || 'UNKNOWN'}</span>
                    </div>
                </div>
                <div className="card flex-col justify-between">
                    <div className="subtitle">PIPELINE</div>
                    <div className="title" style={{ marginTop: 10 }}>
                        <span className={`badge ${badgeClass(status?.pipeline)}`}>{status?.pipeline?.replace('_', ' ').toUpperCase() || 'UNKNOWN'}</span>
                    </div>
                </div>
            </div>

            <div className="grid-cols-2" style={{ marginTop: 16 }}>
                <div className="card" style={{ minHeight: 300 }}>
                    <div className="title">Anomaly Detection</div>
                    <div className="text-small text-muted mb-4">Model 1 Sequence Evaluator</div>

                    <div className="flex items-center" style={{ marginTop: 30 }}>
                        <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
                            {/* Radial placeholder using CSS */}
                            <div style={{
                                width: 150, height: 150, borderRadius: '50%',
                                border: `8px solid ${latest?.anomaly?.detected ? 'var(--brand-red)' : 'var(--border-subtle)'}`,
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                flexDirection: 'column'
                            }}>
                                <span className="text-muted" style={{ fontSize: 11 }}>SCORE</span>
                                <span style={{ fontSize: 28, fontWeight: 700 }}>{latest?.anomaly?.score?.toFixed(4) || '—'}</span>
                            </div>
                        </div>
                        <div style={{ flex: 1 }} className="flex-col gap-4">
                            <div>
                                <div className="text-small text-muted">Current Status</div>
                                <div style={{ fontWeight: 600, color: latest?.anomaly?.detected ? 'var(--brand-red)' : 'var(--brand-green)' }}>
                                    {latest?.status?.replace(/_/g, ' ').toUpperCase() || 'UNKNOWN'}
                                </div>
                            </div>
                            <div>
                                <div className="text-small text-muted">Detection Threshold</div>
                                <div style={{ fontWeight: 600, fontFamily: 'monospace' }}>{latest?.anomaly?.threshold || '—'}</div>
                            </div>
                            <div>
                                <div className="text-small text-muted">Telemetry Window</div>
                                <div style={{ fontSize: 12 }}>{latest?.timestamp || '—'}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="card" style={{ minHeight: 300 }}>
                    <div className="title">Root Cause Analysis</div>
                    <div className="text-small text-muted mb-4">Model 2 Dependency Graph Inference</div>

                    <div className="flex flex-col gap-4" style={{ marginTop: 16 }}>
                        <div style={{ padding: 12, background: 'var(--bg-base)', border: '1px solid var(--border-focus)', borderRadius: 4 }}>
                            <div className="text-small text-muted">RCA Status</div>
                            <div style={{ color: 'var(--brand-amber)', fontWeight: 600 }}>{latest?.root_cause?.status?.replace(/_/g, ' ').toUpperCase() || 'NOT TRIGGERED'}</div>
                        </div>

                        {latest?.root_cause?.service ? (
                            <div style={{ padding: 12, background: 'rgba(255, 75, 75, 0.1)', border: '1px solid rgba(255, 75, 75, 0.3)', borderRadius: 4 }}>
                                <div className="text-small text-muted" style={{ color: 'var(--brand-red)' }}>Probable Root Cause</div>
                                <div style={{ fontSize: 18, color: 'var(--brand-red)', fontWeight: 700 }}>{latest.root_cause.service}</div>
                                <div className="text-small" style={{ marginTop: 4 }}>Confidence Score: {latest.root_cause.score?.toFixed(4)}</div>
                            </div>
                        ) : (
                            <div style={{ padding: 24, textAlign: 'center', border: '1px dashed var(--border-focus)', borderRadius: 4, color: 'var(--text-muted)' }}>
                                {latest?.root_cause?.status === 'insufficient_graph_data'
                                    ? 'INSUFFICIENT GRAPH DATA TO BUILD TOPOLOGY'
                                    : 'NO ROOT CAUSE DETECTED'}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
