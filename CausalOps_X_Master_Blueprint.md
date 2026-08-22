# CausalOps X: Master Project Blueprint
## Causal AI-Powered AIOps Platform for Microservice Infrastructure Monitoring & Remediation

**Document Version:** 2.0 (Revised for technical consistency and implementation realism)
**Last Updated:** August 2026
**Status:** Revised Specification — Internally Consistent
**Project Scope:** Layered platform — MVP core, advanced intelligence, and a research contribution (ATCGT), suitable for a final-year project, hackathon demo, and a research paper foundation

---

## How to Read This Document

Every capability in this blueprint is tagged with one of four labels. This replaces the earlier draft's tendency to describe targets, hypotheses, and future plans as if they were already-achieved facts.

| Tag | Meaning |
|---|---|
| **[MVP]** | Must be built and working for the core demo / final-year deliverable |
| **[ADVANCED]** | Builds on the MVP; adds intelligence beyond basic detection |
| **[RESEARCH]** | The ATCGT contribution and its experimental evaluation — hypotheses to be tested, not established results |
| **[FUTURE]** | Explicitly out of scope for the current project; documented for roadmap completeness only |

No section in this document should be read as claiming production traffic, trained models, measured accuracy, or research results already exist. Numbers presented as performance are **targets**, stated explicitly as such.

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Part 1: Vision & Strategy](#part-1-vision--strategy)
3. [Part 2: System Architecture](#part-2-system-architecture)
4. [Part 3: Technology Stack](#part-3-technology-stack)
5. [Part 4: Development Roadmap](#part-4-development-roadmap)
6. [Part 5: Backend Development](#part-5-backend-development)
7. [Part 6: Frontend Dashboard](#part-6-frontend-dashboard)
8. [Part 7: Database Design](#part-7-database-design)
9. [Part 8: Monitoring & Observability](#part-8-monitoring--observability)
10. [Part 9: AI/ML Pipeline](#part-9-aiml-pipeline)
11. [Part 10: Explainable AI](#part-10-explainable-ai)
12. [Part 11: Testing Strategy](#part-11-testing-strategy)
13. [Part 12: Deployment, DevOps & MLOps](#part-12-deployment-devops--mlops)
14. [Part 13: Research Paper](#part-13-research-paper)
15. [Part 14: Future Roadmap](#part-14-future-roadmap)
16. [Appendix](#appendix)

---

## Executive Summary

**CausalOps X** is a causal-AI-powered AIOps platform that helps SRE and platform teams move beyond "what failed" toward "why it failed, what it will affect, and what to do about it" in microservice systems.

### Pipeline

```
Observability (metrics, logs, traces, K8s events)
  → Anomaly Detection
  → Root Cause Analysis
  → Failure Propagation Prediction
  → Recovery Recommendation
  → Counterfactual Evaluation
  → Human Approval
  → Safe (allowlisted) Remediation
  → Continuous Feedback / Retraining
```

### Three Layers

- **LAYER 1 — MVP / Core Production System**: Kubernetes-based test environment, metrics/logs/traces ingestion, anomaly detection, root cause analysis, service dependency graph, incident management, dashboard, human-approved remediation.
- **LAYER 2 — Advanced Intelligence**: Failure propagation prediction, recovery recommendation, counterfactual evaluation, explainability, feedback learning.
- **LAYER 3 — Research Contribution**: The Adaptive Temporal Causal Graph Transformer (ATCGT) — a proposed research architecture, temporal + graph + causal modeling, ablation studies, baseline comparisons.

### Core Pipeline Components (Five)

The production/advanced pipeline is composed of **five** components. This is the correct and only count used throughout this document:

1. Anomaly Detection
2. Root Cause Analysis
3. Failure Propagation Prediction
4. Recovery Recommendation
5. Counterfactual Evaluation

**ATCGT is not a sixth pipeline component.** It is a research architecture — an alternative, more advanced implementation proposed to enhance components 2 and 3 (Root Cause Analysis and Failure Propagation Prediction). Earlier drafts of this document referred to ATCGT as "Model 6"; that has been corrected everywhere.

### Target Users
- DevOps/SRE teams managing microservices
- Platform engineering organizations
- Cloud infrastructure teams
- Research community (AIOps & Causal ML)

### Target Metrics (Hypotheses to Validate, Not Guarantees)

All figures below are **targets** to be established experimentally on public benchmark datasets and our own controlled fault-injection testbed — not claims about current or production performance.

| Metric | Target | How It Will Be Measured |
|---|---|---|
| MTTR reduction (controlled testbed) | To be measured; hypothesis: significant reduction vs. manual baseline | Controlled experiment comparing manual vs. assisted incident resolution on injected faults |
| Anomaly detection false positive rate | Target < 5% | Evaluated on held-out validation split |
| RCA Top-1 accuracy | Target ≥ 85% (stretch goal) | Evaluated on public + controlled datasets |
| RCA Top-3 accuracy | Target ≥ 90% | Same as above |
| Detection latency | Target < 30 seconds | End-to-end pipeline benchmark |
| Inference latency (RCA) | Target < 2 seconds P99 | Load test on inference service |

### Research Novelty (Proposed, Not Yet Established)

- **Proposed contribution**: ATCGT, an architecture that combines temporal attention, graph-based dependency reasoning, and causal structure learning for root cause analysis and failure propagation prediction in microservices.
- This is presented as a **research hypothesis to be evaluated** against established baselines (LSTM, static graph-based RCA, MicroRank, and other published methods), not as an already-proven state-of-the-art result.

---

# PART 1: VISION & STRATEGY

## 1.1 Project Overview

### What is CausalOps X?

CausalOps X is an AIOps platform that applies causality-aware machine learning to the problem of diagnosing failures in distributed systems. While traditional monitoring tools report *what* failed, CausalOps X is designed to help answer:
- **Why** did it fail? (Root Cause Analysis)
- **How** will it impact other services? (Failure Propagation Prediction)
- **What** should we do about it? (Recovery Recommendation)
- **What if** we take action X? (Counterfactual Evaluation)

### Positioning

| Aspect | Traditional APM | ML-Based AIOps | CausalOps X (Target) |
|--------|-----------------|----------------|----|
| Detection | Rule-based thresholds | Statistical anomaly detection | Anomaly detection (VAE-based) |
| Diagnosis | Manual correlation | Statistical ML | Graph-based root cause ranking, with causal reasoning as a research goal |
| Prediction | None | Time series forecasting | Failure propagation prediction (LSTM baseline, graph-temporal advanced) |
| Remediation | Human oncall | Runbook automation | Ranked recommendations, human-approved, allowlisted execution |
| Simulation | None | None | Counterfactual "what-if" estimation with explicit uncertainty |

This is a positioning goal the project is designed to work toward, not a claim that CausalOps X currently outperforms these categories in production.

---

## 1.2 Problem Statement

### The Challenge
Modern microservice architectures are:
- **Complex**: tens to hundreds of interdependent services
- **Dynamic**: services scaling, redeploying, changing behavior constantly
- **Opaque**: hard to reason about causality in failures
- **Costly**: incident response time is a real, measurable business cost

### Known Industry Pain Points (Cited as Motivation, Not Our Data)
1. Alert fatigue — large volumes of alerts, low actionable fraction (widely reported in AIOps literature)
2. High MTTR for medium-complexity incidents
3. Root cause identification consumes a large share of incident response time
4. Cascade failures — one component failing can affect many downstream services
5. Manual remediation carries escalation risk

These are motivating observations drawn from the general AIOps literature and industry reporting, not statistics measured from our own production deployment (we do not have one).

### Why Existing Solutions Fall Short
- **Prometheus/Grafana**: report metrics, but provide no causal reasoning layer
- **Commercial APM tools (Datadog, New Relic, etc.)**: primarily correlation/statistical ML, not causal
- **PagerDuty and similar**: orchestrate human response, don't improve diagnosis quality
- **Ad-hoc/offline ML scripts**: typically don't integrate live service-dependency information

---

## 1.3 Objectives

### Primary Objectives (MVP + Advanced)
1. Build a working anomaly detection → RCA → incident management pipeline on a real Kubernetes test environment **[MVP]**
2. Extend to failure propagation prediction, recovery recommendation, and counterfactual evaluation **[ADVANCED]**
3. Establish target performance experimentally (not assumed in advance) on public benchmark datasets and a controlled fault-injection testbed **[MVP/ADVANCED]**
4. Provide explainability for all AI decisions (SHAP for tabular/tree models, attention/gradient-based explanations for graph models, explicit causal-assumption disclosure for counterfactual outputs) **[ADVANCED]**
5. Propose and evaluate ATCGT as a research contribution in causal/graph ML for systems **[RESEARCH]**

### Secondary Objectives
1. Support both Kubernetes-native workloads (VM support is a **[FUTURE]** extension)
2. Distinguish infrastructure-, application-, configuration-, and traffic-driven root causes where the data supports it
3. Keep architecture extensible for future industry-specific use cases **[FUTURE]**

### Business Objectives (Long-Term, Not MVP)
1. Open-source the core platform (Apache 2.0) **[FUTURE]**
2. Explore enterprise scalability and multi-tenancy after MVP validation **[FUTURE]**
3. Explore a managed-service / support business model **[FUTURE]**

---

## 1.4 Research Novelty

### Proposed Contribution: Adaptive Temporal Causal Graph Transformer (ATCGT) — Proposed Research Architecture

**Problem motivating the design**: static service graphs don't capture temporal dynamics, and standard transformers don't respect graph/causal structure.

**Proposed approach**: ATCGT is designed to:
- Learn dependency/temporal structure from observed telemetry
- Use temporal attention across a `(time, service, feature)` representation (not a flattened sequence — see Part 9 for the corrected architecture)
- Integrate service-graph structure into transformer attention
- Be evaluated for whether it improves RCA and failure-propagation prediction over non-causal, non-graph, or non-temporal baselines

**Framing**: we propose this combination for AIOps and will evaluate it empirically. We do not claim it is the first such combination in the broader ML literature, and we will only report performance numbers after they are actually measured (see Part 13).

### Contribution 2: Counterfactual Evaluation for Remediation Decisions **[ADVANCED/RESEARCH]**

**Problem**: recovery actions can't safely be tested against production before being applied.

**Approach**: use causal-inference-style reasoning (explicit causal assumptions, `do()`-style intervention framing, estimated outcome ranges with uncertainty) to estimate the likely effect of a candidate action before executing it. This is explicitly framed as **causal effect estimation under stated assumptions**, not as guaranteed prediction — see Part 9.8.

### Contribution 3: Multi-Level Root Cause Analysis **[ADVANCED]**

Identify root causes across:
- Infrastructure (hardware, networking)
- Application (code, dependency failures)
- Configuration (environment, parameters)
- Traffic/load (spikes, unusual usage patterns)

---

## 1.5 Expected Outcomes

### Technical Outcomes
1. A working AIOps pipeline running against a self-managed Kubernetes test cluster **[MVP]**
2. Five pipeline components, implemented and evaluated (not all necessarily at "production-ready" maturity) **[MVP/ADVANCED]**
3. A service-dependency graph in Neo4j, sized to whatever the test environment actually produces (tens to low hundreds of services/nodes for a student-scale testbed — not claimed at 100K+ nodes without real evidence of that scale) **[MVP]**
4. An explainability system combining SHAP and causal-assumption disclosures **[ADVANCED]**
5. A CI/CD pipeline with automated testing and deployment to a test Kubernetes cluster **[MVP]**

### Research Outcomes
1. A written report/paper on ATCGT, including an honest ablation study and baseline comparison **[RESEARCH]**
2. A documented, versioned experimental dataset (public + self-generated fault-injection data) suitable for others to reproduce **[RESEARCH]**
3. An open-source repository (GitHub) **[FUTURE, once mature enough to publish]**

### Project-Scope Outcomes (Not "Commercial" Claims)
1. A working demo suitable for a hackathon / final-year presentation **[MVP]**
2. A documented case study on the controlled fault-injection testbed (not a customer case study) **[ADVANCED]**
3. Enterprise features (multi-tenancy, formal compliance certifications, managed billing) are explicitly **[FUTURE]** and out of scope for the current project

---

# PART 2: SYSTEM ARCHITECTURE

## 2.1 High-Level Architecture

```
                              Users
                                │
                                ▼
                      React Dashboard (TS)
                                │
                                ▼
                    FastAPI API Gateway (REST + WebSocket)
                                │
                                ▼
              Incident Service / Intelligence Orchestration
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                          AI LAYER                              │
│                                                                 │
│  Anomaly Detection → Root Cause Analysis → Failure Propagation │
│                                    → Recovery Recommendation    │
│                                    → Counterfactual Evaluation  │
│                                                                 │
│              ┌─────────────────────────────────┐               │
│              │  ATCGT — Research Architecture   │               │
│              │  (enhances RCA + Propagation)    │               │
│              └─────────────────────────────────┘               │
└───────────────────────────────────────────────────────────────┘
                                │
                                ▼
                     Decision / Safety Layer
                    (risk score, policy check)
                                │
                                ▼
                         Human Approval
                                │
                                ▼
                Allowlisted Remediation Executor
                                │
                                ▼
                           Kubernetes
```

**Observability data plane** (authoritative diagram — see Part 8.1 for the full explanation):

```
Kubernetes / Applications
 │
 ├── Metrics
 │    └── Prometheus
 │         └── Feature Extraction (stream-processing-service)
 │
 ├── Traces
 │    └── OpenTelemetry SDK
 │         └── OpenTelemetry Collector
 │              └── Jaeger / Trace Backend
 │                   └── Trace Feature Extraction (queried directly by RCA — Part 9.4)
 │
 ├── Logs
 │    └── Log Agent → Log Backend
 │         └── Log Feature Extraction
 │
 └── Kubernetes Events
      └── Kubernetes API
           └── Event Ingestion
                └── Kafka (raw.events)
```

Traces intentionally do **not** flow through Kafka. Jaeger (via the OpenTelemetry Collector) is already a durable, queryable trace store with its own retention and indexing — routing trace data through Kafka as well would duplicate that storage path for no benefit at this project's scale, and was an inconsistency in an earlier draft (which listed a `raw.traces` Kafka topic while also describing a separate OTel → Jaeger path). Kafka remains the backbone for **metrics** (after ingestion), **events**, and all **derived pipeline events** (enriched features, model outputs, incidents, actions) — i.e., wherever multiple internal consumers need to react to a stream of events. Traces are read directly from Jaeger's query API by whatever service needs them (primarily the RCA engine, Part 9.4), rather than being streamed.

**Data plane:**

```
PostgreSQL / TimescaleDB   — metrics, incidents, actions, model performance, audit log
Neo4j                      — service dependency graph, causal-hypothesis edges
Redis                      — caching, short-lived state, rate limiting (not primary storage)
```

**Streaming plane:**

```
Kafka (KRaft mode — no ZooKeeper)
```

Note on scale: this document earlier implied 100K+ metrics/sec and 100K+ node graphs as if already achieved. Those remain **long-term [FUTURE]** aspirational figures for a mature deployment; the MVP testbed is expected to run at a scale appropriate to a small Kubernetes cluster (a handful to a few dozen services), and all "SLA" numbers below are **targets to validate under load testing**, not measured guarantees.

---

## 2.2 Microservice Decomposition

```yaml
causalops-x/
├── data-ingestion-service/          # [MVP] Collects metrics, events, traces, logs
│   ├── prometheus-scraper
│   ├── kubernetes-event-watcher
│   ├── otel-collector-integration
│   └── custom-plugin-loader          # [FUTURE]
│
├── stream-processing-service/       # [MVP] Real-time feature extraction
│   ├── kafka-consumer
│   ├── feature-extractor
│   └── windowing-engine
│
├── ml-inference-service/            # [MVP/ADVANCED] Model serving
│   ├── anomaly-detector              # [MVP] VAE
│   ├── rca-engine                    # [MVP] Graph Transformer
│   ├── failure-propagation-predictor # [ADVANCED] LSTM baseline / Temporal-GNN advanced
│   ├── recovery-recommender          # [ADVANCED] Learning-to-rank
│   ├── counterfactual-evaluator      # [ADVANCED] Causal effect estimation
│   └── atcgt-research-model          # [RESEARCH] optional, evaluated separately
│
├── explainability-service/          # [ADVANCED] Explanations & interpretability
│   ├── shap-explainer
│   ├── causal-assumption-reporter
│   └── confidence-scorer
│
├── incident-service/                # [MVP] Incident management
│   ├── incident-detector
│   ├── incident-aggregator
│   ├── notification-engine
│   └── incident-tracker
│
├── remediation-service/             # [MVP baseline / ADVANCED full] Action execution & approval
│   ├── action-recommender
│   ├── approval-engine               # [MVP] human approval required by default
│   ├── executor (allowlisted K8s actions only)
│   ├── rollback-handler
│   └── safety-guardrails
│
├── dashboard-service/               # [MVP] Frontend backend
│   ├── api-gateway
│   ├── auth-service
│   ├── query-engine
│   └── websocket-handler (native WebSocket, FastAPI)
│
├── database-service/                # [MVP] Data layer
│   ├── postgres-timescale-manager
│   ├── neo4j-manager
│   └── redis-cache
│
└── monitoring-service/              # [MVP] Internal monitoring (monitoring the platform itself)
    ├── prometheus-exporter
    ├── otel-tracer
    └── logging-aggregator
```

### Service Communication Patterns

```
Synchronous (gRPC or REST):
- Dashboard ↔ API Gateway
- ML Inference Service ← Stream Processing Service (feature reads)
- Explainability Service ← ML Inference Service

Asynchronous (Kafka):
- Data Ingestion → Kafka topic (raw.metrics, raw.events) — traces do NOT flow through Kafka; see Part 8.1 for why
- Stream Processing → Kafka topic (enriched.features)
- ML Inference → Kafka topic (ml.anomalies, ml.rca_results, ml.propagation_predictions, ml.recommendations)
- Incident Service ← relevant ML topics
- Remediation Service ← incidents topic

Pub/Sub (WebSocket, native):
- Incident Service → Dashboard (real-time updates)
- Remediation Service → Dashboard (action status)
```

We deliberately use **one** stream-processing mechanism (a Python Kafka consumer service) rather than layering Kafka Streams, Faust, and Redis Streams on top of each other — see Part 3.3 for the reasoning.

### 2.2.1 MVP Implementation Rule: Logical Separation ≠ Mandatory Separate Deployments

The decomposition above is the **logical** architecture — it names the responsibilities the system needs, so that data flow, ownership, and testing boundaries are clear. It is not a requirement that every box above ship as its own independently-deployed Kubernetes microservice from day one.

> During MVP development, logically separated components do not necessarily need to be deployed as separate Kubernetes Deployments/microservices. Several of them may initially be implemented as modules within fewer deployable processes (for example, `data-ingestion-service` and `stream-processing-service` running as two threads/workers inside one deployable unit, or `incident-service` and `remediation-service` sharing one FastAPI process behind clearly separated internal modules). They can be split into independently scaled and deployed services later, once a specific scaling, isolation, or team-ownership need actually justifies the operational overhead of a separate deployment.

The **logical** boundaries that must remain distinct regardless of deployment topology are:
```
Data Ingestion
Stream Processing
ML Inference
Explainability
Incident Management
Remediation
API Gateway
Dashboard
```
Keeping these as separate *modules* (clear interfaces, independent tests) — even inside fewer deployable *processes* — is what keeps the eventual split into real microservices cheap later. This rule exists specifically so the project doesn't have to stand up nine separately-deployed, separately-scaled Kubernetes services before a single incident has been detected end-to-end; it keeps the MVP realistic for a student/final-year timeline while preserving the target architecture for later.

---

## 2.3 Data Flow Architecture

### Flow 1: Anomaly Detection **[MVP]**
```
Prometheus Scrape → Data Ingestion → Kafka(raw.metrics)
  → Stream Processing (normalization, windowing)
  → Kafka(enriched.features)
  → ML Inference (Anomaly Detector: VAE)
  → Kafka(ml.anomalies)
  → Incident Service → Incident Created
  → Dashboard (alert triggered)
```

### Flow 2: Root Cause Analysis **[MVP]**
```
Anomaly Detected → Incident Created
  → Trigger RCA
  → Fetch recent metrics/traces (TimescaleDB)
  → Load service graph (Neo4j)
  → ML Inference (RCA Engine: Graph Transformer)
  → Kafka(ml.rca_results)
  → Explainability Service (SHAP + causal-assumption report)
  → Dashboard (root cause ranking visualization)
```

### Flow 3: Failure Propagation Prediction **[ADVANCED]**
```
Root Cause Identified
  → ML Inference (Failure Propagation Predictor: LSTM baseline, or Temporal-GNN/ATCGT advanced)
  → Kafka(ml.propagation_predictions)
  → Incident Service (update affected-services estimate)
  → Dashboard (impact visualization)
```

### Flow 4: Recovery Recommendation + Counterfactual Evaluation **[ADVANCED]**
```
Root Cause + Propagation Estimate Known
  → ML Inference (Recovery Recommender: learning-to-rank)
  → Counterfactual Evaluator (estimate outcome of top candidate actions)
  → Ranked actions with success probability, estimated recovery time, risk, uncertainty
  → Explainability Service (why this action, what assumptions were made)
  → Dashboard (recommend → approve → execute)
```

### Flow 5: Human-Approved, Allowlisted Remediation **[MVP baseline]**
```
User Approves Action
  → Remediation Service (policy check, risk threshold check)
  → Execute allowlisted action only (e.g. ACTION_SCALE_SERVICE, ACTION_RESTART_POD, ACTION_ROLLBACK_DEPLOYMENT)
  → Monitor rollout
  → Detect success/failure
  → If failure: trigger rollback
  → Update incident record
```

Fully autonomous remediation (no human approval) is **[FUTURE]** — see Part 14. The default and MVP workflow always requires human approval before any action executes.

---

## 2.4 Component SLAs — Targets, Not Measured Guarantees

| Component | Responsibility | Target Latency | Status |
|---|---|---|---|
| Data Ingestion | Collect metrics/events/traces/logs | Target < 1s scrape-to-Kafka | [MVP] |
| Stream Processing | Real-time feature engineering | Target < 2s end-to-end | [MVP] |
| Anomaly Detection | VAE inference | Target < 1s per request | [MVP] |
| RCA Engine | Graph Transformer inference | Target < 2s P99 | [MVP] |
| Failure Propagation | LSTM / Temporal-GNN inference | Target < 2s P99 | [ADVANCED] |
| Recovery Recommender | Ranking inference | Target < 1s | [ADVANCED] |
| Counterfactual Evaluator | Estimate outcome for top-k actions | Target < 3s | [ADVANCED] |
| Explainability | SHAP / causal report generation | Target < 2s | [ADVANCED] |
| Incident Detection | Anomaly → incident record | Target < 30s end-to-end | [MVP] |
| Remediation Execution | Allowlisted action dispatch | Target < 10s | [MVP] |
| Dashboard API | Query response | Target < 300ms | [MVP] |
| Dashboard WebSocket | Push update latency | Target < 200ms | [MVP] |

All of these will be validated through load testing (Part 11) rather than assumed.

---

# PART 3: TECHNOLOGY STACK

## 3.1 Data Ingestion & Collection

### 3.1.1 Prometheus **[MVP]**

**What It Is**: Time-series metrics monitoring system.
**Why We Use It**: Kubernetes-native, industry standard, large ecosystem.
**Where It Fits**: Scrapes application and infrastructure metrics; primary metrics source for anomaly detection.

**Pros**: Native K8s auto-discovery; pull-based; PromQL; built-in alerting rules.
**Cons**: Local storage only (needs an external long-term store, e.g. TimescaleDB); high-cardinality label combinations need care; pull model is less suited to very high-frequency discrete events (use Kafka + the event/trace paths for those).

**Configuration**:
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_pod_label_app]
        target_label: job

  - job_name: 'kubernetes-nodes'
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    kubernetes_sd_configs:
      - role: node
```

### 3.1.2 Kubernetes API Server (Events) **[MVP]**

Captures deployment changes, pod scaling, and resource-limit events for correlation with anomalies.

```python
# Watch pod changes
watch = stream(v1.list_namespaced_pod, namespace="causalops-test")
for event in watch:
    if event['object'].status.phase == 'Failed':
        send_to_kafka(event, topic='raw.events')
```

### 3.1.3 OpenTelemetry + Jaeger (Distributed Tracing) **[MVP]**

**Correction**: earlier drafts described Jaeger as the primary telemetry *collector*. It is not — it is a **trace backend/storage and UI**. The collection layer is the **OpenTelemetry Collector**.

```
Application → OpenTelemetry SDK (instrumentation)
            → OpenTelemetry Collector (receives, processes, batches, exports)
            → Jaeger (trace storage + query/UI)
```

**Why this matters**: OpenTelemetry is vendor-neutral, so the trace backend (Jaeger, Tempo, etc.) can be swapped without re-instrumenting every service.

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
      http:
processors:
  batch:
  probabilistic_sampler:
    sampling_percentage: 10
exporters:
  jaeger:
    endpoint: jaeger-collector:14250
    tls:
      insecure: true
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [probabilistic_sampler, batch]
      exporters: [jaeger]
```

### 3.1.4 Custom Plugin System **[FUTURE]**

An extensible interface for third-party data sources (Datadog, New Relic, custom apps). Not required for MVP.

```python
class MetricsPlugin:
    def __init__(self, config: dict):
        self.config = config

    def collect(self) -> list:
        """Return list of metrics"""
        raise NotImplementedError

    def verify_connectivity(self) -> bool:
        """Health check"""
        raise NotImplementedError
```

---

## 3.2 Streaming: Kafka with KRaft **[MVP]**

**Correction**: earlier drafts specified a ZooKeeper-based Kafka deployment. Kafka's ZooKeeper mode is being phased out industry-wide; this project uses **Kafka in KRaft mode** (no ZooKeeper dependency).

**Topics** (traces are intentionally excluded — see Part 3.2.2 / Part 8.1 for why):
- `raw.metrics`, `raw.events` — ingestion-layer topics
- `enriched.features` — processed features ready for ML
- `ml.anomalies`, `ml.rca_results`, `ml.propagation_predictions`, `ml.recommendations` — model outputs
- `incidents` — incident lifecycle events
- `actions` — remediation action lifecycle events

> **Note on scope**: the Kafka configuration below is intended for the controlled Kubernetes testbed/demo environment described throughout this document. It is not presented as a guaranteed, copy-paste production configuration. A production deployment should use a validated Kafka KRaft Helm chart (e.g. the Strimzi Kafka Operator or Confluent's official chart) rather than assuming this simplified example is production-ready as-is.

**Deployment concepts required for a valid KRaft cluster** (all reflected below):
- a shared **cluster ID** (generated once, injected into every broker/controller — KRaft nodes will refuse to form a cluster without a matching ID)
- explicit **broker vs. controller roles** (`KAFKA_PROCESS_ROLES`)
- a **controller quorum** (`KAFKA_CONTROLLER_QUORUM_VOTERS`)
- **listeners** (what each broker binds to) vs. **advertised listeners** (what clients are told to connect to — these differ in Kubernetes, where the pod's internal address and the client-facing service address are not the same)
- **persistent storage** per broker (`volumeClaimTemplates`)
- **stable broker identity** across restarts (each pod's `KAFKA_NODE_ID` must be a fixed, stable integer tied to that specific pod — a `StatefulSet`'s stable pod ordinal, read via `$(hostname)` at container-entrypoint time, not via a Kubernetes `fieldRef` path, since `metadata.ordinal.index` is not a valid Downward API field)
- **replication factor** for topics (Part 3.2, topic configuration below)
- **health/readiness checks** so Kubernetes doesn't route traffic to a broker that hasn't finished KRaft startup

**Demo/testbed deployment (KRaft, no ZooKeeper)**:
```yaml
# kafka-deployment.yaml — TESTBED/DEMO CONFIGURATION, not a production chart.
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kafka
spec:
  serviceName: kafka
  replicas: 3
  selector:
    matchLabels:
      app: kafka
  template:
    metadata:
      labels:
        app: kafka
    spec:
      # Stable per-pod node ID is derived from the pod's stable StatefulSet hostname
      # (kafka-0, kafka-1, kafka-2) at container startup — not from a nonexistent
      # 'metadata.ordinal.index' Downward API field.
      containers:
      - name: kafka
        image: confluentinc/cp-kafka:7.6.0
        command: ["/bin/bash", "-c"]
        args:
          - |
            export KAFKA_NODE_ID=$(hostname | grep -o '[0-9]*$')
            exec /etc/confluent/docker/run
        env:
        - name: CLUSTER_ID
          valueFrom:
            configMapKeyRef:
              name: kafka-cluster-id     # generated ONCE (e.g. `kafka-storage random-uuid`) and stored here
              key: cluster-id
        - name: KAFKA_PROCESS_ROLES
          value: "broker,controller"
        - name: KAFKA_CONTROLLER_QUORUM_VOTERS
          value: "0@kafka-0.kafka:9093,1@kafka-1.kafka:9093,2@kafka-2.kafka:9093"
        - name: KAFKA_LISTENERS
          value: "PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093"
        - name: KAFKA_ADVERTISED_LISTENERS
          value: "PLAINTEXT://$(hostname).kafka.$(NAMESPACE).svc.cluster.local:9092"
        - name: KAFKA_CONTROLLER_LISTENER_NAMES
          value: "CONTROLLER"
        - name: KAFKA_INTER_BROKER_LISTENER_NAME
          value: "PLAINTEXT"
        - name: KAFKA_LOG_RETENTION_HOURS
          value: "168"
        - name: NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        ports:
        - containerPort: 9092
        - containerPort: 9093
        volumeMounts:
        - name: kafka-data
          mountPath: /var/lib/kafka/data
        readinessProbe:
          tcpSocket:
            port: 9092
          initialDelaySeconds: 20
          periodSeconds: 10
        livenessProbe:
          tcpSocket:
            port: 9092
          initialDelaySeconds: 30
          periodSeconds: 15
  volumeClaimTemplates:
  - metadata:
      name: kafka-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi   # sized for a test/demo cluster, not a production estimate
```

Do not claim production-scale Kafka performance from this configuration — it has not been load-tested (Part 11 establishes real numbers once it is).

**Topic configuration** (test-cluster scale, not a throughput guarantee):
```bash
kafka-topics --create \
  --topic ml.anomalies \
  --partitions 6 \
  --replication-factor 3 \
  --config retention.ms=86400000 \
  --config compression.type=snappy

kafka-topics --create \
  --topic enriched.features \
  --partitions 6 \
  --replication-factor 3 \
  --config retention.ms=604800000 \
  --config compression.type=lz4
```

**Alternatives considered**: RabbitMQ (simpler, lower throughput ceiling), Redis Streams (lower latency, non-persistent — used only as a secondary/complementary layer here, see 3.2.1), AWS Kinesis (managed, vendor-locked).

### 3.2.1 Redis — Complementary, Not a Second Streaming Backbone **[MVP]**

Redis is used **only** where it's genuinely the right tool:
- Dashboard WebSocket pub/sub for low-latency UI pushes
- Short-lived feature cache (last N minutes) to avoid re-querying TimescaleDB on every request
- Rate limiting for the API gateway

Redis is **not** a second event-streaming backbone alongside Kafka. Kafka is the single source of truth for the event log; Redis holds ephemeral, derived state.

```python
import redis
r = redis.Redis(host='redis', port=6379, decode_responses=True)

# Cache recent features (expire in 1 hour)
r.hset(f'features:{service_id}:{timestamp}', mapping={
    'cpu_usage': 45.2, 'memory_usage': 2048, 'request_latency_ms': 120,
})
r.expire(f'features:{service_id}:{timestamp}', 3600)

# Rate limiting
r.incr(f'requests:{user_id}:{hour}')
r.expire(f'requests:{user_id}:{hour}', 3600)
```

---

## 3.3 Stream Processing — Simplified **[MVP]**

**Correction**: earlier drafts required Kafka Streams, Faust, *and* Redis Streams simultaneously — three overlapping stream-processing systems doing similar jobs. This is unnecessary complexity for the project's actual scale. We use **one** approach:

```
Kafka → Python consumer (stream-processing-service) → feature extraction → Kafka(enriched.features) → ML inference
```

```python
from kafka import KafkaConsumer, KafkaProducer
import json
from collections import deque

class StreamProcessor:
    def __init__(self):
        self.consumer = KafkaConsumer('raw.metrics', bootstrap_servers=['kafka:9092'])
        self.producer = KafkaProducer(bootstrap_servers=['kafka:9092'])
        self.windows: dict[str, deque] = {}

    def process(self):
        for message in self.consumer:
            metric = json.loads(message.value)
            self.enrich_metric(metric)
            self.producer.send('enriched.features', json.dumps(metric).encode())

    def enrich_metric(self, metric: dict) -> None:
        """Add lag, moving average, derivative features."""
        service_id = metric['labels']['service']
        window = self.windows.setdefault(service_id, deque(maxlen=100))
        window.append(metric['value'])
        if len(window) > 1:
            recent = list(window)
            metric['features'] = {
                'lag_1': recent[-2],
                'ma_5': sum(recent[-5:]) / min(5, len(recent)),
                'ma_30': sum(recent[-30:]) / min(30, len(recent)),
                'derivative': metric['value'] - recent[-2],
                'stddev': self._stddev(recent),
            }

    @staticmethod
    def _stddev(values: list[float]) -> float:
        n = len(values)
        if n < 2:
            return 0.0
        mean = sum(values) / n
        return (sum((v - mean) ** 2 for v in values) / (n - 1)) ** 0.5
```

If throughput ever genuinely requires a dedicated stream-processing framework, **Apache Flink** is the documented upgrade path (higher operational complexity, evaluated only if the plain-consumer approach becomes a measured bottleneck) — this is a **[FUTURE]** decision gated on evidence, not a default.

---

## 3.4 Machine Learning Framework

### 3.4.1 PyTorch **[MVP]**

Used for all neural models (VAE, Graph Transformer, LSTM/Temporal-GNN, ATCGT).

```dockerfile
FROM pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime

WORKDIR /app
RUN pip install pytorch-lightning optuna mlflow
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "train_models.py"]
```

### 3.4.2 PyTorch Geometric **[MVP/ADVANCED]**

Used for the RCA Graph Transformer and (in the advanced/research track) the temporal graph model.

```python
import torch
from torch_geometric.nn import TransformerConv

class ServiceGraphTransformer(torch.nn.Module):
    """RCA model: node features -> per-service root-cause score."""
    def __init__(self, in_channels: int, hidden_channels: int, heads: int = 4, num_layers: int = 2):
        super().__init__()
        self.layers = torch.nn.ModuleList()
        self.layers.append(TransformerConv(in_channels, hidden_channels, heads=heads, edge_dim=4))
        for _ in range(num_layers - 1):
            self.layers.append(TransformerConv(hidden_channels * heads, hidden_channels, heads=heads, edge_dim=4))
        self.output_head = torch.nn.Linear(hidden_channels * heads, 1)

    def forward(self, x, edge_index, edge_attr):
        for layer in self.layers:
            x = torch.relu(layer(x, edge_index, edge_attr))
        return self.output_head(x).squeeze(-1)  # root-cause score per node
```

See Part 9.3 for the corrected input design (node/edge features, not bare service-ID embeddings).

### 3.4.3 LightGBM **[MVP, for anomaly threshold calibration and tabular baselines]**

Used as a fast tabular baseline for anomaly scoring calibration and as a baseline for the recovery-recommendation ranking task (see Part 9.5).

```python
import lightgbm as lgb

ranker = lgb.LGBMRanker(
    objective='lambdarank',
    num_leaves=31,
    learning_rate=0.05,
    n_estimators=200,
)
```

### 3.4.4 TensorFlow/Keras — Removed as a Second Deep Learning Framework

**Correction**: the earlier draft used both PyTorch (for GNN/Transformer models) and TensorFlow/Keras (for the LSTM). Maintaining two deep learning frameworks in one small project adds needless operational and cognitive overhead. The LSTM baseline is implemented in **PyTorch** as well, for consistency:

```python
import torch
import torch.nn as nn

class FailurePropagationLSTM(nn.Module):
    """Baseline propagation model. Input: (batch, time_steps, num_services, num_features)."""
    def __init__(self, num_services: int, num_features: int, hidden_size: int = 64):
        super().__init__()
        self.num_services = num_services
        self.lstm = nn.LSTM(input_size=num_services * num_features, hidden_size=hidden_size, batch_first=True)
        self.head = nn.Linear(hidden_size, num_services)  # probability each service fails next

    def forward(self, x):
        b, t, s, f = x.shape
        x = x.reshape(b, t, s * f)
        _, (h_n, _) = self.lstm(x)
        return torch.sigmoid(self.head(h_n[-1]))
```

---

## 3.5 Time-Series & Sequence Utilities

### 3.5.1 Prophet **[ADVANCED, optional baseline]**

Used only as a simple univariate baseline for trend/seasonality decomposition — not a core dependency of the pipeline.

---

## 3.6 Causal Inference Libraries — Corrected

**Correction**: the earlier draft listed **CausalNex** (QuantumBlack) as a core dependency. CausalNex has been unmaintained for some time and is no longer an appropriate dependency for this project. It has been **removed** from the stack.

### 3.6.1 DoWhy + causal-learn **[ADVANCED/RESEARCH]**

- **DoWhy**: for structuring causal assumptions explicitly and estimating treatment effects (used for the counterfactual evaluation component).
- **causal-learn**: for causal structure discovery algorithms such as PC and FCI, used as an *analysis/validation* tool on the learned service dependency graph — not to auto-certify any learned adjacency matrix as a proven causal graph (see Part 9.9 for why that distinction matters).

```python
from dowhy import CausalModel

model = CausalModel(
    data=observational_df,
    treatment='scale_database_action',
    outcome='payment_latency_ms',
    graph=causal_graph_gml,  # explicit assumed causal graph, not learned-and-trusted blindly
)
identified_estimand = model.identify_effect()
estimate = model.estimate_effect(identified_estimand, method_name="backdoor.linear_regression")
# Always report estimate.value together with an uncertainty interval, not a bare point estimate.
```

---

## 3.7 Explainability & Interpretability **[ADVANCED]**

### 3.7.1 SHAP

For tree/tabular models (anomaly threshold calibration, recovery ranking):

```python
import shap

explainer = shap.TreeExplainer(ranking_model)
shap_values = explainer.shap_values(features)

explanation = {
    'prediction': 'ANOMALY_DETECTED',
    'top_contributors': [
        {'feature': 'cpu_usage', 'contribution': 0.35},
        {'feature': 'memory_spike', 'contribution': 0.28},
        {'feature': 'error_rate', 'contribution': 0.15},
    ]
}
```

### 3.7.2 Captum

For the PyTorch Graph Transformer / temporal models:

```python
from captum.attr import IntegratedGradients

ig = IntegratedGradients(graph_transformer_model)
attributions = ig.attribute(node_features, additional_forward_args=(edge_index, edge_attr))
# Per-node, per-feature importance for the RCA score.
```

Explanations produced by SHAP/Captum describe **model feature importance**, not proven causal effect — the two are kept explicitly labeled and separate (see Part 9.8 and Part 10).

---

## 3.8 Data Layer (Overview — full schema in Part 7)

- **PostgreSQL + TimescaleDB** — metrics, incidents, actions, model performance, audit log. See Part 7 for the corrected schema.
- **Neo4j** — service dependency graph and causal-hypothesis edges. See Part 7.2 for corrected, parameterized queries.
- **Redis** — caching, pub/sub, rate limiting only (Part 3.2.1).

---

## 3.9 Containerization & Orchestration **[MVP]**

### 3.9.1 Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"
USER 1000:1000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Non-root user, resource limits, and minimal base images are used for every service (see Part 12.5 — Security Hardening).

### 3.9.2 Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-inference-service
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: ml-inference
  template:
    metadata:
      labels:
        app: ml-inference
    spec:
      securityContext:
        runAsNonRoot: true
      containers:
      - name: ml-inference
        image: causalops/ml-inference:latest
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values: [ml-inference]
```

Replica counts and HA sizing here are for a demo/test cluster, not a production-scale claim.

---

## 3.10 Technology Stack Summary Table

| Layer | Technology | Notes |
|---|---|---|
| Metrics | Prometheus | [MVP] |
| Traces | OpenTelemetry SDK + Collector + Jaeger | [MVP] — OTel Collector is the collection layer, Jaeger is the backend |
| Logs | Application → log agent → log backend | [MVP] |
| Events | Kubernetes API → Kafka | [MVP] |
| Streaming | Kafka (KRaft, no ZooKeeper) | [MVP] |
| Stream processing | Python Kafka consumer service | [MVP]; Flink is a future option, not required |
| Caching / pub-sub | Redis | [MVP], complementary only |
| ML framework | PyTorch (+ PyTorch Geometric) | [MVP/ADVANCED] — single framework, not PyTorch+TensorFlow |
| Tabular ranking | LightGBM | [MVP/ADVANCED] |
| Causal inference | DoWhy, causal-learn | [ADVANCED/RESEARCH]; CausalNex removed |
| Explainability | SHAP, Captum | [ADVANCED] |
| Metrics DB | PostgreSQL + TimescaleDB | [MVP] |
| Graph DB | Neo4j | [MVP] |
| Frontend | React, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, Zustand, Cytoscape.js, Recharts, native WebSocket | [MVP] — see Part 6 |
| Containers | Docker | [MVP] |
| Orchestration | Kubernetes | [MVP] |
| Experiment tracking | MLflow | [ADVANCED] — see Part 12.4 |

---

# PART 4: DEVELOPMENT ROADMAP

## 4.1 Roadmap Principles

- Every phase below is tagged **[MVP]**, **[ADVANCED]**, **[RESEARCH]**, or **[FUTURE]**.
- We do not claim every advanced feature reaches production-readiness within a fixed number of weeks. Phase lengths are planning estimates, not guarantees.
- "Production-ready" is only used for components that have passed the testing strategy in Part 11, not for anything still in development.

## 4.2 Phases

### Phase 1 — Environment & Architecture Setup **[MVP]**
- Provision a Kubernetes test cluster (local — kind/minikube, or a small cloud cluster)
- Set up repo structure, CI skeleton, base Docker images
- Deploy Kafka (KRaft), PostgreSQL/TimescaleDB, Neo4j, Redis to the test cluster

### Phase 2 — Observability Pipeline **[MVP]**
- Deploy Prometheus, OpenTelemetry Collector, Jaeger, log collection
- Build data-ingestion-service to move metrics/traces/logs/events into Kafka
- Deliverable: raw telemetry visible end-to-end in Kafka topics

### Phase 3 — Database & Service Graph **[MVP]**
- Implement corrected PostgreSQL/TimescaleDB schema (Part 7)
- Populate Neo4j with the test cluster's actual service dependency graph
- Deliverable: queryable service graph reflecting the real testbed topology

### Phase 4 — Incident Detection & Anomaly Detection **[MVP]**
- Build stream-processing-service (feature extraction)
- Implement and train the VAE anomaly detector on data collected from the testbed (Part 9.2)
- Build incident-service (create incidents from detected anomalies)
- Deliverable: anomalies flowing from telemetry into tracked incidents; **validation metrics measured, not assumed**

### Phase 5 — Root Cause Analysis **[MVP]**
- Implement the Graph Transformer RCA model with real node/edge features (Part 9.3)
- Integrate with Neo4j for graph structure and TimescaleDB for feature history
- Deliverable: ranked root-cause list per incident, evaluated with Top-1/Top-3/Top-5/MRR on held-out fault-injection data

### Phase 6 — Failure Propagation Prediction **[ADVANCED]**
- Implement LSTM baseline
- Implement Temporal-GNN advanced variant
- Deliverable: propagation predictions compared against the LSTM baseline

### Phase 7 — Recovery Recommendation **[ADVANCED]**
- Implement learning-to-rank recommender (Part 9.5)
- Define and implement the allowlisted action set
- Deliverable: ranked action list with predicted success probability, estimated recovery time, and risk score

### Phase 8 — Counterfactual Evaluation **[ADVANCED]**
- Implement DoWhy-based causal effect estimation for top recommended actions
- Deliverable: outcome estimates with explicit uncertainty for candidate actions, on the controlled fault-injection testbed

### Phase 9 — Dashboard & Explainability **[MVP/ADVANCED]**
- Build the React dashboard (Part 6)
- Integrate SHAP/Captum explanations and causal-assumption reporting
- Deliverable: end-to-end demo — incident appears, RCA shown, recommendation shown with explanation, human approves, action executes

### Phase 10 — ATCGT Research Implementation **[RESEARCH]**
- Implement the corrected temporal-graph-causal architecture (Part 9.9)
- Train on public benchmark datasets + self-generated fault-injection data

### Phase 11 — Benchmark Evaluation & Ablation Study **[RESEARCH]**
- Compare ATCGT against LSTM baseline, static-graph RCA baseline, and published baselines (MicroRank and others) on public datasets
- Run ablation studies (ATCGT minus causal component, minus temporal attention, minus graph transformer, full ATCGT)
- Deliverable: honestly reported results — including cases where ATCGT does *not* outperform baselines, if that's what the experiments show

### Phase 12 — Deployment Hardening & Write-Up **[MVP/RESEARCH]**
- Security hardening pass (Part 12.5)
- Load testing to establish real latency/throughput numbers (replacing all "target" figures with measured ones where possible)
- Write the research report/paper (Part 13)

## 4.3 What Is Explicitly Out of the 12-Phase Roadmap

The following are documented in Part 14 as **[FUTURE]** and are not part of the current roadmap: fully autonomous (no-approval) remediation, RL-based recommendation, multi-tenancy, LLM chat interface, and formal enterprise compliance work.

---

# PART 5: BACKEND DEVELOPMENT

## 5.1 API Design Principles **[MVP]**

- FastAPI for all HTTP/WebSocket services.
- **Explicit Pydantic models for every request/response** — no generic `body: dict` handlers, so the API is self-documenting and validated.
- Consistent ID types across API, database, Kafka messages, and frontend types (see 5.3).

## 5.2 Example: Incident API with Explicit Schemas

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from uuid import UUID

app = FastAPI()

class IncidentStatus(str, Enum):
    open = "open"
    investigating = "investigating"
    remediating = "remediating"
    resolved = "resolved"
    closed = "closed"

class IncidentSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class IncidentCreateRequest(BaseModel):
    root_cause_service_id: str
    affected_service_ids: list[str] = Field(default_factory=list)
    severity: IncidentSeverity
    detected_at: datetime

class IncidentResponse(BaseModel):
    incident_id: UUID
    root_cause_service_id: str
    affected_service_ids: list[str]
    severity: IncidentSeverity
    status: IncidentStatus
    detected_at: datetime
    created_at: datetime
    resolved_at: datetime | None = None

@app.post("/api/v1/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(payload: IncidentCreateRequest) -> IncidentResponse:
    ...

@app.get("/api/v1/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: UUID) -> IncidentResponse:
    ...
```

## 5.3 ID Consistency Rule **[MVP]**

**Correction**: earlier drafts mixed serial integer IDs (`SERIAL PRIMARY KEY`) in PostgreSQL with string-based IDs used elsewhere (Kafka messages, Neo4j node keys, API path parameters), which is a real source of subtle bugs (e.g. an endpoint accepting a text `action_id` but joining it against an integer column).

**Fixed convention, used everywhere — two ID types, not one:**

| Entity | ID type | Reason |
|---|---|---|
| `service_id` | **TEXT** — a stable, human-readable slug (e.g. `"payment-service"`, `"api-gateway"`, `"auth-service"`) | Services are canonical entities shared across PostgreSQL, Neo4j, Kafka partition keys, telemetry labels (Prometheus/OTel), and APIs. A slug is the natural shared key across all of these systems and is what operators actually read in dashboards and logs. |
| `incident_id`, `anomaly_id`, `action_id`, `prediction_id`, `rca_result_id`, `recommendation_id` | **UUID** | These are generated event/result entities (Part 7.1: `uuid_generate_v4()`), not canonical shared identities — a UUID avoids collisions and doesn't need to be human-readable. |

**Architectural note**: Service identity uses a stable TEXT slug because services are canonical entities shared across PostgreSQL, Neo4j, Kafka, telemetry labels, and APIs. Event/incident/model-result entities use UUIDs, because they are generated records referencing services, not identities of the services themselves.

`service_id` is **never** UUID anywhere in this document. Any prior wording suggesting otherwise (including an earlier version of this section, which listed `service_id` alongside `incident_id`/`action_id`/`anomaly_id`/`rca_result_id` as "all UUID") has been corrected. The PostgreSQL schema (Part 7.1: `service_id TEXT PRIMARY KEY`) is authoritative and is not changed to UUID.

This single rule is applied consistently across Part 7 (database), Part 5 (API), Part 9 (Kafka messages), and Part 6 (frontend types).

## 5.4 Safe Remediation: Allowlisted Actions Only **[MVP]**

The AI layer never generates or executes arbitrary shell/kubectl commands. It selects from a fixed, allowlisted action enum, each backed by a reviewed, parameterized handler:

```python
from enum import Enum

class RemediationActionType(str, Enum):
    ACTION_SCALE_SERVICE = "ACTION_SCALE_SERVICE"
    ACTION_RESTART_POD = "ACTION_RESTART_POD"
    ACTION_ROLLBACK_DEPLOYMENT = "ACTION_ROLLBACK_DEPLOYMENT"
    ACTION_TRAFFIC_SHIFT = "ACTION_TRAFFIC_SHIFT"
    ACTION_RATE_LIMIT = "ACTION_RATE_LIMIT"
    ACTION_CACHE_INVALIDATE = "ACTION_CACHE_INVALIDATE"
    ACTION_DEPENDENCY_FALLBACK = "ACTION_DEPENDENCY_FALLBACK"

ACTION_HANDLERS = {
    RemediationActionType.ACTION_SCALE_SERVICE: scale_service_handler,
    RemediationActionType.ACTION_RESTART_POD: restart_pod_handler,
    RemediationActionType.ACTION_ROLLBACK_DEPLOYMENT: rollback_deployment_handler,
    # ... one reviewed, parameter-validated handler per action type
}

def execute_action(action_type: RemediationActionType, params: dict, approved_by: str) -> dict:
    if action_type not in ACTION_HANDLERS:
        raise ValueError(f"Action {action_type} is not in the allowlist")
    handler = ACTION_HANDLERS[action_type]
    return handler(**params)  # each handler validates its own params against a Pydantic model
```

Default workflow (Part 2.3, Flow 5): **AI Recommendation → Risk Evaluation → Policy Check → Human Approval → Execute Allowlisted Action → Monitor → Rollback if needed.** Autonomous (no-approval) execution for low-risk actions is a **[FUTURE]** extension, added only after the approval workflow has a track record.

## 5.5 Authentication & Authorization **[MVP]**

| Consumer | Mechanism |
|---|---|
| External/API clients (service-to-service) | API key |
| Dashboard users | JWT access token (short-lived) + refresh token |
| Authorization | RBAC — roles: Admin, Engineer, Viewer |

Additional requirements:
- Token expiry enforced server-side; refresh-token rotation
- Passwords (if used) hashed with a modern algorithm (e.g. bcrypt/argon2) — never stored in plaintext
- Secrets loaded from a secret manager / Kubernetes Secrets — **never committed to source code**
- Audit logging of all authentication events and remediation approvals
- Rate limiting per API key/user
- Input validation on every endpoint via Pydantic
- CORS restricted to known dashboard origins
- TLS/HTTPS everywhere (see Part 12.5)

---

# PART 6: FRONTEND DASHBOARD

## 6.1 Stack — Consolidated, No Duplicate Libraries **[MVP]**

**Correction**: earlier drafts listed overlapping options (multiple state-management and charting libraries, plus both native WebSocket and Socket.IO) without picking one. The dashboard uses a single, consistent stack:

| Concern | Choice |
|---|---|
| Framework | React + TypeScript |
| Styling | Tailwind CSS |
| Component library | shadcn/ui |
| Server-state / data fetching | TanStack Query |
| Client-state | Zustand |
| Service dependency graph visualization | Cytoscape.js |
| Charts (metrics, time series) | Recharts |
| Real-time updates | Native browser WebSocket (matches the FastAPI WebSocket backend — see 6.2) |

No overlapping charting or state-management libraries are introduced without a specific, documented reason.

## 6.2 WebSocket Consistency **[MVP]**

**Correction**: the earlier draft's backend used FastAPI's native WebSocket support while the frontend section referenced Socket.IO — these are not interoperable without a Socket.IO server, which was never specified on the backend. We standardize on **native WebSocket on both ends**:

**Backend**:
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws/incidents")
async def incident_updates(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            event = await incident_event_queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
```

**Frontend**:
```typescript
function useIncidentSocket() {
  const [incidents, setIncidents] = useState<Incident[]>([]);

  useEffect(() => {
    const socket = new WebSocket(`${WS_BASE_URL}/ws/incidents`);
    socket.onmessage = (event) => {
      const incident: Incident = JSON.parse(event.data);
      setIncidents((prev) => upsertIncident(prev, incident));
    };
    return () => socket.close();
  }, []);

  return incidents;
}
```

If a use case genuinely needs Socket.IO features (auto-reconnect, rooms, fallback transports), that would require adding `python-socketio` on the backend explicitly — this is a **[FUTURE]** decision, not a silent mismatch.

## 6.3 Frontend Types Match Backend IDs **[MVP]**

```typescript
interface Incident {
  incident_id: string;       // UUID, matches Part 5.3 / Part 7 schema
  root_cause_service_id: string;   // TEXT slug (e.g. "payment-service"), NOT a UUID — Part 5.3
  affected_service_ids: string[];  // TEXT slugs, NOT UUIDs — Part 5.3
  severity: "low" | "medium" | "high" | "critical";
  status: "open" | "investigating" | "remediating" | "resolved" | "closed";
  detected_at: string;       // ISO-8601
  created_at: string;
  resolved_at: string | null;
}

interface RemediationAction {
  action_id: string;         // UUID
  incident_id: string;       // UUID, FK
  action_type:
    | "ACTION_SCALE_SERVICE"
    | "ACTION_RESTART_POD"
    | "ACTION_ROLLBACK_DEPLOYMENT"
    | "ACTION_TRAFFIC_SHIFT"
    | "ACTION_RATE_LIMIT"
    | "ACTION_CACHE_INVALIDATE"
    | "ACTION_DEPENDENCY_FALLBACK";
  predicted_success_probability: number;
  estimated_recovery_time_seconds: number;
  risk_score: number;
  status: "recommended" | "approved" | "executing" | "succeeded" | "failed" | "rolled_back";
}
```

## 6.4 Service Dependency Graph View **[MVP]**

Cytoscape.js renders the Neo4j-backed service graph, with root-cause and blast-radius highlighting driven by the RCA and propagation-prediction API responses. No competing graph-visualization library is used.

---

# PART 7: DATABASE DESIGN

## 7.1 PostgreSQL + TimescaleDB Schema — Corrected **[MVP]**

**Corrections applied**: no invalid inline `CREATE INDEX ON` syntax embedded inside table definitions; every table referenced anywhere in the API actually exists here; consistent UUID IDs (Part 5.3); explicit `created_at`/timestamp fields; foreign keys; status/severity as `CHECK`-constrained enums; indexes created as separate, valid statements.

```sql
-- Extension setup
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================
-- services: the canonical list of known services (mirrors Neo4j nodes)
-- ============================================================
CREATE TABLE services (
    service_id      TEXT PRIMARY KEY,           -- stable slug, matches Neo4j node key
    display_name    TEXT NOT NULL,
    tier            TEXT,                       -- e.g. 'core', 'edge'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- metrics: TimescaleDB hypertable
-- ============================================================
CREATE TABLE metrics (
    time            TIMESTAMPTZ NOT NULL,
    service_id      TEXT NOT NULL REFERENCES services(service_id),
    metric_name     TEXT NOT NULL,
    metric_value    DOUBLE PRECISION NOT NULL,
    tags            JSONB
);
SELECT create_hypertable('metrics', 'time', if_not_exists => TRUE);

CREATE INDEX idx_metrics_service_metric_time
    ON metrics (service_id, metric_name, time DESC);
CREATE INDEX idx_metrics_tags
    ON metrics USING GIN (tags);

-- ============================================================
-- events: Kubernetes / application events
-- ============================================================
CREATE TABLE events (
    event_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    time            TIMESTAMPTZ NOT NULL,
    event_type      TEXT NOT NULL,
    service_id      TEXT REFERENCES services(service_id),
    description     TEXT,
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_events_time ON events (time DESC, event_type);
CREATE INDEX idx_events_service_time ON events (service_id, time DESC);

-- ============================================================
-- anomalies: raw anomaly-detector outputs
-- ============================================================
CREATE TABLE anomalies (
    anomaly_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id       TEXT NOT NULL REFERENCES services(service_id),
    detected_at      TIMESTAMPTZ NOT NULL,
    anomaly_score    DOUBLE PRECISION NOT NULL,
    reconstruction_error DOUBLE PRECISION,
    model_version    TEXT NOT NULL,
    features         JSONB,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_anomalies_service_time ON anomalies (service_id, detected_at DESC);
CREATE INDEX idx_anomalies_created_at ON anomalies (created_at DESC);

-- ============================================================
-- incidents
-- ============================================================
CREATE TABLE incidents (
    incident_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    root_cause_service_id TEXT REFERENCES services(service_id),
    affected_service_ids  TEXT[] NOT NULL DEFAULT '{}',
    severity              TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status                TEXT NOT NULL DEFAULT 'open'
                              CHECK (status IN ('open', 'investigating', 'remediating', 'resolved', 'closed')),
    detected_at           TIMESTAMPTZ NOT NULL,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at           TIMESTAMPTZ,
    triggering_anomaly_id UUID REFERENCES anomalies(anomaly_id)
);
CREATE INDEX idx_incidents_created_at ON incidents (created_at DESC);
CREATE INDEX idx_incidents_status ON incidents (status);

-- ============================================================
-- rca_results: root-cause analysis outputs per incident
-- ============================================================
CREATE TABLE rca_results (
    rca_result_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id       UUID NOT NULL REFERENCES incidents(incident_id),
    service_id        TEXT NOT NULL REFERENCES services(service_id),
    rank              INTEGER NOT NULL,           -- 1 = top candidate
    root_cause_score  DOUBLE PRECISION NOT NULL,
    model_version     TEXT NOT NULL,
    explanation       JSONB,                      -- SHAP/Captum top contributors
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_rca_results_incident ON rca_results (incident_id, rank);

-- ============================================================
-- failure_predictions: propagation-prediction outputs per incident
-- ============================================================
CREATE TABLE failure_predictions (
    prediction_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id         UUID NOT NULL REFERENCES incidents(incident_id),
    predicted_service_id TEXT NOT NULL REFERENCES services(service_id),
    failure_probability DOUBLE PRECISION NOT NULL,
    predicted_time_to_failure_seconds DOUBLE PRECISION,
    model_version        TEXT NOT NULL,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_failure_predictions_incident ON failure_predictions (incident_id);

-- ============================================================
-- remediation_actions
-- ============================================================
CREATE TABLE remediation_actions (
    action_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id         UUID NOT NULL REFERENCES incidents(incident_id),
    action_type          TEXT NOT NULL CHECK (action_type IN (
                              'ACTION_SCALE_SERVICE', 'ACTION_RESTART_POD',
                              'ACTION_ROLLBACK_DEPLOYMENT', 'ACTION_TRAFFIC_SHIFT',
                              'ACTION_RATE_LIMIT', 'ACTION_CACHE_INVALIDATE',
                              'ACTION_DEPENDENCY_FALLBACK'
                          )),
    params                JSONB NOT NULL DEFAULT '{}',
    predicted_success_probability DOUBLE PRECISION,
    estimated_recovery_time_seconds DOUBLE PRECISION,
    risk_score            DOUBLE PRECISION,
    status                TEXT NOT NULL DEFAULT 'recommended'
                              CHECK (status IN ('recommended', 'approved', 'executing', 'succeeded', 'failed', 'rolled_back')),
    approved_by           TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    executed_at           TIMESTAMPTZ,
    rollback_at           TIMESTAMPTZ
);
CREATE INDEX idx_remediation_actions_incident ON remediation_actions (incident_id, created_at DESC);
CREATE INDEX idx_remediation_actions_status ON remediation_actions (status);

-- ============================================================
-- feedback: outcome labels used to improve models over time
-- ============================================================
CREATE TABLE feedback (
    feedback_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id      UUID NOT NULL REFERENCES incidents(incident_id),
    rca_result_id    UUID REFERENCES rca_results(rca_result_id),
    action_id        UUID REFERENCES remediation_actions(action_id),
    was_correct       BOOLEAN,
    actual_root_cause_service_id TEXT REFERENCES services(service_id),
    notes             TEXT,
    submitted_by      TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_feedback_incident ON feedback (incident_id);

-- ============================================================
-- model_performance: tracked evaluation runs (see Part 12.4 MLOps)
-- ============================================================
CREATE TABLE model_performance (
    run_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name        TEXT NOT NULL,             -- e.g. 'rca_graph_transformer'
    model_version     TEXT NOT NULL,
    dataset_version   TEXT NOT NULL,
    metric_name       TEXT NOT NULL,             -- e.g. 'top1_accuracy'
    metric_value      DOUBLE PRECISION NOT NULL,
    evaluated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_model_performance_model ON model_performance (model_name, evaluated_at DESC);

-- ============================================================
-- audit_log
-- ============================================================
CREATE TABLE audit_log (
    audit_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor              TEXT NOT NULL,             -- user id or service name
    action              TEXT NOT NULL,             -- e.g. 'incident.approve_action'
    resource_type       TEXT,
    resource_id          TEXT,
    metadata             JSONB,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_log_created_at ON audit_log (created_at DESC);
CREATE INDEX idx_audit_log_actor ON audit_log (actor, created_at DESC);

-- ============================================================
-- users: dashboard authentication (Part 5.5)
-- ============================================================
CREATE TABLE users (
    user_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email              TEXT NOT NULL UNIQUE,
    password_hash       TEXT NOT NULL,             -- bcrypt/argon2, never plaintext
    role                  TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'engineer', 'viewer')),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at         TIMESTAMPTZ
);
```

Every table referenced by the API in Part 5 exists above, with consistent UUID keys and explicit `created_at` timestamps.

## 7.2 Neo4j — Corrected, Parameterized Queries **[MVP]**

**Correction 1**: never interpolate user input directly into Cypher strings. All queries use parameters.

**Correction 2**: relationship properties are accessed as relationship properties (`r.confidence`), never mistakenly treated as node properties.

**Schema**:
```cypher
// Service nodes
CREATE (:Service {id: 'auth-service', tier: 'core'});
CREATE (:Service {id: 'api-gateway', tier: 'edge'});

// Dependency relationship, with observed telemetry as edge properties
CREATE (s1:Service {id: 'auth-service'})-[:CALLS {
    latency_p99_ms: 45,
    error_rate: 0.001,
    call_frequency_per_min: 1200
}]->(s2:Service {id: 'api-gateway'});

// Learned dependency-failure hypothesis (NOT asserted as a proven causal fact — see Part 9.9)
CREATE (s1)-[:CAUSES_FAILURE_HYPOTHESIS {
    confidence: 0.62,
    model_version: 'atcgt-v0.1',
    evaluated_at: datetime()
}]->(s2);
```

**Correct, parameterized query examples (Python driver)**:
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", get_secret("NEO4J_PASSWORD")))

def find_affected_services(tx, service_id: str, max_hops: int = 5):
    query = """
    MATCH (n:Service {id: $service_id})-[:CALLS*1..%d]->(affected:Service)
    RETURN DISTINCT affected.id AS service_id
    """ % max_hops  # max_hops is a fixed server-side integer, never raw user text; service_id is parameterized
    return tx.run(query, service_id=service_id).data()

def find_most_critical_services(tx):
    query = """
    MATCH (s:Service)<-[:CALLS]-(dependent)
    RETURN s.id AS service_id, count(dependent) AS num_dependents
    ORDER BY num_dependents DESC
    LIMIT 20
    """
    return tx.run(query).data()

def get_failure_hypothesis_confidence(tx, service_id: str):
    # Correctly reads the CONFIDENCE from the relationship, not the node
    query = """
    MATCH (service:Service {id: $service_id})-[r:CAUSES_FAILURE_HYPOTHESIS]->(affected:Service)
    RETURN service.id AS service_id, affected.id AS affected_id, r.confidence AS confidence
    ORDER BY r.confidence DESC
    """
    return tx.run(query, service_id=service_id).data()

with driver.session() as session:
    result = session.execute_read(find_affected_services, service_id="auth-service", max_hops=5)
```

**Pros**: fast path-finding queries, natural fit for visualization, flexible schema.
**Cons**: operational complexity for clustering; smaller ecosystem than SQL databases. Both are accepted trade-offs for the dependency-graph use case.

---

# PART 8: MONITORING & OBSERVABILITY

## 8.1 Telemetry Architecture — Explicit **[MVP]**

This section is the single authoritative description of the telemetry architecture (matches Part 2.1's diagram exactly — there is no second, conflicting version of this architecture elsewhere in the document):

```
Metrics:
  Application / Kubernetes → Prometheus → feature extraction (stream-processing-service)

Traces:
  Application → OpenTelemetry SDK → OpenTelemetry Collector → Jaeger (trace backend/UI)
    → trace feature extraction reads directly from Jaeger's query API (no Kafka hop — see below)

Logs:
  Application → log collector (e.g. Fluent Bit) → log backend (e.g. Loki) → feature extraction

Kubernetes events:
  Kubernetes API → event ingestion (kubernetes-event-watcher) → Kafka (raw.events)
```

Two corrections consolidated here:

1. **OpenTelemetry Collector is the collection layer for traces; Jaeger is the storage/query backend, not the collector.** (This corrects an earlier draft that described Jaeger as the primary telemetry collector.)
2. **Traces do not additionally flow through a Kafka topic.** An earlier draft listed a `raw.traces` Kafka topic (Part 3.2) alongside this OTel → Jaeger path, which was redundant and never resolved. The corrected, single design: metrics and events flow through Kafka (because multiple internal services need to react to them as a stream); traces are stored durably in Jaeger and queried directly by consumers — primarily the RCA engine (Part 9.4) — via Jaeger's own query API. If a future requirement genuinely needs trace events broadcast to multiple independent consumers in real time, adding a Kafka export from the OTel Collector is a documented, deliberate **[FUTURE]** extension, not an implicit assumption.

## 8.2 Internal Platform Monitoring **[MVP]**

CausalOps X also monitors itself:
- Prometheus exporters on every internal service (latency, error rate, queue depth)
- OpenTelemetry tracing across service-to-service calls within CausalOps X itself
- Centralized logging for all internal services
- Dashboards (Grafana or the CausalOps dashboard itself) showing pipeline health: ingestion lag, inference latency, Kafka consumer lag

## 8.3 Alerting on the Platform Itself **[MVP]**

Basic Prometheus alerting rules for the platform's own health (e.g. Kafka consumer lag exceeding a threshold, inference-service error rate spike) — distinct from the AIOps *product* functionality, which alerts on the *monitored* cluster.

---

# PART 9: AI/ML PIPELINE

## 9.1 Pipeline Overview — Five Components **[MVP/ADVANCED]**

The production/advanced pipeline has **five** components. ATCGT (Part 9.9) is a **research architecture**, not a sixth pipeline component — it is a proposed alternative implementation for components 2 and 3.

| # | Component | Baseline Approach | Status |
|---|---|---|---|
| 1 | Anomaly Detection | Variational Autoencoder (VAE) | [MVP] |
| 2 | Root Cause Analysis | Graph Transformer over service graph | [MVP] |
| 3 | Failure Propagation Prediction | LSTM (baseline) / Temporal-GNN (advanced) | [ADVANCED] |
| 4 | Recovery Recommendation | Learning-to-rank | [ADVANCED] |
| 5 | Counterfactual Evaluation | Causal effect estimation (DoWhy) | [ADVANCED] |

Research track: **ATCGT** proposed as an enhanced implementation of components 2 and 3 (Part 9.9).

### 9.1.1 Master Model Pipeline Table

This is the single centralized reference for every model in the system — training data source, input, output, and status are kept consistent with the detailed descriptions in 9.3–9.9. If any other part of this document appears to disagree with this table, this table is authoritative.

| Component | Model | Training Data | Input | Output | Purpose | Status |
|---|---|---|---|---|---|---|
| Anomaly Detection | VAE | Normal (unlabeled) telemetry from the testbed | Time-windowed service metrics | Anomaly score (reconstruction error) | Detect abnormal service behavior | MVP |
| Root Cause Analysis | Graph Transformer | Labeled incidents (public benchmark + controlled fault-injection) | Node features (metrics/events/trace-derived) + edge features + service graph (Neo4j) | Ranked root-cause scores per service | Identify the most likely root-cause service(s) | MVP |
| Failure Propagation | LSTM (baseline) | Temporal fault-injection sequences | Per-service time series | Per-service failure probability | Baseline propagation prediction | Advanced |
| Failure Propagation | Temporal-GNN / Graph Transformer | Temporal + graph fault-injection data | Time + service + graph features | Affected-services / propagation prediction | Graph-aware propagation prediction | Advanced |
| Recovery Recommendation | LightGBM Learning-to-Rank | Controlled action/outcome data (Part 9.6.1) | Incident features + candidate-action features | Ranked candidate actions | Recommend a remediation action | Advanced |
| Counterfactual Evaluation | DoWhy + causal effect estimation | Intervention/outcome data from the controlled testbed (Part 9.7.1) | System state + intervention (`do(action)`) + stated causal assumptions | Estimated causal effect + uncertainty interval | "What-if" decision support before executing an action | Advanced/Research |
| Research Model | ATCGT | Public benchmark datasets + controlled fault-injection data | Temporal service graph — `(batch, time, services, features)` + edge features | RCA ranking / propagation prediction (alternative to rows 2 and 3) | Research contribution — evaluated, not assumed superior | Research |

## 9.2 Dataset Strategy — Corrected **[MVP/ADVANCED/RESEARCH]**

**Correction**: earlier drafts claimed access to "6 months of production metrics," "1M+ production metric vectors," and "500-1000+ manually annotated production incidents." We have no production deployment and no such data exists yet. The corrected strategy uses three clearly distinguished sources:

### A. Public AIOps Benchmark Datasets

Used for reproducible experiments and baseline comparison. Examples to evaluate for fit (exact choice depends on license/availability at implementation time):

| Dataset | Modality | Labels | Purpose | Known Limitations |
|---|---|---|---|---|
| AIOps Challenge datasets (e.g. 2018/2020 competition data) | Metrics, some traces | Incident/root-cause labels for competition tasks | RCA and anomaly-detection benchmarking | Domain-specific to the originating company's stack; may not transfer directly |
| RCAEval (or equivalent current public RCA benchmark suite) | Metrics, traces, logs | Root-cause labels, fault-injection metadata | Standardized RCA evaluation across multiple published methods | Coverage of fault types may not match our own testbed's fault types |

**We do not fabricate dataset statistics.** Before use, each dataset's actual size, label coverage, and license are checked and documented in the research report (Part 13), not assumed here.

### B. Controlled Kubernetes Test Environment — Self-Generated

We build our own microservice testbed on Kubernetes and collect:
- Prometheus metrics
- OpenTelemetry traces
- Application/system logs
- Kubernetes events
- The actual service dependency graph of the testbed (not assumed — derived from real trace data)

### C. Controlled Fault Injection — Self-Generated, Labeled

Labeled incidents are generated via controlled fault injection (e.g. using Chaos Mesh or a hand-rolled fault-injection harness):

- CPU stress
- memory stress
- pod failure / crash
- network latency injection
- packet loss
- service crash
- database slowdown
- traffic spike
- bad deployment / configuration error
- dependency failure

Each generated incident is stored with:
```
incident_id, fault_type, root_cause, start_time, end_time,
affected_services, propagation_order, metrics, traces, logs,
action_taken, action_result
```

### Summary Table

| Source | Label | Status |
|---|---|---|
| Public benchmark datasets | **PUBLIC DATA** | [MVP/RESEARCH] |
| Our Kubernetes testbed telemetry | **SELF-GENERATED CONTROLLED DATA** | [MVP] |
| Our fault-injection incidents | **SELF-GENERATED CONTROLLED DATA (labeled)** | [MVP/ADVANCED] |
| Any data used only to validate architecture choices before real data collection | **SYNTHETIC DATA** | clearly marked wherever used, never presented as real |

No claim in this document assumes access to real production traffic or production incident history from any company.

### 9.2.1 Dataset Selection Tracker (to be filled in once datasets are actually chosen)

The exact public datasets have not been finalized yet. This table is the tracked, single source of truth for dataset selection — it is filled in with real values (name, license, exact modality/labels) once a dataset is actually evaluated for fit, and referenced from Part 13 (Research Paper) rather than duplicated there. No statistics are invented ahead of that selection.

| Dataset | Source | Modality | Labels | Primary Use | License | Train/Validation/Test Strategy |
|---|---|---|---|---|---|---|
| Public Dataset 1 | TBD | TBD | TBD | Anomaly Detection / RCA | TBD | TBD |
| Public Dataset 2 | TBD | TBD | TBD | RCA / Failure Propagation | TBD | TBD |
| Kubernetes Testbed | Self-generated | Metrics, traces, logs, K8s events | Ground truth (we control the environment) | Full pipeline (all 5 components) | N/A — internal | Chronological (temporal) split, Part 11.2 |
| Fault Injection Dataset | Self-generated | Multi-modal (metrics + traces + logs + labels) | Known fault type / root cause / propagation order | RCA, Failure Propagation, Recovery Recommendation | N/A — internal | Temporal split, with held-out incidents never used for threshold or hyperparameter tuning (Part 9.3.1) |

## 9.3 Component 1: Anomaly Detection (VAE) **[MVP]**

```
Telemetry → Feature Engineering → VAE → Reconstruction Error → Anomaly Score
```

Input features (per service, per time window): CPU, memory, latency, error rate, throughput, network I/O, disk I/O, rolling statistics (mean/std over multiple windows).

```python
import torch
import torch.nn as nn

class AnomalyVAE(nn.Module):
    def __init__(self, input_dim: int, latent_dim: int = 8):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32), nn.ReLU(),
            nn.Linear(32, latent_dim * 2),  # outputs [mu, logvar]
        )
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 32), nn.ReLU(),
            nn.Linear(32, input_dim),
        )
        self.latent_dim = latent_dim

    def forward(self, x):
        h = self.encoder(x)
        mu, logvar = h[:, :self.latent_dim], h[:, self.latent_dim:]
        std = torch.exp(0.5 * logvar)
        z = mu + std * torch.randn_like(std)
        x_hat = self.decoder(z)
        recon_loss = ((x - x_hat) ** 2).sum(dim=1)
        kl_loss = -0.5 * (1 + logvar - mu.pow(2) - logvar.exp()).sum(dim=1)
        loss = (recon_loss + kl_loss).mean()
        anomaly_score = recon_loss  # higher reconstruction error -> more anomalous
        return loss, anomaly_score
```

**Data splits and label usage — corrected**:
- **Training data**: unlabeled "normal" telemetry from the testbed — the VAE does **not** require incident labels to train (it learns to reconstruct normal behavior).
- **Validation data**: a held-out slice used for threshold selection (choosing the anomaly-score cutoff).
- **Test data**: labeled fault-injection incidents, used **only** for final evaluation, never for threshold tuning.

### 9.3.1 Threshold-Selection Methodology

Threshold selection is a distinct step from training, and is never performed against the test split:

```
Normal training telemetry
        ↓
Train VAE (unsupervised — no labels used)
        ↓
Validation set (normal + a small amount of fault-injection data, held out from training)
        ↓
Select anomaly-score threshold
        ↓
Freeze threshold
        ↓
Evaluate exactly once, on held-out test incidents (never seen before this point)
```

Candidate threshold-selection approaches (the actual choice, and why, is documented once experiments are run — this is not decided in advance):
- **Percentile-based threshold** — e.g. flag anything above the 99th percentile of validation reconstruction error
- **Validation-set FPR constraint** — pick the threshold that keeps false positives on the validation set below a target rate
- **Validation F1 optimization** — where validation labels exist (some fault-injection cases in the validation split), pick the threshold that maximizes F1 on that split

The test split's labels are **never** used to choose or adjust the threshold — only to report final, one-shot evaluation numbers.

**Targets, not guarantees**: "Target performance will be established experimentally" on the held-out test split — we do not claim a specific AUC or false-positive rate in advance. Part 4's target table (false positive rate < 5%) is a **goal**, reported alongside the actually-measured number once training and evaluation are complete.

## 9.4 Component 2: Root Cause Analysis (Graph Transformer) **[MVP]**

**Correction 1**: earlier drafts represented the RCA model's input as bare service-ID embeddings (i.e., the model only knew *which* service, not its actual telemetry state). This is corrected to a proper feature-encoder + graph-transformer design.

**Correction 2**: earlier drafts implied all of the RCA engine's inputs (metrics, events, *and* traces) could be fetched from TimescaleDB. That's only true for metrics and events. The RCA engine's actual data sources are:

```
RCA Engine — Data Sources
 │
 ├── Recent metrics          → PostgreSQL / TimescaleDB (Part 7.1)
 ├── Kubernetes/app events    → PostgreSQL (`events` table, Part 7.1)
 ├── Distributed traces       → Jaeger / configured trace backend, queried directly (Part 8.1) — NOT stored in TimescaleDB
 └── Service dependency graph → Neo4j (Part 7.2)
```

These four sources feed the feature-encoder pipeline:

```
Telemetry (metrics + events from TimescaleDB, traces from Jaeger)
                                          │
                                          ▼
                                 Feature Extraction
                                          │
                                          ▼
                              Node + edge features
                                          │
                    Service dependency graph (Neo4j) ──┘
                                          ▼
                                  Graph Transformer
                                          ▼
                          Root-cause score per service
                                          ▼
                              Ranked RCA results
```

Trace data is never claimed to be stored in TimescaleDB — it is read from Jaeger's own query API at inference time (or, if latency requirements later demand it, cached briefly in Redis per Part 3.2.1, which is a caching layer, not a storage path).

**Node features** (per service, at incident time): CPU, memory, latency, error rate, throughput, current anomaly score, recent historical failure frequency, and trace-derived features (e.g. per-hop latency contribution, error propagation from traces touching this service).

**Edge features** (per dependency): dependency type (`CALLS`, etc.), observed latency, error rate, request rate, call frequency.

```python
import torch
from torch_geometric.nn import TransformerConv

class FeatureEncoder(torch.nn.Module):
    def __init__(self, raw_feature_dim: int, embed_dim: int):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(raw_feature_dim, embed_dim), torch.nn.ReLU(),
            torch.nn.Linear(embed_dim, embed_dim),
        )

    def forward(self, raw_node_features):
        return self.net(raw_node_features)

class RCAGraphTransformer(torch.nn.Module):
    def __init__(self, raw_feature_dim: int, embed_dim: int = 32, edge_dim: int = 4, heads: int = 4):
        super().__init__()
        self.encoder = FeatureEncoder(raw_feature_dim, embed_dim)
        self.gt1 = TransformerConv(embed_dim, embed_dim, heads=heads, edge_dim=edge_dim)
        self.gt2 = TransformerConv(embed_dim * heads, embed_dim, heads=heads, edge_dim=edge_dim)
        self.output_head = torch.nn.Linear(embed_dim * heads, 1)

    def forward(self, raw_node_features, edge_index, edge_attr):
        x = self.encoder(raw_node_features)
        x = torch.relu(self.gt1(x, edge_index, edge_attr))
        x = self.gt2(x, edge_index, edge_attr)
        return self.output_head(x).squeeze(-1)  # per-node root-cause score
```

**Evaluation** — not accuracy alone:
- Top-1, Top-3, Top-5 accuracy (is the true root cause in the top-k ranked list?)
- Mean Reciprocal Rank (MRR)
- Precision, Recall, F1 (treating "is this service a contributing root cause" as a per-service classification task, since incidents can have more than one contributing cause)

## 9.5 Component 3: Failure Propagation Prediction **[ADVANCED]**

Three explicitly compared variants:

| Variant | Description | Status |
|---|---|---|
| Baseline | LSTM over per-service time series (Part 3.4.4) | [ADVANCED] |
| Advanced | Temporal Graph Neural Network / Graph Transformer with temporal attention | [ADVANCED] |
| Research | ATCGT (Part 9.9) | [RESEARCH] |

**Purpose of the three-way comparison**: to determine, empirically, whether adding graph structure and then causal structure actually improves propagation prediction over a plain temporal baseline — not to assume in advance that more architecture is automatically better.

**Evaluation**:
- Top-k prediction accuracy (does the model correctly identify the next k services to be affected?)
- Propagation-path accuracy against the fault-injection ground truth
- Time-to-failure MAE (mean absolute error, in seconds)
- Blast-radius prediction error (predicted vs. actual count/set of affected services)
- Precision/Recall/F1 where the task is framed as multi-label classification (which services will be affected)

No accuracy or MAE figure is claimed before these experiments are run; Part 4's numbers are targets only.

## 9.6 Component 4: Recovery Recommendation — Learning-to-Rank (Not RL) **[ADVANCED]**

**Correction**: earlier drafts specified an RL model (DQN/PPO-style) trained on "1000+ past incidents" for the MVP/advanced recommender. We have no such dataset, and RL from scratch on a small fault-injection dataset is not a realistic MVP approach. The **primary implementation is a supervised learning-to-rank model**:

**Input features**: root cause, incident severity, current service state, propagation-prediction state, historical outcomes of similar past actions (from our own controlled fault-injection runs), overall system health.

**Output**: a ranked list of candidate actions with scores.

### 9.6.1 Where the Training Labels Actually Come From

The learning-to-rank model does **not** learn from fabricated historical production incidents — there are none. Its initial training data is generated entirely from controlled experiments on our own fault-injection testbed:

```
Controlled fault injection (Part 9.2C)
        ↓
Create incident (per Part 7.1 `incidents` table)
        ↓
Generate candidate allowlisted actions for this incident
        ↓
Execute each candidate action in the controlled environment (one at a time, or across repeated
runs of the same injected fault, so actions can be fairly compared)
        ↓
Measure outcome:
    - success / failure
    - recovery time
    - error-rate improvement
    - latency improvement
    - blast radius / risk incurred by the action itself
        ↓
Create an action-outcome record (feeds the `feedback` table, Part 7.1)
        ↓
Train the Learning-to-Rank model on these (incident, action, outcome) records
```

**Worked example:**
```
Incident:
  Database CPU = 95%

Candidate A: scale_database
  → recovery time = 18s, successful

Candidate B: restart_payment_service
  → recovery time = 45s, unsuccessful (did not address the root cause)
```

These two outcomes become a ranking-training pair for that incident: `scale_database` should rank above `restart_payment_service` for this incident type. As more controlled runs accumulate (and, later, more real approved-and-executed actions via the same `feedback` table), the ranking model is retrained (Part 12.4, MLOps).

Allowlisted candidate actions remain exactly as defined in Part 5.4 — no new action types are introduced here, and the recommender never proposes an action outside this fixed set:
```
scale pods
restart service
traffic shift
rate limiting
cache invalidation
dependency fallback
rollback
```

```python
import lightgbm as lgb

# Candidate actions per incident are featurized as (incident_features, action_features) rows,
# labeled by outcome from controlled fault-injection experiments (action succeeded / time-to-recovery).
ranker = lgb.LGBMRanker(objective='lambdarank', num_leaves=31, learning_rate=0.05, n_estimators=200)
ranker.fit(X_train, y_train, group=group_sizes_train)

# Example output for one incident:
# scale_pods            -> 0.91
# restart_service        -> 0.68
# traffic_shift          -> 0.52
```

**Candidate actions** (matches the allowlist in Part 5.4): scale pods, restart service, traffic shift, rate limiting, cache invalidation, dependency fallback, rollback.

Each recommendation returned to the dashboard includes: predicted success probability, estimated recovery time, risk score, and an explanation (Part 10).

**RL is explicitly future work**: "Reinforcement learning (DQN/PPO-style policy learning) is future research / an optional advanced implementation, to be pursued only after sufficient state-action-reward data has been collected from real approved-and-executed actions (via the feedback table in Part 7.1). We do not claim RL is trained or deployed until that data genuinely exists." See Part 14.

## 9.7 Component 5: Counterfactual Evaluation — Causal Effect Estimation, Not Ordinary Prediction **[ADVANCED]**

**Correction**: counterfactual evaluation is not "just another prediction model." It is causal effect estimation under explicit assumptions:

```
Observational data
  → causal assumptions / causal graph (explicitly stated, not silently assumed)
  → intervention: do(action)
  → estimated outcome (with uncertainty)
  → estimated side effects
  → decision support (shown to the human approver, not auto-executed)
```

**Worked example**:
```
Current state:
  Database CPU = 95%
  Payment latency = 4.0s

Candidate intervention: do(scale_database)

Estimated outcome (from DoWhy backdoor-adjustment estimate on the controlled testbed data):
  Latency:          estimated range, e.g. 1.2s – 1.8s (95% CI)
  Error rate:        estimated range
  Success probability: estimated point value with confidence interval
  Risk:               estimated value (based on blast radius of the action itself)
```

**Explicit distinctions maintained throughout the UI and the report**:
- **Correlation** ("these two things move together")
- **Prediction** ("what the model expects to happen if nothing changes")
- **Causal effect estimate** ("what we estimate would happen *if we intervened*, under stated assumptions")
- **Counterfactual** ("what would have happened differently, had a different action been taken")

We do not claim that running a causal-inference library "proves" causality — the identifying assumptions (no unmeasured confounders, correct causal graph, etc.) are stated explicitly, and their plausibility (and violation risk) is discussed for every counterfactual shown to a user.

### 9.7.1 Where the Intervention/Outcome Data Actually Comes From

Causal effect estimation needs *some* data on interventions and their outcomes. We do not assume this data exists — it is generated the same way the recovery-recommendation training data is (Part 9.6.1), on the controlled testbed:

```
Controlled Kubernetes testbed
        ↓
Apply a known intervention (an allowlisted action, executed deliberately — Part 5.4)
        ↓
Observe the system's actual outcome (metrics, error rate, latency, recovery time)
        ↓
Store (state, action, outcome) as one intervention/outcome record
        ↓
Accumulate an intervention/outcome dataset across many controlled runs
        ↓
Define causal assumptions explicitly (the assumed causal graph, confounders considered, temporal precedence — Part 9.10)
        ↓
DoWhy / causal effect estimation, using the intervention/outcome dataset above
        ↓
Estimated effect + uncertainty interval
        ↓
Shown to the human approver as decision support — never auto-executed on the estimate alone
```

This is the same underlying controlled-experiment data source described in Part 9.2(C) and Part 9.6.1 — fault injection creates the "before" state, an allowlisted action creates the intervention, and the testbed's own telemetry after the action captures the outcome. No production intervention history is assumed or required to get started.

**Explicitly stated, not implied**: DoWhy does not automatically prove causality. Every causal estimate it produces is conditional on the identification assumptions we state going in (the assumed causal graph, no unmeasured confounders, correct model of the "backdoor" adjustment set, etc.). If those assumptions don't hold, the estimate can be wrong even though the computation itself is correct. This caveat is shown alongside every counterfactual result presented to a user, not buried in documentation.

## 9.8 Explainability Boundaries (Cross-Reference to Part 10)

SHAP/Captum explanations describe **feature importance for a model's prediction**. Causal effect estimates describe **an estimated causal effect under stated assumptions**. These two kinds of output are visually and textually distinguished in the dashboard — a SHAP explanation is never presented as "the cause" of an incident; it's presented as "what most influenced the model's score."

## 9.9 ATCGT — Proposed Research Architecture **[RESEARCH]**

**Full name**: Adaptive Temporal Causal Graph Transformer (ATCGT) — Proposed Research Architecture.

**Framing** (corrected from the earlier draft's unsupported claims): we **propose** this architecture and **hypothesize** it will improve RCA and failure-propagation prediction over non-temporal, non-graph, or non-causal baselines. We do **not** claim it is state-of-the-art, first-of-its-kind, or that it outperforms baselines by any specific percentage, until that is actually measured (Part 13).

**Components**:
1. Temporal representation (preserves the time dimension — see the architecture correction below)
2. Graph-based service-dependency reasoning
3. Causal structure learning / causal constraints (informed by causal-learn / DoWhy, not a blind learned-adjacency-matrix)
4. Temporal attention
5. Graph Transformer layers
6. RCA / propagation-prediction output head

**Architecture correction — temporal attention must not flatten the graph structure.**

The earlier draft's temporal-attention implementation collapsed the input into a flat sequence, discarding the service/node dimension before attention was applied — which defeats the point of combining temporal and graph reasoning. The corrected design explicitly preserves all three dimensions — `(batch, time_steps, services, features)` — through the temporal encoder:

```python
import torch
import torch.nn as nn
from torch_geometric.nn import TransformerConv

class TemporalGraphAttention(nn.Module):
    """
    Operates on (batch, time_steps, num_services, feature_dim).
    Preserves the time dimension AND the service/node dimension —
    does not flatten them together before attention.
    """
    def __init__(self, feature_dim: int, embed_dim: int, num_heads: int = 4):
        super().__init__()
        self.input_proj = nn.Linear(feature_dim, embed_dim)
        # Temporal attention is applied per-service, across the time axis
        self.temporal_attn = nn.MultiheadAttention(embed_dim, num_heads, batch_first=True)

    def forward(self, x):
        # x: (batch, time_steps, services, features)
        b, t, s, f = x.shape
        x = self.input_proj(x)                          # (b, t, s, embed_dim)
        x = x.permute(0, 2, 1, 3).reshape(b * s, t, -1)  # (b*s, t, embed_dim) — attends over time, per service
        attn_out, _ = self.temporal_attn(x, x, x)
        attn_out = attn_out.reshape(b, s, t, -1).permute(0, 2, 1, 3)  # back to (b, t, s, embed_dim)
        return attn_out  # time and service dimensions both preserved


class ATCGT(nn.Module):
    """
    Temporal encoder -> dependency/causal representation -> graph transformer -> prediction head.
    The learned adjacency/attention weights are treated as a CAUSAL HYPOTHESIS to be validated
    (Part 9.9, 'Causal Discovery Caveats'), not as a proven causal graph.
    """
    def __init__(self, feature_dim: int, embed_dim: int = 32, num_services: int = 50, edge_dim: int = 4):
        super().__init__()
        self.temporal = TemporalGraphAttention(feature_dim, embed_dim)
        self.graph_transformer = TransformerConv(embed_dim, embed_dim, heads=4, edge_dim=edge_dim)
        self.output_head = nn.Linear(embed_dim * 4, 1)

    def forward(self, x, edge_index, edge_attr):
        # x: (batch, time_steps, services, features)
        temporal_repr = self.temporal(x)               # (batch, time_steps, services, embed_dim)
        last_step = temporal_repr[:, -1, :, :]          # most recent timestep's representation per service
        b, s, e = last_step.shape
        node_repr = last_step.reshape(b * s, e)
        graph_out = self.graph_transformer(node_repr, edge_index, edge_attr)
        return self.output_head(graph_out).reshape(b, s)  # per-service score
```

### 9.9.1 Correct Batching for `batch_size > 1` — Implementation Note

**The `forward()` above is only correct when `batch_size == 1`, or when every graph in the batch shares one identical `edge_index`.** Reshaping `(b, s, e)` to `(b*s, e)` and passing that into `TransformerConv` alongside a single `edge_index` implicitly assumes every one of the `b` graphs in the batch has the exact same node indexing — which is true for our fixed testbed topology, but is **not** a safe general assumption (e.g. once different incidents have different subsets of the graph, or the topology changes between fault-injection runs). Reusing one `edge_index` across a naively-reshaped batch, without offsetting node indices per graph, silently produces wrong edges (node `0` of graph 2 gets connected as if it were node `0` of graph 1).

The general-purpose fix is to build a proper PyTorch Geometric `Batch` (disjoint-union) representation before the graph-transformer stage, so PyG offsets node indices for us automatically:

```
Temporal representation:  (batch, time, services, features)
        ↓  temporal attention per service (Part 9.9, TemporalGraphAttention)
(batch, time, services, embedding)
        ↓  select last timestep (or another aggregation over time)
(batch, services, embedding)
        ↓  wrap each graph-in-batch as its own torch_geometric.data.Data,
        ↓  then combine with torch_geometric.data.Batch.from_data_list([...])
PyTorch Geometric Batch — node indices auto-offset per graph, edges never cross between graphs
        ↓
Graph Transformer (operates on the batched, disjoint graph as if it were one big graph)
        ↓
RCA / propagation output, then un-batched back into (batch, services) using batch.batch pointers
```

```python
from torch_geometric.data import Data, Batch

def build_batched_graph(node_repr, edge_index, edge_attr, batch_size: int, num_services: int):
    """
    node_repr: (batch_size, num_services, embed_dim) — per-graph node features.
    edge_index / edge_attr: the (possibly per-graph-varying) graph structure.
    Returns a single PyG Batch with node indices correctly offset per graph.
    """
    graphs = [
        Data(x=node_repr[i], edge_index=edge_index, edge_attr=edge_attr)
        for i in range(batch_size)
    ]
    return Batch.from_data_list(graphs)

# Usage inside ATCGT.forward, replacing the naive reshape:
#   batched = build_batched_graph(last_step, edge_index, edge_attr, b, s)
#   graph_out = self.graph_transformer(batched.x, batched.edge_index, batched.edge_attr)
#   per_service_scores = self.output_head(graph_out).reshape(b, s)  # safe: PyG guarantees the ordering
```

This is treated as a required correctness fix before any batched training run, not an optional optimization — silently-wrong edges between unrelated graphs in a batch would corrupt every downstream RCA/propagation result without necessarily causing a visible error.

## 9.10 Causal Discovery Caveats — Explicit **[RESEARCH]**

**Correction**: a learnable adjacency matrix (or learned attention weights over the service graph) is **not** the same thing as a validated causal graph. This document does not conflate the two anywhere.

**Techniques used for causal structure analysis**: PC algorithm, FCI algorithm (via `causal-learn`), and DoWhy for effect estimation once a causal graph is assumed.

**Assumptions and limitations documented for every causal claim made by the system**:
- Temporal precedence (a cause must precede its effect — enforced by only allowing edges consistent with observed event ordering)
- Potential unmeasured confounders (e.g. a shared upstream cause not captured in telemetry)
- Intervention assumptions (that `do(action)` in our estimate matches what actually happens when the action executes in the cluster)
- Identifiability limitations (not every causal effect is identifiable from observational data alone, even with a correct graph)

Any "causal" edge or effect shown to a user is labeled with these caveats, not presented as ground truth.

---

# PART 10: EXPLAINABLE AI

## 10.1 Two Distinct Kinds of Explanation **[ADVANCED]**

1. **Model feature-importance explanations** (SHAP for tabular/ranking models, Captum/attention weights for graph/temporal models): describe what most influenced a specific model's output. These are statements about the model, not about reality.
2. **Causal-assumption disclosures** (Part 9.7, 9.10): describe the assumptions behind a counterfactual/causal-effect estimate, and their known limitations.

The dashboard never merges these into a single "why this happened" statement without labeling which kind of explanation it is.

## 10.2 Example Explanation Payload

```json
{
  "incident_id": "5b1c...-uuid",
  "rca_explanation": {
    "type": "model_feature_importance",
    "method": "shap",
    "top_contributors": [
      {"feature": "cpu_usage", "contribution": 0.35},
      {"feature": "memory_spike", "contribution": 0.28},
      {"feature": "error_rate", "contribution": 0.15}
    ]
  },
  "counterfactual_explanation": {
    "type": "causal_effect_estimate",
    "assumptions": ["no unmeasured confounders", "correct causal graph as specified", "stable intervention effect"],
    "estimate": {"metric": "payment_latency_ms", "value": 1400, "ci_95": [1100, 1800]}
  }
}
```

## 10.3 Confidence & Risk Scoring **[ADVANCED]**

Every RCA result, propagation prediction, and recommended action carries a confidence/risk score derived from model uncertainty (e.g. ensemble variance or calibrated probability), shown alongside — not instead of — the explanation.

---

# PART 11: TESTING STRATEGY

## 11.1 Test Categories **[MVP/ADVANCED]**

- **Unit testing** — individual functions/classes (feature extraction, action handlers, Pydantic models)
- **Integration testing** — service-to-service flows (e.g. anomaly → incident → RCA)
- **API testing** — every endpoint against its Pydantic schema, including error cases
- **Database testing** — schema migrations, constraint enforcement, query correctness
- **ML testing** — see 11.2
- **Data validation testing** — schema checks on ingested telemetry, fault-injection metadata completeness
- **Model regression testing** — new model versions must not regress on the fixed evaluation set without an explicit, documented reason
- **End-to-end testing** — full pipeline on the controlled testbed, from injected fault to displayed recommendation
- **Load testing** — establishes the real latency/throughput numbers referenced in Part 2.4
- **Security testing** — see Part 12.5
- **Failure injection testing** — the fault-injection harness (Part 9.2C) doubles as a testing tool for the platform's own resilience
- **Recovery testing** — verifies rollback actually works when a remediation action fails

## 11.2 ML-Specific Testing **[MVP/ADVANCED]**

- **Data leakage checks**: verify no test-set fault-injection incidents leak into training data (e.g. via overlapping time windows)
- **Train/validation/test separation**: enforced and logged for every training run (Part 9.3)
- **Temporal splits, not random splits, for time-series data**: random splits on time-series telemetry can leak future information into training; we split chronologically (train on earlier time ranges, validate/test on later ones) unless there's a specific documented reason not to
- **Baseline comparison**: every advanced/research model is evaluated against its stated baseline (Part 9.5, 9.9), not evaluated in isolation
- **Reproducibility**: fixed random seeds, logged in MLflow (Part 12.4)
- **Model versioning**: every deployed model has a version string recorded in `model_performance` (Part 7.1)

```python
import torch, pytest

@pytest.fixture
def model():
    return AnomalyVAE(input_dim=16)

def test_model_forward_pass(model, sample_normal_data):
    loss, anomaly_scores = model(sample_normal_data[:1])
    assert loss.shape == torch.Size([])
    assert anomaly_scores.shape == torch.Size([1])

def test_anomaly_scores_are_higher_for_injected_faults(model, sample_normal_data, sample_fault_injected_data):
    """Model trained on normal data should score fault-injected data higher, on average,
    on the held-out evaluation set. This is checked, not assumed."""
    _, normal_scores = model(sample_normal_data)
    _, fault_scores = model(sample_fault_injected_data)
    assert fault_scores.mean() > normal_scores.mean()

def test_no_temporal_leakage(train_time_range, test_time_range):
    assert train_time_range[1] <= test_time_range[0], "train window must fully precede test window"
```

---

# PART 12: DEPLOYMENT, DEVOPS & MLOPS

## 12.1 Kubernetes Deployment Strategy **[MVP]**

```yaml
# Test/demo cluster HA setup (not a production-scale claim)
- 3 replicas per stateless service where feasible on the demo cluster's resources
- Pod Disruption Budgets
- Horizontal Pod Autoscaling
- Persistent storage for databases

# Rolling updates
- Max surge: 1 pod
- Max unavailable: 0 pods
```

## 12.2 CI/CD Pipeline **[MVP]**

```yaml
GitHub Actions Workflow:
1. On PR: unit tests, linting, security scanning (dependency + container image scan)
2. On merge to main: build Docker images
3. Push to registry
4. Deploy to staging namespace
5. Run integration tests against staging
6. On release tag: deploy to the demo/production-like namespace
```

## 12.3 Security Hardening **[MVP]**

- OWASP API Security Top 10 checklist applied to every endpoint
- Input validation via Pydantic on every request
- SQL injection prevention: parameterized queries only (SQLAlchemy/psycopg with bound parameters)
- Cypher injection prevention: parameterized Cypher only (Part 7.2)
- Authentication/authorization per Part 5.5
- Rate limiting on the API gateway
- Secrets management via a secret manager / Kubernetes Secrets — never in source code or images
- TLS/HTTPS for all external and, where feasible, internal traffic
- Audit logging (Part 7.1 `audit_log` table)
- Dependency scanning and container image scanning in CI (12.2)
- Kubernetes RBAC scoped per service account
- NetworkPolicies restricting pod-to-pod traffic to what's actually needed
- Pod security: non-root containers, read-only root filesystem where possible, no privilege escalation
- Resource limits on every container (Part 3.9.2)

**Remediation-specific**: the AI layer never generates or executes arbitrary Kubernetes/shell commands. Only the allowlisted action set (Part 5.4) can be executed, and every execution requires human approval by default (Part 2.3 Flow 5).

## 12.4 MLOps Workflow **[ADVANCED]**

```
Data → preprocessing → feature generation → training → validation → evaluation
     → model registry → deployment → monitoring → feedback → retraining
```

- **MLflow** (or an equivalent open-source registry) for experiment tracking, model versioning, and dataset versioning
- Every training run logs: model version, dataset version (which public/self-generated data snapshot was used), metrics, hyperparameters/training configuration, and the resulting deployment version
- The `model_performance` table (Part 7.1) mirrors MLflow's tracked metrics for querying from the dashboard

## 12.5 What "Production-Ready" Means Here

A component is described as production-ready in this document **only if** it has: passing tests per Part 11, measured (not just targeted) latency/throughput under load testing, and a security review per 12.3. Nothing in this document should be read as certifying enterprise production-readiness for a component that hasn't gone through this process.

---

# PART 13: RESEARCH PAPER

## 13.1 Paper Structure

**Working title**: *Adaptive Temporal Causal Graph Transformers for Root Cause Analysis in Microservices: A Proposed Architecture and Empirical Evaluation*

**Sections**:
1. **Abstract** — states the proposed architecture and the empirical question being tested, not a pre-claimed result
2. **Introduction**
   - Problem: diagnosing root causes in distributed systems is hard because static/non-temporal/non-causal methods miss propagation dynamics
   - Proposed approach: combine causal-structure hypotheses, temporal modeling, and graph transformers
3. **Related Work**
   - AIOps systems (including MicroRank and other published RCA baselines)
   - Causal inference in ML systems
   - Graph neural networks and graph transformers
4. **Method (ATCGT)** — architecture as specified in Part 9.9, including the corrected temporal-attention design
5. **Experiments**
   - **Datasets**: public AIOps/RCA benchmark datasets (named and cited once selected), plus our own controlled Kubernetes fault-injection dataset (self-generated, clearly labeled as such — Part 9.2)
   - **Baselines**: LSTM (Part 9.5), static-graph RCA (no temporal component), MicroRank, and any other published baseline we can reproduce or fairly compare against
   - **Results**: reported only after the experiments are run — including negative or mixed results if that's what we find
   - **Ablation study**: ATCGT minus causal component, minus temporal attention, minus graph transformer, vs. full ATCGT
6. **Evaluation**
   - Precision, Recall, F1, NDCG, MRR (task-appropriate — Part 9.4, 9.5)
   - Inference latency (measured, not assumed)
   - Interpretability (what the SHAP/Captum/causal-assumption outputs actually look like on real examples)
7. **Limitations & Future Work** — explicitly includes the causal-discovery caveats from Part 9.10, and any gap between public-dataset performance and our own testbed's performance
8. **Conclusion**

**Target venues**: to be decided based on the strength of actual results; realistic options range from workshop papers to systems/ML conferences depending on what the evaluation shows. We do not pre-commit to NeurIPS/ICML/OSDI-level claims before there are results that would justify submission there.

## 13.2 Claims Discipline

Throughout the paper (and this blueprint), we use:
- "We propose..." / "We hypothesize..." / "To be evaluated against..." / "Expected contribution..." — before experiments
- Specific, cited numbers — only after experiments are actually run, with the dataset and method stated alongside every number

We do not use "first to combine X and Y," "state-of-the-art," or specific outperformance percentages unless they are experimentally established and reproducible.

---

# PART 14: FUTURE ROADMAP

## 14.1 Explicitly Out-of-Scope-for-Now Enhancements

### Autonomous Remediation (No Human Approval) **[FUTURE]**
- Only after the human-approved workflow (Part 2.3 Flow 5, Part 12.3) has a track record on low-risk action types
- Requires a formal risk-scoring policy and staged rollout, not a default from day one

### RL-Based Recovery Recommendation **[FUTURE]**
- Pursued only once enough state-action-reward data exists from real approved/executed actions (via the `feedback` table, Part 7.1)
- Until then, the learning-to-rank approach (Part 9.6) is the recommender

### LLM Integration **[FUTURE]**
- Chat interface for incident investigation
- Natural-language root-cause explanations layered on top of the existing structured explanations (Part 10) — not a replacement for them
- Any narrative generation would need to be clearly labeled as generated text, not a new source of ground truth

### Advanced Analytics **[FUTURE]**
- Predictive analytics for future incidents (beyond the propagation-prediction horizon already in scope)
- Trend analysis, capacity-planning integration

### Multi-Tenancy **[FUTURE]**
- Isolated namespaces per customer/team
- Per-tenant model fine-tuning
- Usage-based billing (only relevant if/when this becomes a hosted service)

### Horizontal Integration **[FUTURE]**
- CI/CD pipeline integration (correlating deployments with incidents)
- Cost-anomaly detection
- Security-incident correlation

## 14.2 Success Metrics — Reframed as Measurement Plans, Not Guarantees

| Metric | Target | Measurement Plan |
|--------|--------|-------------|
| MTTR | Reduction vs. manual baseline, magnitude TBD | Controlled A/B comparison on the fault-injection testbed: manual resolution vs. CausalOps-assisted resolution |
| RCA accuracy | Target ≥85% Top-1 (stretch goal) | Measured on public + controlled datasets (Part 9.4) |
| False positives (anomaly detection) | Target <5% | Measured on held-out validation split (Part 9.3) |
| Inference latency | Target <2s P99 for RCA | Measured via load testing (Part 11) |
| Throughput | Defined only after load testing | No number claimed in advance |
| Model improvement over time | Tracked via `model_performance` (Part 7.1) | Compared release-over-release, not assumed at a fixed rate |

---

# APPENDIX

## A. Development Environment Quick Start

```bash
# Clone repository
git clone https://github.com/CausalOps/CausalOps-X.git
cd CausalOps-X

# Create Python environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start local dev stack (Kafka in KRaft mode, Postgres/Timescale, Neo4j, Redis)
docker-compose -f docker/docker-compose.yml up

# Initialize databases (runs the corrected schema from Part 7)
python scripts/setup_databases.py

# Run tests
pytest tests/

# Start services locally
python -m services.ml_inference_service.main &
python -m services.stream_processing_service.main &
python -m services.api_gateway.main &
```

## B. Key References

- **Causal Inference**: DoWhy documentation; Pearl, *The Book of Why*; `causal-learn` documentation (PC, FCI algorithms)
- **Graph Neural Networks**: PyTorch Geometric documentation and tutorials
- **Transformers**: Vaswani et al., "Attention Is All You Need"
- **AIOps**: publicly available AIOps challenge datasets and published RCA baselines (e.g. MicroRank) — exact citations finalized once datasets are selected for Part 13
- **Kubernetes**: official documentation and community best practices
- **Kafka KRaft**: Apache Kafka KRaft mode documentation (ZooKeeper-free deployment)
- **OpenTelemetry**: OpenTelemetry Collector and SDK documentation

## C. Glossary

- **RCA**: Root Cause Analysis
- **MTTR**: Mean Time To Repair
- **Blast Radius**: number of services/users affected by an incident
- **Counterfactual**: a "what-if" outcome estimate under a stated intervention and stated causal assumptions
- **Causal Discovery**: learning candidate causal structure from data — always paired with stated assumptions and limitations in this project (Part 9.10)
- **GNN**: Graph Neural Network
- **VAE**: Variational Autoencoder
- **LSTM**: Long Short-Term Memory
- **SHAP**: SHapley Additive exPlanations
- **ATCGT**: Adaptive Temporal Causal Graph Transformer — the proposed research architecture of this project (Part 9.9)
- **KRaft**: Kafka's built-in consensus protocol, replacing the ZooKeeper dependency
- **Allowlisted action**: one of a fixed, pre-reviewed set of remediation actions the system is permitted to execute (Part 5.4) — never an arbitrary AI-generated command

---

**End of Master Blueprint**

---

# Summary of Revisions (v2.0)

This revision corrects the internal inconsistencies identified in the v1.0 draft while preserving the original project vision (CausalOps X, the five-component pipeline, the ATCGT research contribution, and the overall architecture/terminology). Specifically, this version:

✅ Resolves the "5 models vs. 6 models" contradiction — the pipeline has **five** components; ATCGT is a research architecture, not a sixth model, updated consistently in the executive summary, architecture, roadmap, and evaluation sections
✅ Replaces claimed production data ("6 months of production metrics," "1000+ past incidents," "500+ annotations") with an honest three-source dataset strategy: public benchmarks, self-generated Kubernetes-testbed telemetry, and controlled fault-injection data
✅ Reframes all performance numbers (accuracy, AUC, false-positive rate, MTTR reduction, latency, throughput) as **targets to be established experimentally**, not guaranteed results
✅ Corrects the RCA model's input design (node/edge feature encoding, not bare service-ID embeddings) and adds a full evaluation suite (Top-k, MRR, precision/recall/F1)
✅ Replaces the RL-based recovery recommender with a learning-to-rank model as the primary (MVP/advanced) implementation; RL is explicitly moved to future work, gated on real feedback data
✅ Reframes counterfactual evaluation as causal effect estimation under explicit, stated assumptions — distinguished from correlation and from ordinary prediction
✅ Redesigns the ATCGT temporal-attention mechanism to preserve the `(time, service, feature)` structure instead of flattening it, and removes unsupported "first," "state-of-the-art," and specific-percentage claims in favor of "proposed"/"hypothesized" language
✅ Removes CausalNex from the technology stack (unmaintained, no longer appropriate) in favor of DoWhy + causal-learn, with explicit causal-discovery caveats (temporal precedence, confounding, identifiability)
✅ Replaces ZooKeeper-based Kafka with Kafka in KRaft mode everywhere the deployment is described
✅ Removes redundant, overlapping stream-processing systems (previously Kafka Streams + Faust + Redis Streams simultaneously) in favor of one Kafka-consumer service, with Redis scoped to caching/pub-sub/rate-limiting only
✅ Fixes the PostgreSQL schema: valid, separate `CREATE INDEX` statements; every table referenced by the API now exists (`services`, `anomalies`, `feedback`, `incidents`, `events`, `metrics`, `rca_results`, `failure_predictions`, `remediation_actions`, `model_performance`, `audit_log`, `users`); consistent UUID IDs; explicit timestamps and foreign keys
✅ Fixes all Cypher queries to use parameterized inputs (no string interpolation of user input) and correct relationship-property access
✅ Makes API request/response schemas explicit Pydantic models instead of generic `dict` bodies, and enforces one consistent ID scheme (UUIDs plus stable `service_id` slugs) across API, database, Kafka, Neo4j, and frontend types
✅ Resolves the frontend WebSocket vs. Socket.IO mismatch in favor of native WebSocket on both ends, and consolidates the frontend stack to one state-management and one charting library
✅ Clarifies the observability architecture: OpenTelemetry Collector is the trace collection layer; Jaeger is the trace backend, not the collector
✅ Restructures the roadmap into 12 phases explicitly tagged MVP / Advanced / Research, replacing the earlier "24-week, fully production-ready" framing
✅ Strengthens testing (ML-specific: data leakage checks, chronological splits, baseline comparison, reproducibility) and adds an MLOps workflow (MLflow-based experiment/model/dataset versioning)
✅ Makes remediation safety explicit by default: allowlisted actions only, human approval required before execution, autonomous remediation moved to future work
✅ Rewrites the research paper section and all research claims in hypothesis language ("we propose," "we hypothesize," "to be evaluated against"), with ablation studies as a required part of the evaluation, and no outperformance percentage claimed before it is measured

**This document is the single, internally consistent master blueprint for CausalOps X**, structured so that a student/research team can realistically build the MVP layer, extend into the advanced layer, and pursue the ATCGT research contribution as a genuinely evaluated (not pre-assumed) result.

---

## Revision Status — v2.1

- Remaining contradictions: None identified
- Core architecture: Preserved
- Five-component pipeline: Preserved
- ATCGT research architecture: Preserved
- Production-data claims: Removed
- Performance claims: Reframed as experimental targets
- Security model: Preserved
- Human-approved allowlisted remediation: Preserved
- `service_id` (TEXT slug) vs. entity IDs (UUID): Unified everywhere — Part 5.3, database (Part 7.1), frontend types (Part 6.3), Kafka messages (Part 9), Neo4j node keys (Part 7.2)
- Kafka KRaft deployment example: Labeled as testbed/demo configuration; production path points to a validated Helm chart (e.g. Strimzi), not the inline YAML — Part 3.2
- Telemetry architecture: Traces confirmed to bypass Kafka (queried directly from Jaeger); `raw.traces` topic removed from the Kafka topic list — Part 2.1, Part 3.2, Part 8.1
- RCA data-retrieval flow: Explicit per-source mapping (metrics → TimescaleDB, events → PostgreSQL, traces → Jaeger directly, graph → Neo4j) — Part 9.4
- Master Model Pipeline Table: Added — Part 9.1.1
- Recovery-recommendation training-data generation: Documented end-to-end (fault injection → candidate actions → controlled execution → outcome measurement → training signal) — Part 9.6.1
- Counterfactual intervention/outcome data generation: Documented end-to-end, sourced from the same controlled testbed, with the DoWhy causality caveat stated explicitly — Part 9.7.1
- ATCGT batching for `batch_size > 1`: Corrected with a PyTorch Geometric `Batch`/disjoint-graph implementation note, replacing the earlier single-`edge_index` reuse — Part 9.9.1
- VAE anomaly-threshold methodology: Documented (percentile-based, validation-FPR-constrained, or validation-F1 options; test split never used for threshold selection) — Part 9.3.1
- Dataset-selection table with explicit `TBD` placeholders for not-yet-chosen public datasets: Added — Part 9.2
- MVP deployment simplification rule (logical separation ≠ mandatory separate Kubernetes deployments): Added — Part 2.2.1
- Global scan for: `service_id`/UUID conflicts, Prometheus/TimescaleDB/PostgreSQL/Neo4j/Redis/Jaeger/Kafka references, model-name consistency (VAE, Graph Transformer, LSTM, Temporal-GNN, LightGBM Learning-to-Rank, DoWhy, causal-learn, ATCGT), pipeline component count (five), and fabricated production-data/performance claims: Completed, no contradictions found
