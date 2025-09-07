import hashlib
import hmac
from cryptography.fernet import Fernet
import logging
from typing import Optional
import base64

logger = logging.getLogger(__name__)

class DataEncryptor:
    def __init__(self, encryption_key: bytes, signature_key: Optional[bytes] = None):
        # Normalizza la chiave di crittografia
        if len(encryption_key) == 32:
            encryption_key = base64.urlsafe_b64encode(encryption_key)
        elif len(encryption_key) != 44:  # Lunghezza standard Fernet key
            raise ValueError("Invalid encryption key length")
            
        self.cipher = Fernet(encryption_key)
        self.signature_key = signature_key
    
    def encrypt_data(self, data: bytes) -> bytes:
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.cipher.encrypt(data)
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        return self.cipher.decrypt(encrypted_data)
    
    def encrypt_image(self, image_path: str, output_path: Optional[str] = None) -> Optional[str]:
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            encrypted_data = self.encrypt_data(image_data)
            
            if not output_path:
                output_path = image_path + '.enc'
            
            with open(output_path, 'wb') as f:
                f.write(encrypted_data)
            
            return output_path
        except Exception as e:
            logger.error(f"Errore criptazione immagine: {e}")
            return None
    
    def generate_signature(self, data: str) -> str:
        if self.signature_key is None:
            return ""
            
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hmac.new(self.signature_key, data, hashlib.sha256).hexdigest()
