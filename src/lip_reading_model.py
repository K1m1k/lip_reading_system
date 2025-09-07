import numpy as np
import logging
import os
import cv2
from lipnet_client import LipNetClient
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)

class LipReadingModel:
    def __init__(self, config: dict):
        self.config = config
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        try:
            svc_config = self.config.get('service', {})
            self.client = LipNetClient(
                base_url=svc_config.get('url', 'http://localhost:8000'),
                timeout_s=svc_config.get('timeout_s', 5.0),
                retries=svc_config.get('retries', 2),
            )
            logger.info(f"LipNet client initialized with URL: {svc_config.get('url')}")
        except Exception as e:
            logger.error(f"Failed to initialize LipNet client: {e}")
            raise

    async def predict(self, sequence: List[np.ndarray]) -> Tuple[Optional[str], float]:
        try:
            if len(sequence) == 0:
                return None, 0.0

            processed_sequence = []
            target_size = (100, 50)
            
            for frame in sequence:
                if len(frame.shape) == 2:
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                elif frame.shape[2] == 1:
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                
                frame = cv2.resize(frame, target_size)
                processed_sequence.append(frame)

            text, confidence = await self.client.predict(processed_sequence)
            return text, confidence

        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            return None, 0.0

    async def close(self):
        if self.client:
            await self.client.close()
