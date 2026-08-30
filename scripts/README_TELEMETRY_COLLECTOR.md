# Historical Telemetry Collector

This orchestratable script provisions a specialized background Kafka Consumer to autonomously aggregate `raw.metrics`, `raw.logs`, and `raw.events` directly from the operational brokers. The mission of this script is exclusively to assemble genuine historical JSON dictionaries required for Model 1 Deep Learning LSTM-VAE feature sequences.

## 1. How to start the collector
Make sure your Kafka broker environment (`KAFKA_BOOTSTRAP_SERVERS`) is reachable.
Run the daemon utilizing the project python context:
```bash
python scripts/historical_telemetry_collector.py
```
*(Optionally run within `tmux`, `screen`, or deploy it via an unmanaged generic Kubernetes Pod)*

## 2. Which Kafka topics are consumed
The script subscribes dynamically based on your env block:
- `raw.metrics`
- `raw.logs`
- `raw.events`

## 3. Where the JSONL archive is written
All captured telemetry (appended with tracking metadata) is securely dumped line-by-line to:
`datasets/raw/historical_telemetry_dump.jsonl`

## 4. How to stop it safely
The consumer integrates native UNIX signal interception mechanisms. 
To kill execution safely without silent data loss, transmit a `SIGINT` (CTRL+C) or `SIGTERM`. The loop will abort elegantly, ensuring `f.flush()` completes and disconnecting from the Kafka cluster automatically without poisoning the consumer offset logic. 

## 5. How to verify that records are being collected
As the script polls Kafka intervals (1s loops), successfully captured dumps log status directly incrementally to stdout if monitoring its log tail. Beyond stdout, you can natively verify capture momentum by utilizing the companion verification script (see below).

## 6. How to check the number of records collected & Verify distributions
A native audit utility has been implemented matching Model 1 requirements. To generate immediate diagnostics over your compiled historical cache, invoke:
```bash
python scripts/verify_telemetry_dump.py
```
This utility cleanly maps aggregate counts isolating metrics vs logs vs events representations without locking the destination file boundaries.
