from kafka import KafkaConsumer
import json
import logging
import threading
import socket
import os

# Dynamic DNS monkey-patch to bypass Kafka Advertised Listener issues locally without needing Admin Hosts file edits
if not os.path.exists("/var/run/secrets/kubernetes.io"):
    _orig_getaddrinfo = socket.getaddrinfo
    def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if host == "kafka":
            host = "127.0.0.1"
        return _orig_getaddrinfo(host, port, family, type, proto, flags)
    socket.getaddrinfo = patched_getaddrinfo

from .config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_INPUT_TOPICS, KAFKA_CONSUMER_GROUP
from .normalizer import normalize_event
from .kafka_producer import producer_client
from .features.windows import WindowManager
from .inference import Model1Engine
from . import state_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelemetryConsumer:
    def __init__(self):
        self.thread = None
        self.flush_thread = None
        self.running = False
        self.consumer = None
        self.window_manager = WindowManager()
        self.engine = Model1Engine()
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._consume_loop, daemon=True)
        self.flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self.thread.start()
        self.flush_thread.start()
        
    def stop(self):
        self.running = False
        if self.consumer:
            self.consumer.close()

    def _flush_loop(self):
        import time
        while self.running:
            time.sleep(5)
            features = self.window_manager.flush_expired()
            for f in features:
                producer_client.publish(f.model_dump())
                pred = self.engine.ingest_vector(f)
                if pred.get("status") not in ("INSUFFICIENT_SEQUENCE_DATA", "INVALID_FEATURE_COUNT", "INFERENCE_FAILURE", "REJECT_INVALID_MATHEMATICS"):
                    logger.info(f"Model1 Output Validated >> {pred}")
                    # ── Publish real inference result to shared API state ──
                    state_store.update_model1(pred)

    def _consume_loop(self):
        while self.running:
            try:
                logger.info(f"Connecting consumer to {KAFKA_BOOTSTRAP_SERVERS}")
                self.consumer = KafkaConsumer(
                    *KAFKA_INPUT_TOPICS,
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
                    group_id=KAFKA_CONSUMER_GROUP,
                    value_deserializer=lambda m: self._safe_deserialize(m),
                    auto_offset_reset='latest',
                    enable_auto_commit=True
                )
                
                logger.info("Successfully bound streaming telemetry connections")
                for message in self.consumer:
                    if not self.running:
                        break
                        
                    if message.value is None:
                        continue
                        
                    normalized = normalize_event(message.topic, message.value)
                    if normalized:
                        self.window_manager.add_event(normalized)
                        
            except Exception as e:
                logger.error(f"Consumer connection failure: {e}")
                import time
                time.sleep(5)
                
    def _safe_deserialize(self, value):
        try:
            return json.loads(value.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to decode message efficiently: {e}")
            return None

consumer_worker = TelemetryConsumer()
