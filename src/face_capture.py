import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, Dict, Any
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class FaceCaptureModule:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=1, 
            min_detection_confidence=0.5
        )
        
    def capture_face(self, frame: np.ndarray) -> Optional[np.ndarray]:
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_frame)
            
            if not results.detections:
                return None
                
            detection = max(results.detections, key=lambda d: d.score)
            bbox = detection.location_data.relative_bounding_box
            
            h, w = frame.shape[:2]
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)
            
            margin = self.config.get('face_margin', 20)
            x = max(0, x - margin)
            y = max(0, y - margin)
            width = min(w - x, width + 2 * margin)
            height = min(h - y, height + 2 * margin)
            
            face_image = frame[y:y+height, x:x+width]
            
            if face_image.size == 0:
                return None
                
            return face_image
            
        except Exception as e:
            logger.error(f"Errore acquisizione volto: {e}")
            return None
    
    def save_face_image(self, face_image: np.ndarray, base_path: str, 
                       camera_id: str, timestamp: datetime) -> Optional[str]:
        try:
            if not os.path.exists(base_path):
                os.makedirs(base_path)
                
            filename = f"{camera_id}_face_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.jpg"
            filepath = os.path.join(base_path, filename)
            
            success = cv2.imwrite(filepath, face_image)
            
            if success:
                return filepath
            else:
                logger.error(f"Errore salvataggio immagine volto: {filepath}")
                return None
                
        except Exception as e:
            logger.error(f"Errore salvataggio volto: {e}")
            return None
