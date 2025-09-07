import base64
import json
import httpx
from typing import List, Tuple, Optional
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class LipNetClient:
    def __init__(self, base_url: str, timeout_s: float = 5.0, retries: int = 2):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_s
        self.retries = retries
        self.client = httpx.AsyncClient(timeout=timeout_s)

    async def predict(self, frames_rgb: List[np.ndarray]) -> Tuple[Optional[str], float]:
        encoded_frames = []
        for frame in frames_rgb:
            success, encoded_image = cv2.imencode(".jpg", frame)
            if not success:
                logger.error("Failed to encode frame")
                continue
            encoded_frames.append(base64.b64encode(encoded_image).decode("ascii"))
        
        if not encoded_frames:
            return None, 0.0
            
        payload = {"sequence": encoded_frames}
        
        for attempt in range(self.retries + 1):
            try:
                r = await self.client.post(
                    f"{self.base_url}/predict", 
                    json=payload, 
                    timeout=self.timeout
                )
                r.raise_for_status()
                data = r.json()
                return data.get("text", ""), float(data.get("confidence", 0.0))
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.retries:
                    logger.error(f"All {self.retries + 1} attempts failed")
                    raise
        return None, 0.0

    async def close(self):
        await self.client.aclose()
