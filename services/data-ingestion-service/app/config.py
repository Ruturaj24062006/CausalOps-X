import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
KAFKA_METRICS_TOPIC = os.getenv("KAFKA_METRICS_TOPIC", "raw.metrics")
KAFKA_LOGS_TOPIC = os.getenv("KAFKA_LOGS_TOPIC", "raw.logs")
KAFKA_EVENTS_TOPIC = os.getenv("KAFKA_EVENTS_TOPIC", "raw.events")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
