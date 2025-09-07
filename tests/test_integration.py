import unittest
import sys
import os
from src.enhanced_lip_reading_system import EnhancedLipReadingSystem

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestIntegration(unittest.TestCase):
    def test_system_initialization(self):
        try:
            system = EnhancedLipReadingSystem("config/config.yaml")
            self.assertIsNotNone(system)
        except Exception as e:
            self.fail(f"Errore nell'inizializzazione del sistema: {e}")

if __name__ == '__main__':
    unittest.main()
