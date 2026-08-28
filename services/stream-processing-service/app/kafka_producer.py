from kafka import KafkaProducer
import json
import logging
from .config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_OUTPUT_TOPIC

logger = logging.getLogger(__name__)

class NormalizedProducer:
    def __init__(self):
        self.producer = None
    
    def get_producer(self):
        if not self.producer:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
            except Exception as e:
                logger.error(f"Kafka producer error: {e}")
        return self.producer
    
    def publish(self, message: dict):
        prod = self.get_producer()
        if prod:
            try:
                prod.send(KAFKA_OUTPUT_TOPIC, message)
                return True
            except Exception as e:
                logger.error(f"Failed to produce message: {e}")
        return False

producer_client = NormalizedProducer()
