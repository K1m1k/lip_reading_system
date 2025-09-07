import unittest
from unittest.mock import AsyncMock, patch
import numpy as np
from src.lipnet_client import LipNetClient

class TestLipNetClient(unittest.IsolatedAsyncioTestCase):
    async def test_successful_prediction(self):
        client = LipNetClient("http://localhost:8000")
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "text": "hello",
                "confidence": 0.85
            }
            
            frames = [np.zeros((50, 100, 3), dtype=np.uint8) for _ in range(5)]
            text, confidence = await client.predict(frames)
            
            self.assertEqual(text, "hello")
            self.assertEqual(confidence, 0.85)
            
    async def test_retry_on_failure(self):
        client = LipNetClient("http://localhost:8000", retries=2)
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = [
                Exception("First attempt failed"),
                Exception("Second attempt failed"),
                AsyncMock(status_code=200, json=AsyncMock(return_value={"text": "hello", "confidence": 0.85}))
            ]
            
            frames = [np.zeros((50, 100, 3), dtype=np.uint8) for _ in range(5)]
            text, confidence = await client.predict(frames)
            
            self.assertEqual(text, "hello")
            self.assertEqual(confidence, 0.85)
            self.assertEqual(mock_post.call_count, 3)

if __name__ == '__main__':
    unittest.main()
