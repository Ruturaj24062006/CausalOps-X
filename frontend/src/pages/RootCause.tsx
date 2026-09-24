import { useData } from '../DataContext';
import { GitBranch, ChevronRight, CheckCircle, AlertOctagon } from 'lucide-react';

const C = {
    green: '#37d67a', amber: '#f4b141', red: '#ff4b4b',
    cyan: '#00d2ff', purple: '#9d4edd', muted: '#8b92a5',
    border: '#1e2230', panel: '#0c0d11', base: '#09090c', text: '#e2e4e9',
};

function sc(s?: string | null): string {
    const u = (s ?? '').toUpperCase();
    if (['HEALTHY', 'READY', 'NORMAL', 'ONLINE', 'FLOWING', 'ACTIVE', 'CONFIRMED', 'SUCCESS'].some(x => u.includes(x))) return C.green;
    if (['DEGRADED', 'WARNING', 'BLOCKED', 'EVALUATING'].some(x => u.includes(x))) return C.amber;
    if (['FAILED', 'CRITICAL', 'ANOMALY', 'ERROR'].some(x => u.includes(x))) return C.red;
    return C.cyan;
}

function KV({ k, v, vc }: { k: string; v: string; vc?: string }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: 6, marginBottom: 6, borderBottom: `1px solid ${C.border}` }}>
            <span style={{ fontSize: 9, color: C.muted, fontFamily: 'monospace' }}>{k}</span>
            <span style={{ fontSize: 9, fontFamily: 'monospace', fontWeight: 700, color: vc ?? C.text, maxWidth: 200, textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{v}</span>
        </div>
    );
}

export default function RootCause() {
    // ── consume global data — no local useEffect/polling needed ──
    const { latest, topology, status: mlStatus, lastUpdated } = useData();

    const nodes = topology?.nodes ?? [];
    const edges = topology?.edges ?? [];
    const rootCause = latest?.root_cause?.service;
    const rcaScore = latest?.root_cause?.score;
    const rcaStatus = latest?.root_cause?.status;
    const rcaNodeIdx = latest?.root_cause?.node_index;
    const rcaMissing = latest?.root_cause?.missing_requirements ?? [];
    const isAnomaly = !!latest?.anomaly?.detected ||
        nodes.some(n => ['FAILED', 'CRITICAL', 'BLOCKED'].includes(n.status?.toUpperCase() ?? ''));
    const badNodes = nodes.filter(n => !['HEALTHY', 'READY', 'NORMAL'].includes(n.status?.toUpperCase() ?? ''));

    // Causal chain
    const rootNode = nodes.find(n => n.name === rootCause || n.id === rootCause);
    const affected = nodes.filter(n => n !== rootNode && !['HEALTHY', 'READY', 'NORMAL'].includes(n.status?.toUpperCase() ?? ''));
    const healthy = nodes.filter(n => ['HEALTHY', 'READY', 'NORMAL'].includes(n.status?.toUpperCase() ?? ''));

    type ChainItem = { node: typeof nodes[0]; label: string; color: string };
    const chain: ChainItem[] = [];
    if (rootNode) chain.push({ node: rootNode, label: 'ROOT CAUSE', color: C.red });
    affected.forEach(n => chain.push({ node: n, label: 'IMPACTED', color: C.amber }));
    healthy.slice(0, 2).forEach(n => chain.push({ node: n, label: 'HEALTHY', color: C.green }));

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', background: C.base }}>
            {/* Header */}
            <div style={{ padding: '8px 16px', background: C.panel, borderBottom: `1px solid ${C.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <GitBranch size={16} color={C.purple} />
                    <span style={{ fontSize: 14, fontWeight: 800, letterSpacing: 3, color: C.text, fontFamily: 'monospace' }}>ROOT CAUSE ANALYSIS</span>
                    <span style={{ fontSize: 7, padding: '2px 8px', border: `1px solid ${C.purple}50`, color: C.purple, background: `${C.purple}12`, fontFamily: 'monospace', fontWeight: 700 }}>GraphSAGE V2</span>
                    {rootCause && <span style={{ fontSize: 7, padding: '2px 8px', border: `1px solid ${C.red}50`, color: C.red, background: `${C.red}12`, fontFamily: 'monospace', fontWeight: 700 }}>ROOT CAUSE IDENTIFIED</span>}
                </div>
                <span style={{ fontSize: 8, color: C.muted, fontFamily: 'monospace' }}>Updated: {lastUpdated}</span>
            </div>

            {/* KPI Ribbon */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', background: C.panel, borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
                {[
                    { label: 'ROOT CAUSE SERVICE', value: rootCause ?? (isAnomaly ? 'EVALUATING…' : 'N/A'), color: rootCause ? C.red : isAnomaly ? C.amber : C.muted },
                    { label: 'CONFIDENCE SCORE', value: rcaScore != null ? (rcaScore * 100).toFixed(1) + '%' : 'N/A', color: rcaScore ? C.purple : C.muted },
                    { label: 'RCA STATUS', value: rcaStatus?.replace(/_/g, ' ').toUpperCase() ?? 'N/A', color: sc(rcaStatus) },
                    { label: 'NODE INDEX', value: rcaNodeIdx?.toString() ?? 'N/A', color: C.cyan },
                    { label: 'AFFECTED SERVICES', value: String(badNodes.length), color: badNodes.length > 0 ? C.amber : C.muted },
                ].map(({ label, value, color }, i, arr) => (
                    <div key={label} style={{ padding: '8px 14px', borderRight: i < arr.length - 1 ? `1px solid ${C.border}` : 'none' }}>
                        <div style={{ fontSize: 7, fontFamily: 'monospace', letterSpacing: 2, color: C.muted }}>{label}</div>
                        <div style={{ fontSize: 12, fontWeight: 800, fontFamily: 'monospace', color, marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{value}</div>
                    </div>
                ))}
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
                {/* Causal chain */}
                <div style={{ border: `1px solid ${rootCause ? C.purple + '45' : C.border}`, background: rootCause ? `${C.purple}06` : C.panel, padding: '12px 14px' }}>
                    <div style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, letterSpacing: 2, color: C.muted, marginBottom: 10 }}>
                        <GitBranch size={9} style={{ marginRight: 5 }} />CAUSAL PROPAGATION CHAIN
                    </div>
                    {chain.length === 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '24px 0', gap: 8 }}>
                            <CheckCircle size={22} color={C.green} />
                            <div style={{ fontSize: 10, fontFamily: 'monospace', color: C.green, letterSpacing: 2 }}>NO ACTIVE ROOT CAUSE</div>
                            <div style={{ fontSize: 8, color: C.muted }}>GraphSAGE V2 is on standby.</div>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', alignItems: 'flex-start', flexWrap: 'wrap', gap: 4 }}>
                            {chain.map(({ node, label, color }, i) => (
                                <div key={node.id} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                    <div style={{ padding: '10px 14px', border: `1px solid ${color}45`, background: `${color}08`, minWidth: 110 }}>
                                        <div style={{ fontSize: 10, fontWeight: 800, fontFamily: 'monospace', color, letterSpacing: 1 }}>
                                            {node.name.replace(/-/g, ' ').toUpperCase()}
                                        </div>
                                        <div style={{ fontSize: 7, color: C.muted, marginTop: 3 }}>
                                            <span style={{ color, fontWeight: 700 }}>●</span> {label} · {node.status?.toUpperCase() ?? '—'}
                                        </div>
                                    </div>
                                    {i < chain.length - 1 && <ChevronRight size={14} color={C.border} />}
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    {/* GraphSAGE panel */}
                    <div style={{ border: `1px solid ${rootCause ? C.purple + '45' : C.border}`, background: C.panel, padding: '12px 14px' }}>
                        <div style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, letterSpacing: 2, color: C.purple, marginBottom: 10 }}>
                            GRAPHSAGE V2 — INFERENCE RESULT
                        </div>
                        {rootCause ? (
                            <>
                                <div style={{ padding: '10px 12px', background: `${C.red}0a`, border: `1px solid ${C.red}40`, marginBottom: 10 }}>
                                    <div style={{ fontSize: 7, color: C.muted, fontFamily: 'monospace', marginBottom: 3 }}>CONFIRMED ROOT CAUSE</div>
                                    <div style={{ fontSize: 18, fontWeight: 900, fontFamily: 'monospace', color: C.red }}>{rootCause}</div>
                                </div>
                                <KV k="Confidence" v={rcaScore != null ? (rcaScore * 100).toFixed(2) + '%' : 'N/A'} vc={C.purple} />
                                <KV k="Node Index" v={rcaNodeIdx?.toString() ?? 'N/A'} vc={C.cyan} />
                                <KV k="RCA Status" v={rcaStatus?.replace(/_/g, ' ').toUpperCase() ?? 'N/A'} vc={sc(rcaStatus)} />
                                <KV k="Model 2" v={mlStatus?.model2?.toUpperCase() ?? 'N/A'} vc={sc(mlStatus?.model2)} />
                            </>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                {isAnomaly ? (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px', border: `1px solid ${C.amber}40`, background: `${C.amber}08` }}>
                                        <AlertOctagon size={14} color={C.amber} />
                                        <div>
                                            <div style={{ fontSize: 9, fontFamily: 'monospace', color: C.amber, fontWeight: 700 }}>GRAPHSAGE V2 EVALUATING…</div>
                                            <div style={{ fontSize: 8, color: C.muted, marginTop: 2 }}>Analysing causal graph</div>
                                        </div>
                                    </div>
                                ) : (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px', border: `1px solid ${C.green}35`, background: `${C.green}06` }}>
                                        <CheckCircle size={14} color={C.green} />
                                        <div>
                                            <div style={{ fontSize: 9, fontFamily: 'monospace', color: C.green, fontWeight: 700 }}>NOT TRIGGERED</div>
                                            <div style={{ fontSize: 8, color: C.muted, marginTop: 2 }}>No anomaly detected — on standby</div>
                                        </div>
                                    </div>
                                )}
                                <KV k="RCA Status" v={rcaStatus?.replace(/_/g, ' ').toUpperCase() ?? 'NOT TRIGGERED'} vc={sc(rcaStatus)} />
                                <KV k="Model 2" v={mlStatus?.model2?.toUpperCase() ?? 'N/A'} vc={sc(mlStatus?.model2)} />
                                {rcaMissing.length > 0 && (
                                    <div style={{ padding: '6px 8px', border: `1px solid ${C.amber}40`, background: `${C.amber}08`, fontSize: 8, fontFamily: 'monospace', color: C.amber }}>
                                        Missing: {rcaMissing.join(', ')}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Topology table */}
                    <div style={{ border: `1px solid ${C.border}`, background: C.panel, padding: '12px 14px' }}>
                        <div style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, letterSpacing: 2, color: C.muted, marginBottom: 10 }}>
                            SERVICE TOPOLOGY ({nodes.length} NODES · {edges.length} EDGES)
                        </div>
                        {nodes.length === 0 ? (
                            <div style={{ fontSize: 9, color: C.muted, fontStyle: 'italic' }}>Loading topology…</div>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                {nodes.map(n => {
                                    const isRootN = n.name === rootCause || n.id === rootCause;
                                    const color = isRootN ? C.red : sc(n.status);
                                    return (
                                        <div key={n.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '5px 8px', background: isRootN ? `${C.red}09` : C.base, border: `1px solid ${isRootN ? C.red + '40' : C.border}` }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                                                <span style={{ width: 6, height: 6, borderRadius: '50%', background: color, display: 'inline-block' }} />
                                                <span style={{ fontSize: 9, fontFamily: 'monospace', color: C.text, fontWeight: isRootN ? 800 : 400 }}>{n.name}</span>
                                                {isRootN && <span style={{ fontSize: 6, padding: '0px 4px', border: `1px solid ${C.red}50`, color: C.red, background: `${C.red}12`, fontFamily: 'monospace' }}>ROOT</span>}
                                            </div>
                                            <span style={{ fontSize: 7, fontFamily: 'monospace', fontWeight: 700, color, padding: '1px 6px', background: `${color}12`, border: `1px solid ${color}40` }}>
                                                {n.status?.toUpperCase() ?? 'UNKNOWN'}
                                            </span>
                                        </div>
                                    );
                                })}
                                <div style={{ marginTop: 6, fontSize: 7, color: C.muted, fontFamily: 'monospace' }}>
                                    {edges.map((e, i) => <div key={i}>{e.source} → {e.target} [{e.type}]</div>)}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Model 2 architecture */}
                <div style={{ border: `1px solid ${C.border}`, background: C.panel, padding: '12px 14px' }}>
                    <div style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, letterSpacing: 2, color: C.muted, marginBottom: 10 }}>MODEL 2 — GRAPHSAGE V2 ARCHITECTURE</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
                        {[
                            ['Framework', 'PyTorch Geometric'],
                            ['Architecture', 'GraphSAGE V2 (GNN)'],
                            ['Node Features', '20-dim telemetry vector'],
                            ['Edge Features', '2 (latency, error_rate)'],
                            ['Input', 'Service topology graph'],
                            ['Output', 'Root cause + confidence'],
                            ['Status', mlStatus?.model2?.toUpperCase() ?? 'N/A'],
                            ['Trigger', 'Model 1 anomaly confirmed'],
                        ].map(([k, v]) => (
                            <div key={k} style={{ padding: '7px 10px', border: `1px solid ${C.border}`, background: C.base }}>
                                <div style={{ fontSize: 7, color: C.muted, fontFamily: 'monospace', letterSpacing: 1 }}>{k}</div>
                                <div style={{ fontSize: 8, fontWeight: 700, fontFamily: 'monospace', color: k === 'Status' ? sc(mlStatus?.model2) : C.text, marginTop: 2 }}>{v}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
