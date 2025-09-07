import os
import logging
import hvac
import boto3
from botocore.exceptions import ClientError
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import secrets

logger = logging.getLogger(__name__)

class SecretManager:
    """Gestore centralizzato per le credenziali sicure"""
    
    def __init__(self, config):
        self.config = config
        self.encryption_key = None
        self.signature_key = None
        self._load_keys()
    
    def _load_keys(self):
        """Carica le chiavi di crittografia e firma da Vault/KMS"""
        try:
            # Carica la chiave di crittografia da Vault
            if self.config['encryption']['key_management']['type'] == 'vault':
                self.encryption_key = self._get_key_from_vault(
                    self.config['encryption']['key_management']['secret_path']
                )
            
            # Carica la chiave di firma da KMS
            if self.config['encryption']['signature_key_management']['type'] == 'kms':
                self.signature_key = self._get_key_from_kms(
                    self.config['encryption']['signature_key_management']['kms_key_id']
                )
                
        except Exception as e:
            logger.critical(f"Errore fatale nel caricamento delle chiavi: {e}", exc_info=True)
            raise
    
    def _get_key_from_vault(self, secret_path):
        """Ottiene la chiave di crittografia da HashiCorp Vault"""
        try:
            client = hvac.Client(
                url=os.getenv('VAULT_ADDR'),
                token=os.getenv('VAULT_TOKEN')
            )
            
            if not client.is_authenticated():
                logger.error("Autenticazione Vault fallita")
                return None
                
            # Legge il segreto da Vault
            secret_response = client.secrets.kv.v2.read_secret_version(
                path=secret_path,
                mount_point='secret'
            )
            
            # Estrae la chiave di crittografia
            encryption_key = secret_response['data']['data']['encryption_key']
            return base64.b64decode(encryption_key)
            
        except Exception as e:
            logger.error(f"Errore nel recupero della chiave da Vault: {e}")
            return None
    
    def _get_key_from_kms(self, kms_key_id):
        """Ottiene la chiave di firma da AWS KMS"""
        try:
            kms_client = boto3.client('kms')
            
            # Genera una chiave dati usando KMS
            response = kms_client.generate_data_key(
                KeyId=kms_key_id,
                KeySpec='AES_256'
            )
            
            # La chiave crittografata viene salvata per uso futuro
            self.encrypted_signature_key = response['CiphertextBlob']
            
            # Restituisce la chiave non crittografata per uso immediato
            return response['Plaintext']
            
        except ClientError as e:
            logger.error(f"Errore KMS: {e.response['Error']['Code']}")
            return None
        except Exception as e:
            logger.error(f"Errore generico KMS: {e}")
            return None
    
    def get_encryption_key(self):
        """Restituisce la chiave di crittografia"""
        if not self.encryption_key:
            self._load_keys()
        return self.encryption_key
    
    def get_signature_key(self):
        """Restituisce la chiave di firma"""
        if not self.signature_key:
            self._load_keys()
        return self.signature_key
    
    def rotate_encryption_key(self):
        """Ruota la chiave di crittografia"""
        try:
            # Genera una nuova chiave casuale
            new_key = secrets.token_bytes(32)  # 256-bit key for AES-256
            
            # Crittografa la nuova chiave con la chiave master di Vault
            if self.config['encryption']['key_management']['type'] == 'vault':
                client = hvac.Client(
                    url=os.getenv('VAULT_ADDR'),
                    token=os.getenv('VAULT_TOKEN')
                )
                
                # Scrive la nuova chiave in Vault
                client.secrets.kv.v2.create_or_update_secret(
                    path=self.config['encryption']['key_management']['secret_path'],
                    secret=dict(encryption_key=base64.b64encode(new_key).decode('utf-8')),
                    mount_point='secret'
                )
                
                # Aggiorna la chiave in memoria
                self.encryption_key = new_key
                logger.info("Chiave di crittografia ruotata con successo")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Errore nella rotazione della chiave: {e}")
            return False
    
    @staticmethod
    def generate_secure_key():
        """Genera una chiave crittografica sicura"""
        return secrets.token_bytes(32)  # 256-bit key
    
    @staticmethod
    def generate_vault_token(ttl='24h'):
        """Genera un token Vault sicuro"""
        return secrets.token_hex(32)
