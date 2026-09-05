import { useEffect, useState } from 'react';
import { fetchLatest, type MLLatest } from '../api';

export default function AnomalyDetection() {
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

    const isAnomaly = latest?.anomaly?.detected;
    const isWarming = latest?.status === 'warming_up';

    return (
        <div className="flex-col gap-4">
            <div className="flex items-center justify-between">
                <div className="title">Anomaly Detection Analysis</div>
            </div>

            <div className="grid-cols-4">
                <div className="card flex-col">
                    <div className="text-small text-muted">Input Features</div>
                    <div style={{ fontSize: 20, fontWeight: 700 }}>20</div>
                </div>
                <div className="card flex-col">
                    <div className="text-small text-muted">Detection Status</div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: isAnomaly ? 'var(--brand-red)' : isWarming ? 'var(--brand-amber)' : 'var(--brand-green)' }}>
                        {latest?.status?.replace(/_/g, ' ').toUpperCase() || 'WAITING'}
                    </div>
                </div>
                <div className="card flex-col">
                    <div className="text-small text-muted">Current Score</div>
                    <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'monospace' }}>{latest?.anomaly?.score?.toFixed(5) || '—'}</div>
                </div>
                <div className="card flex-col">
                    <div className="text-small text-muted">Threshold</div>
                    <div style={{ fontSize: 20, fontWeight: 700, fontFamily: 'monospace' }}>{latest?.anomaly?.threshold || '—'}</div>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 16, marginTop: 16 }}>
                <div className="card" style={{ minHeight: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <div style={{ textAlign: 'center' }}>
                        <div className="title text-muted" style={{ color: 'var(--brand-cyan)' }}>CHART ENGINE READY</div>
                        <div className="subtitle text-small">Awaiting robust sequence history API to plot actual backend telemetry history.</div>
                    </div>
                </div>

                <div className="card flex-col gap-4" style={{ background: 'var(--bg-base)' }}>
                    <div className="title" style={{ fontSize: 14 }}>MODEL 1 EXPERT PANEL</div>
                    <div className="text-small text-muted">VAE ANOMALY DETECTION</div>
                    <hr style={{ borderColor: 'var(--border-subtle)', margin: '8px 0' }} />

                    <div className="flex-col gap-2 text-small">
                        <div className="flex justify-between">
                            <span className="text-muted">Algorithm</span>
                            <span>LSTM-VAE</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-muted">Target</span>
                            <span>Sequence Reconstruction</span>
                        </div>
                    </div>

                    <div className="title" style={{ fontSize: 14, marginTop: 16 }}>TIMELINE LOGS</div>
                    <div className="flex-col gap-2" style={{ fontFamily: 'monospace', fontSize: 10, color: 'var(--text-muted)' }}>
                        <div>&gt; {latest?.timestamp || 'Waiting...'} - Frame Processed</div>
                        <div>&gt; Score: {latest?.anomaly?.score}</div>
                        <div style={{ color: 'var(--brand-amber)' }}>&gt; RCA Evaluation context relayed</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
