# CausalOps X 

**CausalOps X** is an advanced causal-AI-powered AIOps platform that goes beyond traditional correlation-based monitoring in microservice systems. It helps Site Reliability Engineers (SRE) and platform teams answer the critical questions:
- *Why did a failure happen?* (Root Cause Analysis)
- *How will it cascade?* (Failure Propagation Prediction)
- *What should we do?* (Recovery Recommendation)

This repository serves as the core layer consisting of infrastructure pipelines, machine learning inference backends, and a React frontend dashboard.

---

## 📂 Project Structure

This project adopts a modular architecture separating model development, backend logic, and frontend visualization. 

* **`/models`** — Causal-AI model weights (trained safely off-site via Google Colab).
* **`/ml`** — Core logic containing anomaly detection algorithms, graph builders, propagation networks, and counterfactual evaluation systems.
* **`/services`** — Individual backend microservices: 
  * `data-ingestion-service`
  * `stream-processing-service`
  * `ml-inference-service`
  * `incident-service`
  * `remediation-service`
* **`/frontend`** — The web dashboard constructed with React, Vite, and WebSocket streaming.
* **`/infrastructure`** & **`/kubernetes`** — The data backbone, housing configurations for Kafka, PostgreSQL (TimescaleDB), Neo4j, Redis, and overall cluster orchestration.
* **`/database`** — Schemas and migration tracks for TimeScale and Cypher (Neo4j).

## 🚀 Getting Started

The platform utilizes a multi-technology setup requiring container orchestration. 

1. Ensure **Docker** and **Kubernetes** configuration files are properly routed on your local machine.
2. Initialize core infrastructure dependencies located in `/infrastructure`.
3. Provide model weight files matching your architecture to `/models` once training loops complete in Colab.

*(Further architectural details are housed locally inside the `docs/` folder.)*
