import unittest
import time
import numpy as np
from src.scalable_processing import DistributedProcessingSystem, FrameBuffer

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.config = {
            'max_threads': 2,
            'buffer_size': 5,
            'frame_batch_size': 2,
            'gpu_acceleration': False
        }
        self.model_path = './tests/test_model.h5'
    
    def test_frame_buffer(self):
        buffer = FrameBuffer(max_size=5)
        
        # Test aggiunta frame
        for i in range(10):
            buffer.add_frame(np.zeros((50, 100), dtype=np.uint8))
        
        # Test recupero frame
        frames = buffer.get_frames(5)
        self.assertEqual(len(frames), 5)
    
    def test_processing_system(self):
        dps = DistributedProcessingSystem(self.config, self.model_path)
        self.assertEqual(len(dps.workers), 2)
        dps.shutdown()

if __name__ == '__main__':
    unittest.main()
