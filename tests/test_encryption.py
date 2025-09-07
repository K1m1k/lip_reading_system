import unittest
import sys
import os
from src.encryption import DataEncryptor

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestEncryption(unittest.TestCase):
    def setUp(self):
        # Generate a valid 32-byte key and encode it for Fernet
        import base64
        key = b'0' * 32
        self.encryption_key = base64.urlsafe_b64encode(key)
        self.signature_key = b'1' * 32
        
    def test_encryption_decryption(self):
        encryptor = DataEncryptor(self.encryption_key, self.signature_key)
        test_data = b"test data"
        
        encrypted = encryptor.encrypt_data(test_data)
        decrypted = encryptor.decrypt_data(encrypted)
        
        self.assertEqual(test_data, decrypted)
        
    def test_signature_generation(self):
        encryptor = DataEncryptor(self.encryption_key, self.signature_key)
        data = "test data"
        
        signature = encryptor.generate_signature(data)
        self.assertIsInstance(signature, str)
        self.assertEqual(len(signature), 64)  # SHA256 hex digest length

if __name__ == '__main__':
    unittest.main()
