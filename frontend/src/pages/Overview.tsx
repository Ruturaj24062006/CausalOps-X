import { useEffect, useState, useRef, useMemo, useCallback } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import * as THREE from 'three';
import {
    fetchStatus, fetchLatest, fetchTopology,
    type MLStatus, type MLLatest, type TopologyData, type TopologyNode
} from '../api';
import { CheckCircle, AlertOctagon, Activity, GitBranch, Radio, RefreshCw } from 'lucide-react';

// ─── Colour utils ────────────────────────────────────────────────────────────

function nodeColor(status?: string | null, isRoot = false, isAnomaly = false): string {
    if (isRoot) return '#ff4b4b';
    if (isAnomaly) return '#ff8800';
    const s = status?.toUpperCase() ?? '';
    if (['HEALTHY', 'READY', 'NORMAL'].includes(s)) return '#37d67a';
    if (['DEGRADED', 'WARNING', 'BLOCKED'].includes(s)) return '#f4b141';
    if (['FAILED', 'CRITICAL', 'ANOMALY'].includes(s)) return '#ff4b4b';
    return '#00d2ff';
}

function statusColor(s?: string | null) {
    const u = s?.toUpperCase() ?? '';
    if (['HEALTHY', 'READY', 'NORMAL', 'ONLINE', 'FLOWING', 'ACTIVE', 'OK'].some(x => u.includes(x))) return '#37d67a';
    if (['DEGRADED', 'WARNING', 'BLOCKED'].some(x => u.includes(x))) return '#f4b141';
    if (['FAILED', 'CRITICAL', 'ANOMALY', 'BREACH', 'DISCONNECTED'].some(x => u.includes(x))) return '#ff4b4b';
    return '#00d2ff';
}

function sysLabel(nodes: TopologyNode[], anomaly: boolean) {
    if (anomaly) return 'ANOMALY';
    if (nodes.some(n => ['FAILED', 'CRITICAL'].includes(n.status?.toUpperCase() ?? ''))) return 'CRITICAL';
    if (nodes.some(n => ['DEGRADED', 'BLOCKED', 'WARNING'].includes(n.status?.toUpperCase() ?? ''))) return 'DEGRADED';
    return 'HEALTHY';
}

// ─── 3D node ─────────────────────────────────────────────────────────────────

interface NodeProps {
    node: TopologyNode;
    pos: [number, number, number];
    selected: boolean;
    isRoot: boolean;
    globalAnomaly: boolean;
    onClick: () => void;
    onPointerOver: () => void;
    onPointerOut: () => void;
}

function ServiceNode({ node, pos, selected, isRoot, globalAnomaly, onClick, onPointerOver, onPointerOut }: NodeProps) {
    const coreRef = useRef<THREE.Mesh>(null);
    const haloRef = useRef<THREE.Mesh>(null);
    const t = useRef(Math.random() * Math.PI * 2);
    const color = nodeColor(node.status, isRoot, globalAnomaly && node.status?.toUpperCase() === 'FAILED');
    const r = selected ? 1.25 : 1.0;

    useFrame((_, dt) => {
        t.current += dt;
        if (coreRef.current) coreRef.current.rotation.y += dt * 0.28;
        if (haloRef.current) {
            const pulse = (isRoot || selected) ? 0.78 + Math.sin(t.current * 2.8) * 0.22 : 0.85 + Math.sin(t.current * 1.6) * 0.1;
            haloRef.current.scale.setScalar(pulse);
        }
    });

    return (
        <group position={pos} onClick={(e) => { e.stopPropagation(); onClick(); }}
            onPointerOver={(e) => { e.stopPropagation(); onPointerOver(); document.body.style.cursor = 'pointer'; }}
            onPointerOut={() => { onPointerOut(); document.body.style.cursor = 'auto'; }}>
            {/* wire cage */}
            <mesh><sphereGeometry args={[r * 1.5, 8, 8]} /><meshBasicMaterial color={color} wireframe opacity={0.1} transparent /></mesh>
            {/* glow halo */}
            <mesh ref={haloRef}>
                <sphereGeometry args={[r * 1.15, 20, 20]} />
                <meshStandardMaterial color={color} emissive={color} emissiveIntensity={isRoot ? 2 : selected ? 1.2 : 0.45} transparent opacity={0.18} />
            </mesh>
            {/* core */}
            <mesh ref={coreRef}>
                <sphereGeometry args={[r, 28, 28]} />
                <meshStandardMaterial color={color} emissive={color} emissiveIntensity={isRoot ? 1.2 : 0.7} roughness={0.2} metalness={0.5} />
            </mesh>
            {/* label */}
            <Html position={[0, -r - 0.72, 0]} center style={{ pointerEvents: 'none' }}>
                <div style={{
                    fontSize: 8, fontFamily: 'monospace', fontWeight: 700, letterSpacing: 1,
                    textTransform: 'uppercase', whiteSpace: 'nowrap', color: '#e2e4e9',
                    background: 'rgba(7,9,12,0.9)', border: `1px solid ${color}45`,
                    padding: '2px 6px',
                    boxShadow: selected || isRoot ? `0 0 10px ${color}40` : 'none',
                }}>
                    {node.name.replace(/-service$/i, '').replace(/-/g, ' ')}
                </div>
            </Html>
        </group>
    );
}

// ─── Animated edge ────────────────────────────────────────────────────────────

function ServiceEdge({ from, to, color, flow }: { from: THREE.Vector3; to: THREE.Vector3; color: string; flow: boolean }) {
    const pRef = useRef<THREE.Mesh>(null);
    const tRef = useRef(Math.random());
    const points = useMemo(() => [from.clone(), to.clone()], [from, to]);
    const geom = useMemo(() => new THREE.BufferGeometry().setFromPoints(points), [points]);
    const mat = useMemo(() => new THREE.LineBasicMaterial({ color, transparent: true, opacity: flow ? 0.8 : 0.22 }), [color, flow]);

    useFrame((_, dt) => {
        if (!flow || !pRef.current) return;
        tRef.current = (tRef.current + dt * 0.35) % 1;
        pRef.current.position.lerpVectors(from, to, tRef.current);
    });

    return (
        <group>
            <primitive object={new THREE.Line(geom, mat)} />
            {flow && (
                <mesh ref={pRef} position={from.clone()}>
                    <sphereGeometry args={[0.13, 7, 7]} />
                    <meshStandardMaterial color={color} emissive={color} emissiveIntensity={3} />
                </mesh>
            )}
        </group>
    );
}

// ─── 3D Canvas scene ─────────────────────────────────────────────────────────

function TopologyScene({
    nodesP, edges, selectedId, rootCause, anomaly,
    onSelect, onNodeEnter, onNodeLeave, camReset
}: {
    nodesP: (TopologyNode & { pos: [number, number, number] })[];
    edges: TopologyData['edges'];
    selectedId: string | null; rootCause?: string; anomaly?: boolean;
    onSelect: (id: string) => void;
    onNodeEnter: (n: TopologyNode) => void;
    onNodeLeave: () => void;
    camReset: number;
}) {
    const { camera } = useThree();

    useEffect(() => {
        if (camReset > 0) { camera.position.set(0, 8, 20); camera.lookAt(0, 0, 0); }
    }, [camReset, camera]);

    return (
        <>
            <ambientLight intensity={0.25} />
            <pointLight position={[10, 16, 10]} intensity={2} />
            <pointLight position={[-10, -6, -6]} intensity={0.5} color="#00d2ff" />
            <gridHelper args={[50, 22, '#111620', '#111620']} position={[0, -7.5, 0]} />

            {nodesP.map(n => (
                <ServiceNode key={n.id} node={n} pos={n.pos}
                    selected={selectedId === n.id}
                    isRoot={!!(rootCause && (rootCause === n.name || rootCause === n.id))}
                    globalAnomaly={!!anomaly}
                    onClick={() => onSelect(n.id)}
                    onPointerOver={() => onNodeEnter(n)}
                    onPointerOut={onNodeLeave}
                />
            ))}

            {edges.map((e, i) => {
                const src = nodesP.find(n => n.id === e.source || n.name === e.source);
                const tgt = nodesP.find(n => n.id === e.target || n.name === e.target);
                if (!src || !tgt) return null;
                const sv = new THREE.Vector3(...src.pos), tv = new THREE.Vector3(...tgt.pos);
                const isFaultPath = anomaly && (rootCause === src.name || rootCause === tgt.name);
                const col = isFaultPath ? '#9d4edd' : e.type === 'async' ? '#9d4edd50' : (anomaly ? '#ff4b4b60' : '#00d2ff');
                return <ServiceEdge key={i} from={sv} to={tv} color={col} flow={!!anomaly} />;
            })}

            <OrbitControls makeDefault enableDamping dampingFactor={0.07} autoRotate autoRotateSpeed={0.45} />
        </>
    );
}



// ─── Sparkline ────────────────────────────────────────────────────────────────

function Spark({ data, color = '#00d2ff', w = 90, h = 24 }: { data: number[]; color?: string; w?: number; h?: number }) {
    if (data.length < 2) return <div style={{ width: w, height: h, opacity: 0.2, background: `linear-gradient(90deg, transparent, ${color}20)` }} />;
    const mn = Math.min(...data), mx = Math.max(...data), rng = mx - mn || 1;
    const pts = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - mn) / rng) * (h - 3) - 2}`).join(' ');
    return (
        <svg width={w} height={h}>
            <defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity="0.3" /><stop offset="100%" stopColor={color} stopOpacity="0" /></linearGradient></defs>
            <polyline points={pts} fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" />
        </svg>
    );
}

// ─── RCA Pipeline indicator ───────────────────────────────────────────────────

function PipelineBar({ status, latest, anomaly, rootCause }: {
    status: MLStatus | null; latest: MLLatest | null; anomaly: boolean; rootCause?: string;
}) {
    const stages = [
        { id: 'kafka', label: 'KAFKA', ok: true, active: true, color: statusColor(status?.telemetry), icon: '⊕' },
        { id: 'm1', label: 'MODEL 1', ok: !anomaly, active: true, color: anomaly ? '#ff4b4b' : '#37d67a', icon: anomaly ? '▲' : '✓' },
        { id: 'seg', label: 'ANOMALY', ok: !anomaly, active: anomaly, color: anomaly ? '#f4b141' : '#2d313b', icon: anomaly ? '⚠' : '—' },
        { id: 'gnn', label: 'GRAPHSAGE', ok: !anomaly, active: anomaly, color: anomaly ? '#9d4edd' : '#2d313b', icon: anomaly ? '◎' : '—' },
        { id: 'rca', label: 'ROOT CAUSE', ok: !rootCause, active: !!rootCause, color: rootCause ? '#9d4edd' : '#2d313b', icon: rootCause ? '✓' : '—' },
    ];

    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {stages.map((s, i) => (
                <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{
                        display: 'flex', alignItems: 'center', gap: 5,
                        padding: '4px 10px',
                        background: s.active ? `${s.color}12` : '#0f1115',
                        border: `1px solid ${s.active ? s.color + '50' : '#1e2230'}`,
                        transition: 'all 0.4s ease',
                        opacity: s.active ? 1 : 0.45,
                    }}>
                        <span style={{ fontSize: 9, color: s.color, fontFamily: 'monospace', fontWeight: 700 }}>{s.icon}</span>
                        <div>
                            <div style={{ fontSize: 8, fontFamily: 'monospace', letterSpacing: 1, color: s.active ? '#e2e4e9' : '#4a5568', fontWeight: 700 }}>{s.label}</div>
                            {s.id === 'm1' && <div style={{ fontSize: 7, color: s.color, fontFamily: 'monospace' }}>
                                {latest?.anomaly?.score?.toFixed(2) ?? '—'} / {latest?.anomaly?.threshold?.toFixed(2) ?? '—'}
                            </div>}
                            {s.id === 'rca' && rootCause && <div style={{ fontSize: 7, color: '#9d4edd', fontFamily: 'monospace', maxWidth: 80, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{rootCause}</div>}
                        </div>
                    </div>
                    {i < stages.length - 1 && (
                        <div style={{ fontSize: 10, color: stages[i + 1].active ? stages[i + 1].color : '#2d313b', fontFamily: 'monospace', transition: 'color 0.4s' }}>→</div>
                    )}
                </div>
            ))}
        </div>
    );
}

// ─── Right panel: intelligent context-aware ───────────────────────────────────

function InspectorPanel({ nodes, status, latest, selectedNode, anomaly, rootCause }: {
    nodes: TopologyNode[]; status: MLStatus | null; latest: MLLatest | null;
    selectedNode: TopologyNode | null; anomaly: boolean; rootCause?: string;
}) {
    const healthyCount = nodes.filter(n => ['HEALTHY', 'READY', 'NORMAL'].includes(n.status?.toUpperCase() ?? '')).length;
    const sys = sysLabel(nodes, anomaly);
    const score = latest?.anomaly?.score;
    const threshold = latest?.anomaly?.threshold;

    if (selectedNode) {
        const color = nodeColor(selectedNode.status, rootCause === selectedNode.name || rootCause === selectedNode.id);
        return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, height: '100%', overflowY: 'auto' }}>
                <div style={{ padding: '10px 12px', border: `1px solid ${color}45`, background: `${color}08` }}>
                    <div style={{ fontSize: 8, fontFamily: 'monospace', color: '#8b92a5', letterSpacing: 2, marginBottom: 8, display: 'flex', justifyContent: 'space-between' }}>
                        SELECTED SERVICE
                        <button onClick={() => { }} style={{ background: 'none', border: 'none', color: '#4a5568', cursor: 'pointer', fontSize: 10, padding: 0 }}>✕</button>
                    </div>
                    <div style={{ fontSize: 15, fontWeight: 800, fontFamily: 'monospace', color, letterSpacing: 1, marginBottom: 4 }}>
                        {selectedNode.name.toUpperCase().replace(/-SERVICE$/, '').replace(/-/g, ' ')}
                    </div>
                    <span style={{ fontSize: 7, padding: '2px 8px', border: `1px solid ${color}50`, color, background: `${color}15`, fontFamily: 'monospace', letterSpacing: 2 }}>
                        {selectedNode.status?.toUpperCase() ?? 'UNKNOWN'}
                    </span>
                    <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {[
                            ['Type', selectedNode.type],
                            ['Namespace', selectedNode.namespace],
                            ['Resource', selectedNode.id],
                            ['CPU', 'N/A'], ['Memory', 'N/A'],
                            ['Model 1 Score', score?.toFixed(4) ?? 'N/A'],
                        ].map(([k, v]) => (
                            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 5, borderBottom: '1px solid #151820' }}>
                                <span style={{ fontSize: 9, color: '#8b92a5', fontFamily: 'monospace' }}>{k}</span>
                                <span style={{ fontSize: 9, fontFamily: 'monospace', fontWeight: 600, color: '#e2e4e9' }}>{v}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {anomaly && rootCause && (
                    <div style={{ padding: '10px 12px', border: '1px solid #9d4edd45', background: '#9d4edd08' }}>
                        <div style={{ fontSize: 8, fontFamily: 'monospace', color: '#9d4edd', letterSpacing: 2, marginBottom: 8 }}>CAUSAL RCA</div>
                        {[
                            ['Root Cause', rootCause],
                            ['Confidence', latest?.root_cause?.score?.toFixed(4) ?? 'N/A'],
                            ['Status', latest?.root_cause?.status?.replace(/_/g, ' ').toUpperCase() ?? '—'],
                        ].map(([k, v]) => (
                            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                                <span style={{ fontSize: 9, color: '#8b92a5', fontFamily: 'monospace' }}>{k}</span>
                                <span style={{ fontSize: 9, fontFamily: 'monospace', fontWeight: 700, color: k === 'Root Cause' ? '#9d4edd' : '#e2e4e9' }}>{v}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    }

    // Default system summary
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, height: '100%' }}>
            {/* System health hero */}
            <div style={{
                padding: '14px 12px', border: `1px solid ${anomaly ? '#ff4b4b45' : '#37d67a30'}`,
                background: anomaly ? '#ff4b4b06' : '#37d67a06',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    {anomaly
                        ? <AlertOctagon size={20} color="#ff4b4b" />
                        : <CheckCircle size={20} color="#37d67a" />}
                    <div>
                        <div style={{ fontSize: 14, fontWeight: 800, fontFamily: 'monospace', color: anomaly ? '#ff4b4b' : '#37d67a', letterSpacing: 2 }}>
                            {anomaly ? 'ANOMALY' : sys}
                        </div>
                        <div style={{ fontSize: 9, color: '#8b92a5', fontFamily: 'monospace' }}>
                            {healthyCount}/{nodes.length} services operational
                        </div>
                    </div>
                </div>
                {anomaly && (
                    <div style={{ background: '#ff4b4b10', border: '1px solid #ff4b4b30', padding: '8px 10px', marginTop: 4 }}>
                        <div style={{ fontSize: 9, color: '#ff4b4b', fontFamily: 'monospace', fontWeight: 700, marginBottom: 4 }}>ACTIVE INCIDENT</div>
                        {rootCause && <div style={{ fontSize: 11, fontFamily: 'monospace', fontWeight: 700, color: '#e2e4e9' }}>Root Cause: {rootCause}</div>}
                        <div style={{ fontSize: 9, color: '#8b92a5', fontFamily: 'monospace', marginTop: 4 }}>
                            Score: <span style={{ color: '#ff4b4b' }}>{score?.toFixed(4)}</span> &gt; {threshold?.toFixed(4)}
                        </div>
                    </div>
                )}
            </div>

            {/* Key metrics */}
            <div style={{ padding: '10px 12px', border: '1px solid #1e2230', display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                    { label: 'MODEL 1', value: score?.toFixed(4) ?? '—', sub: `Threshold: ${threshold?.toFixed(4) ?? '—'}`, color: anomaly ? '#ff4b4b' : '#37d67a' },
                    { label: 'RCA STATUS', value: rootCause ?? 'NOT TRIGGERED', sub: rootCause ? `Conf: ${latest?.root_cause?.score?.toFixed(4) ?? '—'}` : 'GraphSAGE on standby', color: rootCause ? '#9d4edd' : '#8b92a5' },
                    { label: 'PIPELINE', value: status?.pipeline?.toUpperCase() ?? '—', sub: status?.telemetry?.toUpperCase() ?? '—', color: statusColor(status?.pipeline) },
                ].map(m => (
                    <div key={m.label} style={{ borderBottom: '1px solid #151820', paddingBottom: 8 }}>
                        <div style={{ fontSize: 7, fontFamily: 'monospace', color: '#8b92a5', letterSpacing: 2, marginBottom: 3 }}>{m.label}</div>
                        <div style={{ fontSize: 12, fontWeight: 700, fontFamily: 'monospace', color: m.color }}>{m.value}</div>
                        <div style={{ fontSize: 7, color: '#4a5568', marginTop: 1 }}>{m.sub}</div>
                    </div>
                ))}
            </div>

            {/* Affected services when anomaly */}
            {anomaly && nodes.some(n => !['HEALTHY', 'READY'].includes(n.status?.toUpperCase() ?? '')) && (
                <div style={{ padding: '10px 12px', border: '1px solid rgba(255,75,75,0.25)', background: '#ff4b4b05', flex: 1 }}>
                    <div style={{ fontSize: 8, fontFamily: 'monospace', color: '#ff4b4b', letterSpacing: 2, marginBottom: 8, fontWeight: 700 }}>AFFECTED SERVICES</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, paddingLeft: 8, borderLeft: '2px solid rgba(255,75,75,0.25)' }}>
                        {nodes.filter(n => !['HEALTHY', 'READY'].includes(n.status?.toUpperCase() ?? '')).map((n, i, arr) => (
                            <div key={n.id}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontSize: 9, fontFamily: 'monospace', fontWeight: 700, color: nodeColor(n.status, rootCause === n.name || rootCause === n.id) }}>
                                        {n.name.toUpperCase().replace(/-/g, ' ')}
                                    </span>
                                    <span style={{ fontSize: 7, fontFamily: 'monospace', color: nodeColor(n.status), border: `1px solid ${nodeColor(n.status)}40`, padding: '1px 5px' }}>
                                        {n.status?.toUpperCase()}
                                    </span>
                                </div>
                                {i < arr.length - 1 && <div style={{ fontSize: 8, color: '#ff4b4b30', paddingLeft: 4, marginTop: 2 }}>↓</div>}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {!anomaly && (
                <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 6, color: '#2d313b' }}>
                    <CheckCircle size={28} style={{ opacity: 0.35 }} />
                    <div style={{ fontSize: 8, fontFamily: 'monospace', letterSpacing: 2, color: '#37d67a60' }}>NO ACTIVE INCIDENTS</div>
                    <div style={{ fontSize: 7, color: '#2d313b', textAlign: 'center' }}>Click a node to inspect it</div>
                </div>
            )}
        </div>
    );
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Overview() {
    const [status, setStatus] = useState<MLStatus | null>(null);
    const [latest, setLatest] = useState<MLLatest | null>(null);
    const [topology, setTopology] = useState<TopologyData | null>(null);
    const [topoErr, setTopoErr] = useState(false);
    const [scoreHist, setScoreHist] = useState<number[]>([]);
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [hoveredNode, setHoveredNode] = useState<TopologyNode | null>(null);
    const [lastUpdated, setLastUpdated] = useState('—');
    const [camReset, setCamReset] = useState(0);

    useEffect(() => {
        const poll = async () => {
            try {
                const [st, lt] = await Promise.allSettled([fetchStatus(), fetchLatest()]);
                if (st.status === 'fulfilled') setStatus(st.value);
                if (lt.status === 'fulfilled') {
                    setLatest(lt.value);
                    if (lt.value.anomaly?.score != null) setScoreHist(h => [...h.slice(-49), lt.value.anomaly!.score]);
                }
            } catch { /* silent */ }
            try {
                setTopology(await fetchTopology()); setTopoErr(false);
            } catch { setTopoErr(true); }
            setLastUpdated(new Date().toLocaleTimeString('en-GB'));
        };
        poll();
        const id = setInterval(poll, 3000);
        return () => clearInterval(id);
    }, []);

    const nodes = topology?.nodes ?? [];
    const edges = topology?.edges ?? [];
    const anomaly = !!latest?.anomaly?.detected;
    const rootCause = latest?.root_cause?.service;
    const score = latest?.anomaly?.score;
    const threshold = latest?.anomaly?.threshold;
    const healthyN = nodes.filter(n => ['HEALTHY', 'READY', 'NORMAL'].includes(n.status?.toUpperCase() ?? '')).length;
    const sys = sysLabel(nodes, anomaly);

    const nodesP = useMemo(() => {
        const R = 7;
        return nodes.map((n, i) => {
            const a = (i / Math.max(nodes.length, 1)) * Math.PI * 2;
            return { ...n, pos: [Math.cos(a) * R, Math.sin(a * 1.7) * 2.5, Math.sin(a) * R] as [number, number, number] };
        });
    }, [nodes]);

    const selectedNode = nodes.find(n => n.id === selectedId) ?? null;
    const onSelect = useCallback((id: string) => setSelectedId(prev => prev === id ? null : id), []);
    const onNodeEnter = useCallback((n: TopologyNode) => setHoveredNode(n), []);
    const onNodeLeave = useCallback(() => setHoveredNode(null), []);

    const sysCol = statusColor(anomaly ? 'ANOMALY' : sys);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 0, overflow: 'hidden', background: '#09090c' }}>

            {/* ── Compact status ribbon ── */}
            <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '5px 14px', background: '#0c0d10',
                borderBottom: `1px solid ${anomaly ? 'rgba(255,75,75,0.3)' : '#1a1d25'}`,
                flexShrink: 0,
            }}>
                <div style={{ display: 'flex', gap: 18, alignItems: 'center' }}>
                    <div style={{ display: 'flex', gap: 0 }}>
                        {[
                            ['SYSTEM', sys],
                            ['KAFKA', status?.telemetry ?? '…'],
                            ['MODEL 1', status?.model1 ?? '…'],
                            ['MODEL 2', status?.model2?.split('(')[0].trim() ?? '…'],
                            ['PIPELINE', status?.pipeline ?? '…'],
                        ].map(([k, v], i, arr) => (
                            <div key={k} style={{
                                padding: '3px 14px', borderRight: i < arr.length - 1 ? '1px solid #1a1d25' : 'none',
                                display: 'flex', gap: 6, alignItems: 'center'
                            }}>
                                <span style={{ fontSize: 8, fontFamily: 'monospace', color: '#8b92a5', letterSpacing: 1 }}>{k}</span>
                                <span style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, color: statusColor(v) }}>{v?.toUpperCase()}</span>
                                <span style={{ width: 5, height: 5, borderRadius: '50%', background: statusColor(v), display: 'inline-block' }} />
                            </div>
                        ))}
                    </div>
                </div>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                    {anomaly && (
                        <div style={{ fontSize: 8, fontFamily: 'monospace', color: '#ff4b4b', display: 'flex', alignItems: 'center', gap: 5, padding: '2px 10px', border: '1px solid rgba(255,75,75,0.35)', background: 'rgba(255,75,75,0.06)' }}>
                            <AlertOctagon size={9} /> ANOMALY ACTIVE
                        </div>
                    )}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Radio size={8} color="#37d67a" />
                        <span style={{ fontSize: 7, fontFamily: 'monospace', color: '#37d67a', letterSpacing: 2 }}>LIVE</span>
                    </div>
                    <span style={{ fontSize: 8, fontFamily: 'monospace', color: '#4a5568' }}>{lastUpdated}</span>
                    <button onClick={() => setCamReset(c => c + 1)} style={{ background: 'none', border: '1px solid #1a1d25', color: '#4a5568', padding: '2px 8px', cursor: 'pointer', fontSize: 7, fontFamily: 'monospace', display: 'flex', alignItems: 'center', gap: 3 }}>
                        <RefreshCw size={7} /> RESET
                    </button>
                </div>
            </div>

            {/* ── Main area ── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 270px', flex: 1, minHeight: 0, gap: 0 }}>

                {/* 3D Topology — HERO */}
                <div style={{
                    position: 'relative', background: '#06070a',
                    borderRight: '1px solid #1a1d25',
                    borderBottom: '1px solid #1a1d25',
                    overflow: 'hidden',
                }}>
                    {/* Canvas header */}
                    <div style={{
                        position: 'absolute', top: 0, left: 0, right: 0, zIndex: 10,
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        padding: '6px 12px', background: 'rgba(6,7,10,0.82)',
                        borderBottom: '1px solid #1a1d25',
                    }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <span style={{ fontSize: 9, fontFamily: 'monospace', fontWeight: 700, letterSpacing: 2, color: '#e2e4e9' }}>DISTRIBUTED SERVICE TOPOLOGY</span>
                            <span style={{ fontSize: 7, padding: '1px 7px', border: '1px solid #1a1d25', color: '#8b92a5', fontFamily: 'monospace' }}>{nodes.length} NODES · {edges.length} EDGES</span>
                        </div>
                        <div style={{ fontSize: 7, color: '#4a5568', fontFamily: 'monospace', display: 'flex', gap: 12 }}>
                            <span>Drag: Rotate</span><span>Scroll: Zoom</span><span>Click: Inspect</span>
                        </div>
                    </div>

                    {/* Hover tooltip */}
                    {hoveredNode && (
                        <div style={{
                            position: 'absolute', top: 44, left: 12, zIndex: 20,
                            background: 'rgba(6,7,10,0.95)', border: `1px solid ${nodeColor(hoveredNode.status)}45`,
                            padding: '8px 12px', minWidth: 150, pointerEvents: 'none',
                        }}>
                            <div style={{ fontSize: 10, fontWeight: 700, fontFamily: 'monospace', color: nodeColor(hoveredNode.status), marginBottom: 5, letterSpacing: 1 }}>
                                {hoveredNode.name.toUpperCase().replace(/-SERVICE$/, '')}
                            </div>
                            <div style={{ fontSize: 8, color: '#8b92a5', fontFamily: 'monospace' }}><span style={{ color: '#4a5568' }}>STATUS  </span>{hoveredNode.status?.toUpperCase() ?? '—'}</div>
                            <div style={{ fontSize: 8, color: '#8b92a5', fontFamily: 'monospace' }}><span style={{ color: '#4a5568' }}>TYPE    </span>{hoveredNode.type}</div>
                            <div style={{ fontSize: 8, color: '#8b92a5', fontFamily: 'monospace' }}><span style={{ color: '#4a5568' }}>NS      </span>{hoveredNode.namespace}</div>
                        </div>
                    )}

                    {/* Legend */}
                    <div style={{
                        position: 'absolute', bottom: 10, left: 10, zIndex: 10,
                        background: 'rgba(6,7,10,0.85)', border: '1px solid #1a1d25',
                        padding: '6px 9px', display: 'flex', flexDirection: 'column', gap: 4,
                    }}>
                        {[['#37d67a', 'Healthy'], ['#f4b141', 'Degraded'], ['#ff4b4b', 'Failed / Root Cause'], ['#9d4edd', 'Causal RCA Path']].map(([c, l]) => (
                            <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 7, fontFamily: 'monospace', color: '#8b92a5' }}>
                                <span style={{ width: 5, height: 5, borderRadius: '50%', background: c, display: 'inline-block', boxShadow: `0 0 4px ${c}` }} />
                                {l}
                            </div>
                        ))}
                    </div>

                    {/* Canvas */}
                    {topoErr ? (
                        <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 8, color: '#4a5568' }}>
                            <AlertOctagon size={28} style={{ opacity: 0.35 }} />
                            <span style={{ fontSize: 9, fontFamily: 'monospace', letterSpacing: 2 }}>TOPOLOGY API UNAVAILABLE</span>
                        </div>
                    ) : nodes.length === 0 ? (
                        <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 8, color: '#4a5568' }}>
                            <Activity size={24} style={{ opacity: 0.25 }} className="animate-spin" />
                            <span style={{ fontSize: 9, fontFamily: 'monospace', letterSpacing: 2 }}>LOADING TOPOLOGY…</span>
                        </div>
                    ) : (
                        <Canvas camera={{ position: [0, 8, 20], fov: 52 }} style={{ width: '100%', height: '100%' }}
                            onPointerMissed={() => setSelectedId(null)}>
                            <TopologyScene
                                nodesP={nodesP} edges={edges}
                                selectedId={selectedId} rootCause={rootCause} anomaly={anomaly}
                                onSelect={onSelect} onNodeEnter={onNodeEnter} onNodeLeave={onNodeLeave}
                                camReset={camReset}
                            />
                        </Canvas>
                    )}
                </div>

                {/* Right inspector */}
                <div style={{ padding: '12px 12px', overflowY: 'auto', borderBottom: '1px solid #1a1d25' }}>
                    <InspectorPanel nodes={nodes} status={status} latest={latest} selectedNode={selectedNode} anomaly={anomaly} rootCause={rootCause} />
                </div>
            </div>

            {/* ── RCA Pipeline bar ── */}
            <div style={{
                padding: '7px 14px', background: '#0c0d10',
                borderTop: '1px solid #1a1d25', borderBottom: '1px solid #1a1d25',
                flexShrink: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <GitBranch size={10} color="#9d4edd" />
                    <span style={{ fontSize: 8, fontFamily: 'monospace', letterSpacing: 2, color: '#8b92a5', fontWeight: 700 }}>CAUSAL REASONING PIPELINE</span>
                </div>
                <PipelineBar status={status} latest={latest} anomaly={anomaly} rootCause={rootCause} />
            </div>

            {/* ── Bottom 3 cards ── */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 0, flexShrink: 0 }}>

                {/* Model 1 */}
                <div style={{ padding: '8px 14px', background: '#0c0d10', borderRight: '1px solid #1a1d25', borderTop: anomaly ? '2px solid #ff4b4b' : '2px solid #37d67a' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                            <span style={{ fontSize: 8, fontFamily: 'monospace', letterSpacing: 2, color: '#8b92a5', fontWeight: 700 }}>MODEL 1</span>
                            <span style={{ fontSize: 7, padding: '1px 6px', border: '1px solid #1a1d25', color: '#8b92a5', fontFamily: 'monospace' }}>LSTM-VAE</span>
                        </div>
                        <span style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, color: anomaly ? '#ff4b4b' : '#37d67a', letterSpacing: 2 }}>{anomaly ? 'ANOMALY' : 'NORMAL'}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                        <div>
                            <div style={{ fontSize: 22, fontWeight: 800, fontFamily: 'monospace', color: anomaly ? '#ff4b4b' : '#e2e4e9', lineHeight: 1 }}>{score?.toFixed(4) ?? '—'}</div>
                            <div style={{ fontSize: 8, color: '#4a5568', marginTop: 2 }}>Threshold {threshold?.toFixed(4) ?? '—'}</div>
                        </div>
                        <Spark data={scoreHist} w={90} h={28} color={anomaly ? '#ff4b4b' : '#00d2ff'} />
                    </div>
                </div>

                {/* Kafka */}
                <div style={{ padding: '8px 14px', background: '#0c0d10', borderRight: '1px solid #1a1d25', borderTop: '2px solid #00d2ff' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 6 }}>
                        <Activity size={10} color="#00d2ff" />
                        <span style={{ fontSize: 8, fontFamily: 'monospace', letterSpacing: 2, color: '#8b92a5', fontWeight: 700 }}>KAFKA / TELEMETRY</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                        {[
                            ['Telemetry', status?.telemetry?.toUpperCase() ?? '—'],
                            ['Pipeline', status?.pipeline?.toUpperCase() ?? '—'],
                            ['Topics', 'raw.metrics, raw.logs, raw.events'],
                        ].map(([k, v]) => (
                            <div key={k} style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span style={{ fontSize: 8, color: '#4a5568', fontFamily: 'monospace' }}>{k}</span>
                                <span style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, color: k !== 'Topics' ? statusColor(v as string) : '#8b92a5', maxWidth: 160, textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{v as string}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Cluster */}
                <div style={{ padding: '8px 14px', background: '#0c0d10', borderTop: `2px solid ${nodes.filter(n => ['FAILED', 'CRITICAL'].includes(n.status?.toUpperCase() ?? '')).length > 0 ? '#ff4b4b' : '#37d67a'}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                        <span style={{ fontSize: 8, fontFamily: 'monospace', letterSpacing: 2, color: '#8b92a5', fontWeight: 700 }}>CLUSTER</span>
                        <span style={{ fontSize: 8, fontFamily: 'monospace', fontWeight: 700, color: sysCol }}>{sys}</span>
                    </div>
                    <div style={{ display: 'flex', gap: 14 }}>
                        {[
                            { label: 'TOTAL', value: nodes.length, color: '#e2e4e9' },
                            { label: 'HEALTHY', value: healthyN, color: '#37d67a' },
                            { label: 'WARN', value: nodes.filter(n => ['DEGRADED', 'BLOCKED', 'WARNING'].includes(n.status?.toUpperCase() ?? '')).length, color: '#f4b141' },
                            { label: 'FAILED', value: nodes.filter(n => ['FAILED', 'CRITICAL'].includes(n.status?.toUpperCase() ?? '')).length, color: '#ff4b4b' },
                        ].map(s => (
                            <div key={s.label} style={{ textAlign: 'center' }}>
                                <div style={{ fontSize: 18, fontWeight: 800, fontFamily: 'monospace', color: s.color, lineHeight: 1 }}>{s.value}</div>
                                <div style={{ fontSize: 7, color: '#4a5568', fontFamily: 'monospace', letterSpacing: 1 }}>{s.label}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
