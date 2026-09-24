import { useData } from '../DataContext';
import { AlertTriangle, Cpu, CheckCircle, Activity } from 'lucide-react';

const C = {
    green: '#37d67a', amber: '#f4b141', red: '#ff4b4b',
    cyan: '#00d2ff', purple: '#9d4edd', muted: '#8b92a5',
    border: '#1e2230', panel: '#0c0d11', base: '#09090c', text: '#e2e4e9',
};

function sc(s?: string | null): string {
    const u = (s ?? '').toUpperCase();
    if (['HEALTHY', 'READY', 'NORMAL', 'ONLINE', 'FLOWING', 'ACTIVE'].some(x => u.includes(x))) return C.green;
    if (['DEGRADED', 'WARNING', 'BLOCKED'].some(x => u.includes(x))) return C.amber;
    if (['FAILED', 'CRITICAL', 'ANOMALY', 'ERROR'].some(x => u.includes(x))) return C.red;
    return C.cyan;
}

function Sparkline({ history, color, threshold }: { history: number[]; color: string; threshold?: number }) {
    if (history.length < 2) {
        return (
            <div style={{ height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', border: `1px solid ${C.border}`, background: C.base }}>
                <span style={{ fontSize: 8, color: C.muted, fontFamily: 'monospace' }}>Collecting data from Model 1…</span>
            </div>
        );
    }
    const W = 700, H = 80;
    const allVals = threshold ? [...history, threshold] : history;
    const max = Math.max(...allVals, 0.001) * 1.15;
    const step = W / (history.length - 1);
    const pts = history.map((v, i) => `${i * step},${H - (v / max) * H}`).join(' ');
    const thY = threshold ? H - (threshold / max) * H : null;
    return (
        <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} style={{ display: 'block', overflow: 'visible' }}>
            {thY !== null && (
                <>
                    <line x1={0} y1={thY} x2={W} y2={thY} stroke={C.amber} strokeWidth={1} strokeDasharray="6 3" opacity={0.7} />
                    <text x={W - 4} y={thY - 4} fontSize={7} fill={C.amber} textAnchor="end" fontFamily="monospace">THRESHOLD</text>
                </>
            )}
            <polyline points={`0,${H} ${pts} ${(history.length - 1) * step},${H}`} fill={color} fillOpacity={0.08} stroke="none" />
            <polyline points={pts} fill="none" stroke={color} strokeWidth={1.8} strokeLinejoin="round" />
            <circle cx={(history.length - 1) * step} cy={H - (history[history.length - 1] / max) * H} r={4} fill={color} />
        </svg>
    );
}

function KV({ k, v, vc }: { k: string; v: string; vc?: string }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 6, marginBottom: 6, borderBottom: `1px solid ${C.border}` }}>
            <span style={{ fontSize: 9, color: C.muted, fontFamily: 'monospace' }}>{k}</span>
            <span style={{ fontSize: 9, fontFamily: 'monospace', fontWeight: 700, color: vc ?? C.text }}>{v}</span>
        </div>
    );
}

export default function AnomalyDetection() {
    // ── consume global data — no local useEffect/polling needed ──
    const { latest, topology, status: mlStatus, lastUpdated, scoreHistory } = useData();

    const nodes = topology?.nodes ?? [];
    const score = latest?.anomaly?.score;
    const threshold = latest?.anomaly?.threshold;
    const isAnomaly = !!latest?.anomaly?.detected ||
        nodes.some(n => ['FAILED', 'CRITICAL', 'BLOCKED'].includes(n.status?.toUpperCase() ?? ''));
    const pct = score != null && threshold != null ? Math.min((score / threshold) * 100, 200) : null;
    const badNodes = nodes.filter(n => !['HEALTHY', 'READY', 'NORMAL'].includes(n.status?.toUpperCase() ?? ''));

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', background: C.base }}>
            {/* Header */}
            <div style={{ padding: '8px 16px', background: C.panel, borderBottom: `1px solid ${C.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <AlertTriangle size={16} color={isAnomaly ? C.red : C.amber} />
                    <span style={{ fontSize: 14, fontWeight: 800, letterSpacing: 3, color: C.text, fontFamily: 'monospace' }}>ANOMALY DETECTION</span>
                    {isAnomaly
                        ? <span style={{ fontSize: 7, padding: '2px 8px', border: `1px solid ${C.red}50`, color: C.red, background: `${C.red}12`, fontFamily: 'monospace', fontWeight: 700 }}>ANOMALY ACTIVE</span>
                        : <span style={{ fontSize: 7, padding: '2px 8px', border: `1px solid ${C.green}50`, color: C.green, background: `${C.green}12`, fontFamily: 'monospace', fontWeight: 700 }}>NORMAL</span>}
                </div>
                <span style={{ fontSize: 8, color: C.muted, fontFamily: 'monospace' }}>Updated: {lastUpdated}</span>
            </div>

            {/* KPI Ribbon */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', background: C.panel, borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
                {[
                    { label: 'CURRENT SCORE', value: score?.toFixed(5) ?? '…', color: isAnomaly ? C.red : C.text },
                    { label: 'THRESHOLD', value: threshold?.toFixed(5) ?? '…', color: C.amber },
                    { label: 'STATUS', value: isAnomaly ? 'ANOMALY' : 'NORMAL', color: isAnomaly ? C.red : C.green },
                    { label: 'INPUT FEATURES', value: '20', color: C.cyan },
                    { label: 'AFFECTED SERVICES', value: String(badNodes.length), color: badNodes.length > 0 ? C.red : C.muted },
                ].map(({ label, value, color }, i, arr) => (
                    <div key={label} style={{ padding: '8px 14px', borderRight: i < arr.length - 1 ? `1px solid ${C.border}` : 'none' }}>
                        <div style={{ fontSize: 7, fontFamily: 'monospace', letterSpacing: 2, color: C.muted }}>{label}</div>
                        <div style={{ fontSize: 13, fontWeight: 800, fontFamily: 'monospace', color, marginTop: 2 }}>{value}</div>
                    </div>
                ))}
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
                {/* Score sparkline */}
                <div style={{ border: `1px solid ${isAnomaly ? C.red + '45' : C.border}`, background: C.panel, padding: '12px 14px' }}>
                    <div style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, letterSpacing: 2, color: C.muted, marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
                        <span><Cpu size={9} style={{ marginRight: 5 }} />MODEL 1 SCORE — LIVE HISTORY</span>
                        <span style={{ color: isAnomaly ? C.red : C.green }}>{scoreHistory.length} samples collected</span>
                    </div>
                    <Sparkline history={scoreHistory} color={isAnomaly ? C.red : C.cyan} threshold={threshold} />
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginTop: 10 }}>
                        {[
                            ['CURRENT', score?.toFixed(5), isAnomaly ? C.red : C.green],
                            ['MIN (session)', scoreHistory.length > 0 ? Math.min(...scoreHistory).toFixed(5) : '—', C.cyan],
                            ['MAX (session)', scoreHistory.length > 0 ? Math.max(...scoreHistory).toFixed(5) : '—', C.amber],
                        ].map(([k, v, c]) => (
                            <div key={k} style={{ padding: '6px 10px', border: `1px solid ${C.border}`, background: C.base }}>
                                <div style={{ fontSize: 7, color: C.muted, fontFamily: 'monospace' }}>{k}</div>
                                <div style={{ fontSize: 12, fontWeight: 800, fontFamily: 'monospace', color: c as string }}>{v ?? '—'}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Threshold meter */}
                <div style={{ border: `1px solid ${C.border}`, background: C.panel, padding: '12px 14px' }}>
                    <div style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, letterSpacing: 2, color: C.muted, marginBottom: 8 }}>THRESHOLD PROXIMITY</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{ flex: 1, height: 10, background: C.base, border: `1px solid ${C.border}`, borderRadius: 2, overflow: 'hidden' }}>
                            <div style={{
                                width: `${Math.min(pct ?? 0, 100)}%`, height: '100%',
                                background: pct != null && pct > 85 ? C.red : pct != null && pct > 60 ? C.amber : C.green,
                                transition: 'width 0.5s ease',
                            }} />
                        </div>
                        <span style={{ fontSize: 9, fontFamily: 'monospace', color: C.muted, whiteSpace: 'nowrap' }}>
                            {pct != null ? `${pct.toFixed(1)}% of threshold` : '— %'}
                        </span>
                    </div>
                    <div style={{ fontSize: 7, color: C.muted, fontFamily: 'monospace', marginTop: 4 }}>
                        Score {score?.toFixed(4) ?? '—'} / Threshold {threshold?.toFixed(4) ?? '—'}
                        {pct != null && pct > 100 && <span style={{ color: C.red, marginLeft: 8 }}>⚠ THRESHOLD BREACHED</span>}
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    {/* Model 1 details */}
                    <div style={{ border: `1px solid ${C.border}`, background: C.panel, padding: '12px 14px' }}>
                        <div style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, letterSpacing: 2, color: C.muted, marginBottom: 10 }}>
                            <Activity size={9} style={{ marginRight: 5 }} />MODEL 1 — LSTM-VAE DETAILS
                        </div>
                        <KV k="Algorithm" v="LSTM Variational Autoencoder" />
                        <KV k="Input Features" v="20 (5-sec sliding window)" vc={C.cyan} />
                        <KV k="Sequence Length" v="As per schema" />
                        <KV k="Detection Method" v="Reconstruction MSE" />
                        <KV k="Threshold (fixed)" v={threshold?.toFixed(5) ?? '—'} vc={C.amber} />
                        <KV k="Model Status" v={mlStatus?.model1?.toUpperCase() ?? 'N/A'} vc={sc(mlStatus?.model1)} />
                        <KV k="Kafka Telemetry" v={mlStatus?.telemetry?.toUpperCase() ?? 'N/A'} vc={sc(mlStatus?.telemetry)} />
                        <KV k="Last Inference" v={latest?.timestamp?.split('T')[1]?.slice(0, 8) ?? '—'} />
                    </div>

                    {/* Affected services */}
                    <div style={{ border: `1px solid ${C.border}`, background: C.panel, padding: '12px 14px' }}>
                        <div style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, letterSpacing: 2, color: C.muted, marginBottom: 10 }}>AFFECTED SERVICES</div>
                        {nodes.length === 0 ? (
                            <div style={{ fontSize: 9, color: C.muted, fontStyle: 'italic' }}>Polling topology…</div>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                                {nodes.map(n => {
                                    const color = sc(n.status);
                                    return (
                                        <div key={n.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '5px 8px', background: C.base, border: `1px solid ${color}30` }}>
                                            <span style={{ fontSize: 9, fontFamily: 'monospace', color: C.text }}>{n.name}</span>
                                            <span style={{ fontSize: 7, fontFamily: 'monospace', fontWeight: 700, color, padding: '1px 6px', background: `${color}12`, border: `1px solid ${color}40` }}>
                                                {n.status?.toUpperCase() ?? 'UNKNOWN'}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                        {!isAnomaly && nodes.length > 0 && (
                            <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 5 }}>
                                <CheckCircle size={10} color={C.green} />
                                <span style={{ fontSize: 8, fontFamily: 'monospace', color: C.green }}>All services nominal</span>
                            </div>
                        )}
                        {isAnomaly && (
                            <div style={{ marginTop: 10, padding: '6px 8px', background: `${C.red}08`, border: `1px solid ${C.red}35`, fontSize: 8, fontFamily: 'monospace', color: C.red }}>
                                ⚠ Anomaly detected — check Incidents page for RCA
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
