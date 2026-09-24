import { useEffect, useRef, useMemo, useState } from 'react';
import { useData } from '../DataContext';
import { type TopologyNode, type TopologyEdge } from '../api';
import { Radio, Server, Cpu, Activity, GitBranch } from 'lucide-react';

const C = {
    green: '#37d67a', amber: '#f4b141', red: '#ff4b4b',
    cyan: '#00d2ff', purple: '#9d4edd', muted: '#8b92a5',
    border: '#1e2230', panel: '#0c0d11', base: '#09090c', text: '#e2e4e9',
};

function sc(s?: string | null): string {
    const u = (s ?? '').toUpperCase();
    if (['HEALTHY', 'READY', 'NORMAL', 'ONLINE', 'FLOWING', 'ACTIVE'].some(x => u.includes(x))) return C.green;
    if (['DEGRADED', 'WARNING', 'BLOCKED', 'IMPACTED'].some(x => u.includes(x))) return C.amber;
    if (['FAILED', 'CRITICAL', 'ANOMALY', 'ERROR', 'DISCONNECTED'].some(x => u.includes(x))) return C.red;
    return C.cyan;
}

function Sparkline({ history, color, threshold, height = 60, label }: {
    history: number[]; color: string; threshold?: number; height?: number; label?: string;
}) {
    if (history.length < 2) {
        return (
            <div style={{ height, border: `1px solid ${C.border}`, background: C.base, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: 8, color: C.muted, fontFamily: 'monospace' }}>{label ?? 'Collecting data…'}</span>
            </div>
        );
    }
    const W = 600, H = height;
    const allVals = threshold ? [...history, threshold] : history;
    const max = Math.max(...allVals, 0.001) * 1.15;
    const step = W / (history.length - 1);
    const pts = history.map((v, i) => `${i * step},${H - (v / max) * H}`).join(' ');
    const thY = threshold ? H - (threshold / max) * H : null;
    return (
        <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} style={{ display: 'block', overflow: 'visible' }}>
            {thY !== null && (
                <>
                    <line x1={0} y1={thY} x2={W} y2={thY} stroke={C.amber} strokeWidth={1} strokeDasharray="5 3" opacity={0.7} />
                    <text x={W - 4} y={thY - 4} fontSize={8} fill={C.amber} textAnchor="end" fontFamily="monospace">THRESHOLD</text>
                </>
            )}
            <polyline points={`0,${H} ${pts} ${(history.length - 1) * step},${H}`} fill={color} fillOpacity={0.07} stroke="none" />
            <polyline points={pts} fill="none" stroke={color} strokeWidth={1.8} strokeLinejoin="round" />
            <circle cx={(history.length - 1) * step} cy={H - (history[history.length - 1] / max) * H} r={4} fill={color} />
        </svg>
    );
}

function StatusTimeline({ history }: { history: { status: string; at: string }[] }) {
    if (history.length === 0) return <div style={{ fontSize: 8, color: C.muted, fontFamily: 'monospace', fontStyle: 'italic' }}>No state changes recorded this session.</div>;
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {history.slice().reverse().map((h, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 9, fontFamily: 'monospace' }}>
                    <span style={{ color: C.muted }}>{h.at}</span>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: sc(h.status), display: 'inline-block', flexShrink: 0 }} />
                    <span style={{ color: sc(h.status), fontWeight: 700 }}>{h.status.toUpperCase()}</span>
                </div>
            ))}
        </div>
    );
}

export default function LiveTelemetry() {
    // ── consume global data — instantly available, no local polling needed ──
    const { latest, topology, status: mlStatus, lastUpdated, apiOk, scoreHistory } = useData();

    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [filter, setFilter] = useState<'ALL' | 'HEALTHY' | 'DEGRADED' | 'FAILED'>('ALL');

    // Per-service status-change timeline (session only — recorded locally)
    const statusHistory = useRef<Record<string, { status: string; at: string }[]>>({});
    const prevStatus = useRef<Record<string, string>>({});

    const nodes: TopologyNode[] = topology?.nodes ?? [];
    const edges: TopologyEdge[] = topology?.edges ?? [];

    // Track state transitions locally (data already arrives from context)
    useEffect(() => {
        for (const node of nodes) {
            const prev = prevStatus.current[node.id];
            const curr = node.status ?? 'UNKNOWN';
            if (!statusHistory.current[node.id]) statusHistory.current[node.id] = [];
            if (prev === undefined) {
                statusHistory.current[node.id].push({ status: curr, at: new Date().toLocaleTimeString('en-GB') + ' (startup)' });
            } else if (prev !== curr) {
                statusHistory.current[node.id].push({ status: curr, at: new Date().toLocaleTimeString('en-GB') });
            }
            prevStatus.current[node.id] = curr;
        }
    }, [nodes]);

    const isAnomaly = !!latest?.anomaly?.detected ||
        nodes.some(n => ['FAILED', 'CRITICAL', 'BLOCKED'].includes(n.status?.toUpperCase() ?? ''));
    const rootCause = latest?.root_cause?.service;

    // Auto-select on first data
    useEffect(() => {
        if (!selectedId && nodes.length > 0) {
            const failed = nodes.find(n => ['FAILED', 'CRITICAL', 'BLOCKED'].includes(n.status?.toUpperCase() ?? ''));
            setSelectedId(failed?.id ?? nodes[0].id);
        }
    }, [nodes, selectedId]);

    const filteredNodes = useMemo(() => nodes.filter(n => {
        if (filter === 'ALL') return true;
        if (filter === 'HEALTHY') return ['HEALTHY', 'READY', 'NORMAL'].includes(n.status?.toUpperCase() ?? '');
        if (filter === 'DEGRADED') return ['DEGRADED', 'WARNING', 'BLOCKED'].includes(n.status?.toUpperCase() ?? '');
        if (filter === 'FAILED') return ['FAILED', 'CRITICAL'].includes(n.status?.toUpperCase() ?? '');
        return true;
    }), [nodes, filter]);

    const selected = nodes.find(n => n.id === selectedId) ?? null;
    const selColor = sc(selected?.status);
    const selHistory = selectedId ? (statusHistory.current[selectedId] ?? []) : [];
    const isRoot = selected && (selected.name === rootCause || selected.id === rootCause);

    const upstreams = edges.filter(e => e.target === selected?.id || e.target === selected?.name)
        .map(e => nodes.find(n => n.id === e.source || n.name === e.source))
        .filter(Boolean) as TopologyNode[];
    const downstreams = edges.filter(e => e.source === selected?.id || e.source === selected?.name)
        .map(e => nodes.find(n => n.id === e.target || n.name === e.target))
        .filter(Boolean) as TopologyNode[];

    const failCount = nodes.filter(n => ['FAILED', 'CRITICAL'].includes(n.status?.toUpperCase() ?? '')).length;
    const blockCount = nodes.filter(n => n.status?.toUpperCase() === 'BLOCKED').length;
    const healthyCount = nodes.filter(n => ['HEALTHY', 'READY', 'NORMAL'].includes(n.status?.toUpperCase() ?? '')).length;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', background: C.base }}>
            {/* Header */}
            <div style={{ padding: '8px 16px', background: C.panel, borderBottom: `1px solid ${C.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <Radio size={16} color={C.cyan} />
                    <span style={{ fontSize: 13, fontWeight: 800, letterSpacing: 3, color: C.text, fontFamily: 'monospace' }}>LIVE TELEMETRY</span>
                    {isAnomaly && <span style={{ fontSize: 7, padding: '2px 8px', border: `1px solid ${C.red}50`, color: C.red, background: `${C.red}12`, fontFamily: 'monospace', fontWeight: 700 }}>ANOMALY ACTIVE</span>}
                </div>
                <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
                    {apiOk === false
                        ? <span style={{ fontSize: 7, color: C.red, fontFamily: 'monospace' }}>BACKEND OFFLINE</span>
                        : <span style={{ fontSize: 8, color: C.green, fontFamily: 'monospace' }}>● LIVE · 2s</span>}
                    <span style={{ fontSize: 8, color: C.muted, fontFamily: 'monospace' }}>{lastUpdated}</span>
                </div>
            </div>

            {/* KPI strip */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', background: C.panel, borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
                {[
                    { label: 'SERVICES', value: nodes.length || '…', color: C.text },
                    { label: 'HEALTHY', value: healthyCount, color: C.green },
                    { label: 'BLOCKED', value: blockCount, color: blockCount > 0 ? C.amber : C.muted },
                    { label: 'FAILED', value: failCount, color: failCount > 0 ? C.red : C.muted },
                    { label: 'MODEL 1', value: latest?.anomaly?.score?.toFixed(4) ?? '…', color: isAnomaly ? C.red : C.text },
                    { label: 'KAFKA', value: mlStatus?.telemetry?.toUpperCase() ?? '…', color: sc(mlStatus?.telemetry) },
                ].map(({ label, value, color }, i, arr) => (
                    <div key={label} style={{ padding: '7px 14px', borderRight: i < arr.length - 1 ? `1px solid ${C.border}` : 'none' }}>
                        <div style={{ fontSize: 7, fontFamily: 'monospace', letterSpacing: 2, color: C.muted }}>{label}</div>
                        <div style={{ fontSize: 13, fontWeight: 800, fontFamily: 'monospace', color }}>{value}</div>
                    </div>
                ))}
            </div>

            {/* Master-detail */}
            <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '220px 1fr', overflow: 'hidden' }}>
                {/* LEFT: service list */}
                <div style={{ borderRight: `1px solid ${C.border}`, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: C.panel }}>
                    <div style={{ padding: '8px 10px', borderBottom: `1px solid ${C.border}`, display: 'flex', gap: 4, flexWrap: 'wrap', flexShrink: 0 }}>
                        {(['ALL', 'HEALTHY', 'DEGRADED', 'FAILED'] as const).map(f => (
                            <button key={f} onClick={() => setFilter(f)} style={{
                                fontSize: 7, padding: '2px 7px', cursor: 'pointer', fontFamily: 'monospace', fontWeight: 700, letterSpacing: 1,
                                background: filter === f ? `${C.cyan}18` : 'transparent',
                                border: filter === f ? `1px solid ${C.cyan}` : `1px solid ${C.border}`,
                                color: filter === f ? C.cyan : C.muted,
                            }}>{f}</button>
                        ))}
                    </div>
                    <div style={{ flex: 1, overflowY: 'auto' }}>
                        {filteredNodes.length === 0 && (
                            <div style={{ padding: 12, fontSize: 9, color: C.muted, fontFamily: 'monospace', fontStyle: 'italic' }}>No services match filter.</div>
                        )}
                        {filteredNodes.map(n => {
                            const color = sc(n.status);
                            const isSel = n.id === selectedId;
                            const isRootNode = n.name === rootCause || n.id === rootCause;
                            return (
                                <button key={n.id} onClick={() => setSelectedId(n.id)} style={{
                                    width: '100%', textAlign: 'left', cursor: 'pointer', padding: '8px 12px',
                                    background: isSel ? `${color}12` : 'transparent',
                                    borderLeft: isSel ? `2px solid ${color}` : '2px solid transparent',
                                    borderBottom: `1px solid ${C.border}`, borderTop: 'none', borderRight: 'none',
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                                            <span style={{ width: 7, height: 7, borderRadius: '50%', background: color, flexShrink: 0, display: 'inline-block' }} />
                                            <div>
                                                <div style={{ fontSize: 9, fontWeight: 700, fontFamily: 'monospace', color: C.text }}>{n.name}</div>
                                                <div style={{ fontSize: 7, color: C.muted, marginTop: 1 }}>{n.type}</div>
                                            </div>
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 2 }}>
                                            <span style={{ fontSize: 6, fontFamily: 'monospace', fontWeight: 700, color }}>{n.status?.toUpperCase() ?? '—'}</span>
                                            {isRootNode && <span style={{ fontSize: 6, padding: '0px 4px', border: `1px solid ${C.red}40`, color: C.red, background: `${C.red}12`, fontFamily: 'monospace' }}>ROOT</span>}
                                        </div>
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                    <div style={{ padding: '6px 12px', borderTop: `1px solid ${C.border}`, fontSize: 7, color: C.muted, fontFamily: 'monospace', flexShrink: 0 }}>
                        {filteredNodes.length} / {nodes.length} services shown
                    </div>
                </div>

                {/* RIGHT: detail */}
                {selected ? (
                    <div style={{ overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
                        {/* Service header */}
                        <div style={{ border: `1px solid ${selColor}45`, background: `${selColor}06`, padding: '12px 14px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <Server size={15} color={selColor} />
                                        <span style={{ fontSize: 15, fontWeight: 900, fontFamily: 'monospace', color: C.text, letterSpacing: 2 }}>
                                            {selected.name.toUpperCase().replace(/-/g, ' ')}
                                        </span>
                                        {isRoot && <span style={{ fontSize: 7, padding: '2px 8px', border: `1px solid ${C.red}50`, color: C.red, background: `${C.red}12`, fontFamily: 'monospace', fontWeight: 700 }}>ROOT CAUSE</span>}
                                    </div>
                                    <div style={{ fontSize: 8, color: C.muted, marginTop: 3 }}>{selected.type} · namespace: {selected.namespace}</div>
                                </div>
                                <span style={{ fontSize: 9, fontFamily: 'monospace', fontWeight: 800, padding: '4px 12px', border: `1px solid ${selColor}50`, color: selColor, background: `${selColor}12` }}>
                                    ● {selected.status?.toUpperCase() ?? 'UNKNOWN'}
                                </span>
                            </div>
                        </div>

                        {/* Quick metrics */}
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
                            {[
                                { label: 'STATUS', value: selected.status?.toUpperCase() ?? 'N/A', color: selColor },
                                { label: 'TYPE', value: selected.type ?? 'N/A', color: C.cyan },
                                { label: 'NAMESPACE', value: selected.namespace ?? 'N/A', color: C.muted },
                                { label: 'STATE CHANGES', value: String(selHistory.length) + ' this session', color: selHistory.length > 1 ? C.amber : C.muted },
                            ].map(({ label, value, color }) => (
                                <div key={label} style={{ padding: '8px 10px', border: `1px solid ${C.border}`, background: C.panel }}>
                                    <div style={{ fontSize: 7, color: C.muted, fontFamily: 'monospace', letterSpacing: 1 }}>{label}</div>
                                    <div style={{ fontSize: 10, fontWeight: 800, fontFamily: 'monospace', color, marginTop: 3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{value}</div>
                                </div>
                            ))}
                        </div>

                        {/* Score sparkline */}
                        <div style={{ border: `1px solid ${isAnomaly ? C.red + '45' : C.border}`, background: C.panel, padding: '12px 14px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                <div style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, letterSpacing: 2, color: isAnomaly ? C.red : C.muted }}>
                                    <Cpu size={9} style={{ marginRight: 5 }} />MODEL 1 ANOMALY SCORE (SYSTEM)
                                </div>
                                <div style={{ display: 'flex', gap: 12, fontSize: 8, fontFamily: 'monospace' }}>
                                    <span style={{ color: isAnomaly ? C.red : C.green, fontWeight: 700 }}>{latest?.anomaly?.score?.toFixed(5) ?? '—'}</span>
                                    <span style={{ color: C.muted }}>/ {latest?.anomaly?.threshold?.toFixed(5) ?? '—'}</span>
                                </div>
                            </div>
                            <Sparkline history={scoreHistory} color={isAnomaly ? C.red : C.cyan} threshold={latest?.anomaly?.threshold} height={70} label="Waiting for Model 1 score…" />
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6, marginTop: 8 }}>
                                {[
                                    ['CURRENT', latest?.anomaly?.score?.toFixed(5) ?? '—', isAnomaly ? C.red : C.green],
                                    ['MIN (session)', scoreHistory.length > 0 ? Math.min(...scoreHistory).toFixed(5) : '—', C.cyan],
                                    ['MAX (session)', scoreHistory.length > 0 ? Math.max(...scoreHistory).toFixed(5) : '—', C.amber],
                                ].map(([k, v, col]) => (
                                    <div key={k} style={{ padding: '5px 8px', border: `1px solid ${C.border}`, background: C.base }}>
                                        <div style={{ fontSize: 7, color: C.muted, fontFamily: 'monospace' }}>{k}</div>
                                        <div style={{ fontSize: 9, fontWeight: 800, fontFamily: 'monospace', color: col as string, marginTop: 1 }}>{v}</div>
                                    </div>
                                ))}
                            </div>
                            {isRoot && (
                                <div style={{ marginTop: 8, padding: '5px 8px', background: `${C.red}0a`, border: `1px solid ${C.red}35`, fontSize: 8, fontFamily: 'monospace', color: C.red }}>
                                    ⚠ Root cause confirmed. GraphSAGE confidence: {latest?.root_cause?.score != null ? (latest.root_cause.score * 100).toFixed(1) + '%' : 'N/A'}
                                </div>
                            )}
                        </div>

                        {/* State change timeline */}
                        <div style={{ border: `1px solid ${C.border}`, background: C.panel, padding: '12px 14px' }}>
                            <div style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, letterSpacing: 2, color: C.muted, marginBottom: 10 }}>
                                <Activity size={9} style={{ marginRight: 5 }} />STATE CHANGE TIMELINE (CURRENT SESSION)
                            </div>
                            <StatusTimeline history={selHistory} />
                        </div>

                        {/* Dependencies */}
                        {(upstreams.length > 0 || downstreams.length > 0) && (
                            <div style={{ border: `1px solid ${C.border}`, background: C.panel, padding: '12px 14px' }}>
                                <div style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, letterSpacing: 2, color: C.muted, marginBottom: 10 }}>
                                    <GitBranch size={9} style={{ marginRight: 5 }} />DEPENDENCIES
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                                    {[
                                        { title: 'UPSTREAM (calls this service)', list: upstreams },
                                        { title: 'DOWNSTREAM (this service calls)', list: downstreams },
                                    ].map(({ title, list }) => (
                                        <div key={title}>
                                            <div style={{ fontSize: 7, color: C.muted, fontFamily: 'monospace', marginBottom: 6 }}>{title}</div>
                                            {list.length === 0
                                                ? <div style={{ fontSize: 8, color: C.muted, fontStyle: 'italic' }}>None</div>
                                                : list.map(dep => {
                                                    const dc = sc(dep.status);
                                                    return (
                                                        <div key={dep.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '5px 8px', marginBottom: 4, background: C.base, border: `1px solid ${dc}30` }}>
                                                            <span style={{ fontSize: 9, fontFamily: 'monospace', color: C.text }}>{dep.name}</span>
                                                            <span style={{ fontSize: 7, fontFamily: 'monospace', fontWeight: 700, color: dc }}>{dep.status?.toUpperCase() ?? '—'}</span>
                                                        </div>
                                                    );
                                                })}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* RCA context */}
                        {(isRoot || (isAnomaly && rootCause)) && (
                            <div style={{ border: `1px solid ${C.purple}45`, background: `${C.purple}06`, padding: '12px 14px' }}>
                                <div style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, letterSpacing: 2, color: C.purple, marginBottom: 10 }}>GRAPHSAGE V2 — RCA CONTEXT</div>
                                {[
                                    ['Root Cause Service', rootCause ?? 'Evaluating…', rootCause ? C.red : C.amber],
                                    ['Confidence Score', latest?.root_cause?.score != null ? (latest.root_cause.score * 100).toFixed(2) + '%' : 'N/A', C.purple],
                                    ['RCA Status', latest?.root_cause?.status?.replace(/_/g, ' ').toUpperCase() ?? 'N/A', C.cyan],
                                    ['This Service', isRoot ? 'CONFIRMED ROOT CAUSE' : 'NOT ROOT CAUSE', isRoot ? C.red : C.green],
                                ].map(([k, v, vc]) => (
                                    <div key={k} style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 6, marginBottom: 6, borderBottom: `1px solid ${C.border}`, fontSize: 9, fontFamily: 'monospace' }}>
                                        <span style={{ color: C.muted }}>{k}</span>
                                        <span style={{ color: vc as string, fontWeight: 700 }}>{v}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ) : (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 10 }}>
                        <Server size={32} color={C.border} />
                        <div style={{ fontSize: 10, fontFamily: 'monospace', color: C.muted }}>Select a service from the list</div>
                    </div>
                )}
            </div>
        </div>
    );
}
