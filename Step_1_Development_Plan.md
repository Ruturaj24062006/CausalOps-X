# CausalOps X: Phase 1 Development Plan

Based on the `CausalOps_X_Master_Blueprint.md`, here is the detailed step-by-step breakdown for the very first step in the project, **Phase 1 — Environment & Architecture Setup**.

## Step 1: Provision a Kubernetes Test Cluster
Your first task is to set up the foundational environment where all services will run. Since this is an MVP/Testbed:
- **Local Option**: Install and configure `minikube` or `kind` (Kubernetes in Docker) on your local machine.
- **Cloud Option**: Alternatively, provision a small managed cluster (like Amazon EKS, Google GKE, or DigitalOcean Kubernetes) if you want a more realistic cloud footprint.
- **Goal**: Ensure you can run `kubectl get nodes` and see a healthy cluster ready for deployments.

## Step 2: Set Up Repository Workspace & CI/CD Skeleton
Before writing application code, organize the project structure to manage the microservices.
- **Create Repository Structure**: Set up directories for each logical service (e.g., `data-ingestion-service`, `stream-processing-service`, `ml-inference-service`, etc.).
- **Base Docker Images**: Create foundational `Dockerfile`s for Python and Node.js services with security best practices (e.g., non-root user, minimal base image).
- **CI/CD Skeleton**: Set up a basic GitHub Actions (or GitLab CI) workflow that lints, builds the Docker images, and (optionally) deplhes them to the test cluster.

## Step 3: Deploy Infrastructure Dependencies
Deploy the core databases and message brokers to your Kubernetes test cluster. These are required before any of your custom code can be tested.
1. **Kafka (KRaft Mode)**: Deploy a Kafka cluster without ZooKeeper. This will serve as the event streaming backbone for metrics and anomalies.
2. **PostgreSQL + TimescaleDB**: Deploy the relational database extended with TimescaleDB for storing time-series metrics, incidents, and actions. Run the schema creation SQL scripts defined in Part 7.1.
3. **Neo4j**: Deploy the Neo4j graph database, which will be used to store the service dependency graph and causal hypotheses.
4. **Redis**: Deploy Redis, which will be used strictly for caching, rate limiting, and real-time dashboard WebSocket pub/sub.

## Summary of Deliverables for Phase 1
By the end of Phase 1, you should have a live Kubernetes test cluster containing:
* A structured code repository.
* Running instances of Kafka, PostgreSQL/TimescaleDB, Neo4j, and Redis.
* Validated connectivity to all of these data stores.

Once this infrastructure is stable, you will be ready to move on to **Phase 2: Observability Pipeline**, where you start ingesting actual metrics and traces into this environment!
