import unittest
import sys
import os
from src.secret_manager import SecretManager

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.config = {
            'encryption': {
                'key_management': {
                    'type': 'vault',
                    'secret_path': 'test/encryption_key'
                },
                'signature_key_management': {
                    'type': 'kms',
                    'kms_key_id': 'test-kms-key'
                }
            }
        }
    
    def test_key_generation(self):
        secret_manager = SecretManager(self.config)
        key = secret_manager.generate_secure_key()
        self.assertEqual(len(key), 32)  # 256-bit key
    
    def test_vault_token_generation(self):
        token = SecretManager.generate_vault_token()
        self.assertEqual(len(token), 64)  # 32 bytes in hex

if __name__ == '__main__':
    unittest.main()
