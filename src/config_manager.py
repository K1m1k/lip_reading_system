import os
import yaml
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = {}
        self._load_config()
        self._load_env_vars()
        
    def _load_config(self) -> None:
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Configurazione caricata da {self.config_path}")
        except Exception as e:
            logger.error(f"Errore nel caricamento del file di configurazione: {e}")
            raise
            
    def _load_env_vars(self) -> None:
        load_dotenv()
        
        # Database
        if os.getenv('DB_HOST'):
            self.config['database']['host'] = os.getenv('DB_HOST')
        if os.getenv('DB_PORT'):
            self.config['database']['port'] = int(os.getenv('DB_PORT'))
        if os.getenv('DB_NAME'):
            self.config['database']['name'] = os.getenv('DB_NAME')
        if os.getenv('DB_USER'):
            self.config['database']['user'] = os.getenv('DB_USER')
        if os.getenv('DB_PASSWORD'):
            self.config['database']['password'] = os.getenv('DB_PASSWORD')
            
        # RabbitMQ
        if os.getenv('RABBITMQ_HOST'):
            self.config['message_broker']['host'] = os.getenv('RABBITMQ_HOST')
        if os.getenv('RABBITMQ_PORT'):
            self.config['message_broker']['port'] = int(os.getenv('RABBITMQ_PORT'))
        if os.getenv('RABBITMQ_USER'):
            self.config['message_broker']['username'] = os.getenv('RABBITMQ_USER')
        if os.getenv('RABBITMQ_PASS'):
            self.config['message_broker']['password'] = os.getenv('RABBITMQ_PASS')
        if os.getenv('RABBITMQ_EXCHANGE'):
            self.config['message_broker']['exchange'] = os.getenv('RABBITMQ_EXCHANGE')
        if os.getenv('RABBITMQ_QUEUE'):
            self.config['message_broker']['queue'] = os.getenv('RABBITMQ_QUEUE')
        if os.getenv('RABBITMQ_ROUTING_KEY'):
            self.config['message_broker']['routing_key'] = os.getenv('RABBITMQ_ROUTING_KEY')
            
        # Security
        if os.getenv('VAULT_ADDR'):
            self.config['encryption']['key_management']['vault_address'] = os.getenv('VAULT_ADDR')
        if os.getenv('VAULT_TOKEN'):
            self.config['encryption']['key_management']['vault_token'] = os.getenv('VAULT_TOKEN')
        if os.getenv('KMS_KEY_ID'):
            self.config['encryption']['signature_key_management']['kms_key_id'] = os.getenv('KMS_KEY_ID')
        if os.getenv('JWT_SECRET'):
            self.config['dashboard']['jwt_secret'] = os.getenv('JWT_SECRET')
            
        # Monitoring
        if os.getenv('SYSLOG_HOST'):
            self.config['monitoring']['logging']['handlers'][1]['host'] = os.getenv('SYSLOG_HOST')
        if os.getenv('SYSLOG_PORT'):
            self.config['monitoring']['logging']['handlers'][1]['port'] = int(os.getenv('SYSLOG_PORT'))
        if os.getenv('JAEGER_ENDPOINT'):
            self.config['monitoring']['tracing']['jaeger_endpoint'] = os.getenv('JAEGER_ENDPOINT')
            
        # Alerting
        if os.getenv('ALERT_WEBHOOK_URL'):
            self.config['alerting']['webhook_url'] = os.getenv('ALERT_WEBHOOK_URL')
        if os.getenv('SLACK_WEBHOOK_URL'):
            self.config['alerting']['notification_channels']['slack']['webhook_url'] = os.getenv('SLACK_WEBHOOK_URL')
            
        # Cloud
        if os.getenv('AWS_REGION'):
            self.config['cloud_deployment']['aws']['region'] = os.getenv('AWS_REGION')
        if os.getenv('AWS_VPC_ID'):
            self.config['cloud_deployment']['aws']['vpc_id'] = os.getenv('AWS_VPC_ID')
        if os.getenv('AWS_SUBNET_IDS'):
            self.config['cloud_deployment']['aws']['subnet_ids'] = os.getenv('AWS_SUBNET_IDS').split(',')
        if os.getenv('AWS_SECURITY_GROUP'):
            self.config['cloud_deployment']['aws']['security_group'] = os.getenv('AWS_SECURITY_GROUP')
            
        # LipNet Service
        if os.getenv('LIPNET_URL'):
            self.config['model']['service']['url'] = os.getenv('LIPNET_URL')
            
        logger.info("Variabili d'ambiente caricate e integrate nella configurazione")
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def update(self, key: str, value: Any) -> None:
        keys = key.split('.')
        config_ptr = self.config
        
        for k in keys[:-1]:
            if k not in config_ptr:
                config_ptr[k] = {}
            config_ptr = config_ptr[k]
            
        config_ptr[keys[-1]] = value
        logger.debug(f"Configurazione aggiornata: {key} = {value}")
