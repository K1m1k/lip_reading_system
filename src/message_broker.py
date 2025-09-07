import pika
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MessageBroker:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.channel = None
        self._connect()
    
    def _connect(self):
        try:
            credentials = pika.PlainCredentials(
                self.config['username'], 
                self.config['password']
            )
            
            connection_params = pika.ConnectionParameters(
                host=self.config['host'],
                port=self.config['port'],
                credentials=credentials,
                connection_attempts=self.config.get('connection_retries', 5),
                retry_delay=self.config.get('retry_delay', 2)
            )
            
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()
            
            self.channel.exchange_declare(
                exchange=self.config.get('exchange', 'detection_events'), 
                exchange_type='direct',
                durable=True
            )
            
            self.channel.queue_declare(
                queue=self.config.get('queue', 'detection_queue'), 
                durable=True
            )
            
            self.channel.queue_bind(
                exchange=self.config.get('exchange', 'detection_events'), 
                queue=self.config.get('queue', 'detection_queue'), 
                routing_key=self.config.get('routing_key', 'detection')
            )
            
            # Set prefetch count
            prefetch_count = self.config.get('prefetch', 16)
            self.channel.basic_qos(prefetch_count=prefetch_count)
            
            logger.info("Connesso a RabbitMQ con successo")
            
        except Exception as e:
            logger.error(f"Errore connessione RabbitMQ: {e}")
    
    def publish_detection(self, detection_data: Dict[str, Any]) -> bool:
        try:
            self.channel.basic_publish(
                exchange=self.config.get('exchange', 'detection_events'),
                routing_key=self.config.get('routing_key', 'detection'),
                body=json.dumps(detection_data),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            logger.info(f"Evento pubblicato: {detection_data['phrase']}")
            return True
        except Exception as e:
            logger.error(f"Errore pubblicazione evento: {e}")
            return False
    
    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
    
    def is_connected(self) -> bool:
        return self.connection is not None and not self.connection.is_closed
