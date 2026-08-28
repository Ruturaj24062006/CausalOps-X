from kafka import KafkaProducer
import json
import logging
from .config import KAFKA_BOOTSTRAP_SERVERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaPublisher:
    def __init__(self):
        self.producer = None

    def get_producer(self):
        if self.producer is None:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
            except Exception as e:
                logger.error(f"Failed to initialize Kafka producer: {e}")
        return self.producer

    def publish(self, topic: str, message: dict):
        producer = self.get_producer()
        if not producer:
            return False
        try:
            producer.send(topic, message)
            return True
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            return False

publisher = KafkaPublisher()
