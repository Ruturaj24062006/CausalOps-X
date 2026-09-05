import { useEffect, useState } from 'react';
import { fetchLatest, type MLLatest } from '../api';

export default function LiveTelemetry() {
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

    return (
        <div className="flex-col gap-4">
            <div className="title">Live Telemetry</div>

            <div className="grid-cols-4">
                {['CPU', 'Memory', 'Errors', 'Latency P90'].map(m => (
                    <div key={m} className="card">
                        <div className="subtitle">{m}</div>
                        <div className="title" style={{ marginTop: 8, color: 'var(--text-muted)' }}>—</div>
                    </div>
                ))}
            </div>

            <div className="card" style={{ marginTop: 16, minHeight: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center' }}>
                    <div className="title text-muted" style={{ color: 'var(--brand-amber)' }}>TELEMETRY VISUALIZATION UNAVAILABLE</div>
                    <div className="subtitle text-small">Waiting for historical telemetry API. No simulated data is rendered.</div>

                    <div style={{ marginTop: 24, padding: 12, background: 'var(--bg-base)', border: '1px solid var(--border-subtle)', borderRadius: 4, fontFamily: 'monospace', fontSize: 11, textAlign: 'left', maxWidth: 600, overflow: 'auto', color: 'var(--brand-cyan)' }}>
                        RAW STATE PAYLOAD: {JSON.stringify(latest, null, 2)}
                    </div>
                </div>
            </div>
        </div>
    );
}
