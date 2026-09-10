export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface MLStatus {
    model1: string;
    model2: string;
    telemetry: string;
    pipeline: string;
}

export interface AnomalyData {
    detected: boolean;
    score: number;
    threshold: number;
}

export interface RootCauseData {
    status: string;
    service?: string;
    node_index?: number;
    score?: number;
    reason?: string;
    missing_requirements?: string[];
}

export interface MLLatest {
    status: string;
    timestamp?: string;
    source?: string;
    anomaly?: AnomalyData;
    root_cause?: RootCauseData;
    reason?: string;
    received_samples?: number;
    required_samples?: number;
}

export interface TopologyNode {
    id: string;
    name: string;
    type: string;
    namespace: string;
    status?: string | null;
}

export interface TopologyEdge {
    source: string;
    target: string;
    type: string;
}

export interface TopologyData {
    timestamp: string;
    nodes: TopologyNode[];
    edges: TopologyEdge[];
}

export async function fetchStatus(): Promise<MLStatus> {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/status`);
    if (!res.ok) throw new Error('API error');
    return res.json();
}

export async function fetchLatest(): Promise<MLLatest> {
    const res = await fetch(`${API_BASE_URL}/api/v1/ml/latest`);
    if (!res.ok) throw new Error('API error');
    return res.json();
}

export async function fetchTopology(): Promise<TopologyData> {
    const res = await fetch(`${API_BASE_URL}/api/v1/topology`);
    if (!res.ok) throw new Error('API error');
    return res.json();
}
