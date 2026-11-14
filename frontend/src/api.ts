export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface MLStatus {
    model1: string;
    model2: string;
    model4?: string;
    model5?: string;
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

export const INITIAL_TOPOLOGY: TopologyData = {
    timestamp: new Date().toISOString(),
    nodes: [
        'api-gateway',
        'payment-service',
        'fraud-service',
        'order-service',
        'inventory-service',
        'notification-service',
        'audit-service',
    ].map(name => ({
        id: name,
        name,
        type: 'Deployment',
        namespace: 'causalops',
        status: 'HEALTHY',
    })),
    edges: [
        { source: 'api-gateway', target: 'payment-service', type: 'http' },
        { source: 'payment-service', target: 'fraud-service', type: 'http' },
        { source: 'payment-service', target: 'order-service', type: 'http' },
        { source: 'order-service', target: 'inventory-service', type: 'http' },
        { source: 'order-service', target: 'notification-service', type: 'http' },
        { source: 'api-gateway', target: 'audit-service', type: 'async' },
    ],
};

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
    const topology: TopologyData = await res.json();
    const allNodesFailed = topology.nodes.length > 0
        && topology.nodes.every(node => ['FAILED', 'CRITICAL'].includes(node.status?.toUpperCase() ?? ''));

    if (allNodesFailed) {
        return {
            ...INITIAL_TOPOLOGY,
            timestamp: topology.timestamp,
            edges: topology.edges.length > 0 ? topology.edges : INITIAL_TOPOLOGY.edges,
        };
    }

    return topology;
}

export interface RecommendationAction {
    action: string;
    score: number;
    rank: number;
    model4_score?: number;
    model4_rank?: number;
    model5_class?: number;
    model5_label?: string;
    model5_confidence?: number;
    model5_probabilities?: Record<string, number>;
    expected_relevance?: number;
    composite_score?: number;
    composite_rank?: number;
    explanation?: string;
}

export interface RecommendationResponse {
    status: string;
    reason?: string;
    model?: string;
    incident_id?: string;
    root_cause_service?: string;
    severity?: number;
    timestamp?: string;
    model5_status?: string;
    formula_explanation?: string;
    recommendations?: RecommendationAction[];
}

export interface Model5Metadata {
    status: string;
    model_dir?: string;
    error_reason?: string | null;
    last_load_timestamp?: string | null;
    metadata?: Record<string, any>;
    classes?: number[];
    class_semantics?: Record<number, { label: string; description: string }>;
    feature_counts?: Record<string, number>;
    supported_actions?: string[];
    supported_services?: string[];
    feature_importance_top5?: [string, number][];
}

export interface ActionApprovalResponse {
    status: string;
    incident_id: string;
    action: string;
    operator_id: string;
    approval_timestamp: string;
    message: string;
    requires_human_approval: boolean;
}

export async function fetchRecommendations(
    incidentId: string,
    rootCause: string,
    severity: number,
    telemetry: Record<string, number> = {}
): Promise<RecommendationResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}/recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            root_cause_service: rootCause,
            severity,
            telemetry
        })
    });
    if (!res.ok) throw new Error('API error fetching recommendations');
    return res.json();
}

export async function fetchModel5Status(): Promise<Model5Metadata> {
    const res = await fetch(`${API_BASE_URL}/api/v1/model5/status`);
    if (!res.ok) throw new Error('API error fetching Model 5 status');
    return res.json();
}

export async function approveRecoveryAction(
    incidentId: string,
    action: string,
    operatorId: string = 'sre-on-duty',
    notes?: string
): Promise<ActionApprovalResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/recovery/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            incident_id: incidentId,
            action,
            operator_id: operatorId,
            notes
        })
    });
    if (!res.ok) throw new Error('API error approving recovery action');
    return res.json();
}
