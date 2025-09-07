import sys
import os
import unittest
from database import DatabaseManager

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'name': 'lip_reading_db_test',
            'user': 'lip_user',
            'password': 'secure_password'
        }
        self.db = DatabaseManager(self.db_config)

    def test_add_to_blacklist(self):
        result = self.db.add_to_blacklist("test_phrase")
        self.assertTrue(result)

    def test_get_blacklist(self):
        blacklist = self.db.get_blacklist()
        self.assertIsInstance(blacklist, list)

    def test_save_detection(self):
        detection_data = {
            'phrase': 'test_phrase',
            'confidence': 0.85,
            'camera_id': 'test_camera',
            'location': 'test_location'
        }
        detection_id = self.db.save_detection(detection_data)
        self.assertIsNotNone(detection_id)

    def test_get_detections(self):
        detections = self.db.get_detections()
        self.assertIsInstance(detections, list)

if __name__ == '__main__':
    unittest.main()
