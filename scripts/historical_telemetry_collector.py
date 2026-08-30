import os
import sys
import json
import time
import signal
import logging
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# Existing project env vars
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPICS = [
    os.getenv("KAFKA_METRICS_TOPIC", "raw.metrics"),
    os.getenv("KAFKA_LOGS_TOPIC", "raw.logs"),
    os.getenv("KAFKA_EVENTS_TOPIC", "raw.events")
]
OUT_FILE = os.environ.get("COLLECTOR_OUT_FILE", r"d:\Projects\CausalOps X\datasets\raw\historical_telemetry_dump.jsonl")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Collector")

running = True

def handle_shutdown(signum, frame):
    global running
    logger.info("Graceful shutdown received. Stopping collector...")
    running = False

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

def safe_deserialize(m):
    try:
        return json.loads(m.decode('utf-8'))
    except Exception:
        return {"_raw_error": "deserialize failed", "data": m.decode('utf-8', errors='replace')}

def main():
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    logger.info(f"Targeting Kafka server: {KAFKA_BOOTSTRAP_SERVERS}")
    
    consumer = None
    while running and consumer is None:
        try:
            consumer = KafkaConsumer(
                *TOPICS,
                bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
                group_id="historical_telemetry_archiver",
                auto_offset_reset="earliest",  # ensure no silent data loss from the beginning
                enable_auto_commit=True,
                value_deserializer=safe_deserialize
            )
            logger.info(f"Successfully subscribed to topics: {TOPICS}")
        except Exception as e:
            logger.warning(f"Failed to connect to Kafka. Retrying in 5s... ({e})")
            time.sleep(5)
            
    if not running:
        return

    logger.info(f"Writing telemetry synchronously to {OUT_FILE}")
    
    with open(OUT_FILE, 'a', encoding='utf-8') as f:
        while running:
            try:
                msg_pack = consumer.poll(timeout_ms=1000)
                for tp, messages in msg_pack.items():
                    for msg in messages:
                        record = msg.value
                        
                        # Preserve origin tracking directly on dict root
                        if isinstance(record, dict):
                            record["_kafka_topic"] = msg.topic
                            record["_archive_timestamp"] = time.time()
                            f.write(json.dumps(record) + "\n")
                        else:
                            wrap = {
                                "_kafka_topic": msg.topic,
                                "_archive_timestamp": time.time(),
                                "payload": record
                            }
                            f.write(json.dumps(wrap) + "\n")
                
                if msg_pack:
                    f.flush()
            except Exception as e:
                logger.error(f"Error executing poll/write: {e}")
                time.sleep(1)
                
    if consumer:
        consumer.close()
        logger.info("Kafka consumer un-subscribed and safely closed.")

if __name__ == "__main__":
    main()
