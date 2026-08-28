import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_INPUT_TOPICS = os.getenv("KAFKA_INPUT_TOPICS", "raw.metrics,raw.logs,raw.events").split(",")
KAFKA_OUTPUT_TOPIC = os.getenv("KAFKA_OUTPUT_TOPIC", "enriched.features")
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "causalops-stream-processor")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
