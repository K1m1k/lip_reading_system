import cv2
import numpy as np
import mediapipe as mp
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class LipLandmarks:
    landmarks: np.ndarray
    bounding_box: Optional[np.ndarray] = None
    confidence: float = 0.0
    normalized_landmarks: Optional[np.ndarray] = None

class LipTracker:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=config.get('static_mode', False),
            max_num_faces=config.get('max_faces', 1),
            refine_landmarks=config.get('refine_landmarks', True),
            min_detection_confidence=config.get('min_detection_confidence', 0.5),
            min_tracking_confidence=config.get('min_tracking_confidence', 0.5)
        )
        
        self.lip_indices = list(range(61, 68)) + list(range(267, 294))
        self.face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=1, 
            min_detection_confidence=0.5
        )
        
        self.tracked_positions = {}
        self.smoothing_window = config.get('smoothing_window', 5)
        self.position_history = {}
    
    def detect_lips(self, frame: np.ndarray, stream_id: Optional[str] = None) -> Optional[LipLandmarks]:
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            
            if not results.multi_face_landmarks:
                return self._fallback_detection(frame, stream_id)
                
            face_landmarks = results.multi_face_landmarks[0]
            lip_points = []
            normalized_points = []
            
            for idx in self.lip_indices:
                landmark = face_landmarks.landmark[idx]
                h, w = frame.shape[:2]
                x, y = int(landmark.x * w), int(landmark.y * h)
                lip_points.append([x, y])
                normalized_points.append([landmark.x, landmark.y])
            
            lip_array = np.array(lip_points)
            x_coords = lip_array[:, 0]
            y_coords = lip_array[:, 1]
            
            x_min, x_max = np.min(x_coords), np.max(x_coords)
            y_min, y_max = np.min(y_coords), np.max(y_coords)
            
            if stream_id and self.config.get('smoothing', True):
                lip_array = self._apply_smoothing(stream_id, lip_array)
            
            return LipLandmarks(
                landmarks=lip_array,
                bounding_box=np.array([x_min, y_min, x_max - x_min, y_max - y_min]),
                confidence=self._calculate_confidence(lip_array),
                normalized_landmarks=np.array(normalized_points)
            )
            
        except Exception as e:
            logger.error(f"Errore rilevamento labbra: {e}")
            return None
    
    def _apply_smoothing(self, stream_id: str, current_points: np.ndarray) -> np.ndarray:
        if stream_id not in self.position_history:
            self.position_history[stream_id] = deque(maxlen=self.smoothing_window)
        
        self.position_history[stream_id].append(current_points)
        
        if len(self.position_history[stream_id]) > 1:
            smoothed_points = np.mean(list(self.position_history[stream_id]), axis=0)
            return smoothed_points.astype(np.int32)
        
        return current_points
    
    def _fallback_detection(self, frame: np.ndarray, stream_id: Optional[str]) -> Optional[LipLandmarks]:
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
            
            lip_y = y + height * 0.6
            lip_height = height * 0.3
            
            lip_points = []
            for i in range(8):
                px = x + width * (i / 7)
                py = lip_y + lip_height * (0.5 + 0.3 * np.sin(i * 0.8))
                lip_points.append([px, py])
            
            lip_array = np.array(lip_points, dtype=np.int32)
            
            return LipLandmarks(
                landmarks=lip_array,
                bounding_box=np.array([x, y, width, height]),
                confidence=detection.score[0],
                normalized_landmarks=None
            )
            
        except Exception as e:
            logger.error(f"Errore fallback detection: {e}")
            return None
    
    def extract_roi(self, frame: np.ndarray, landmarks: LipLandmarks) -> np.ndarray:
        x_coords = landmarks.landmarks[:, 0]
        y_coords = landmarks.landmarks[:, 1]
        
        x_min, x_max = np.min(x_coords), np.max(x_coords)
        y_min, y_max = np.min(y_coords), np.max(y_coords)
        
        padding = self.config.get('roi_padding', 15)
        x_min = max(0, x_min - padding)
        y_min = max(0, y_min - padding)
        x_max = min(frame.shape[1], x_max + padding)
        y_max = min(frame.shape[0], y_max + padding)
        
        roi = frame[y_min:y_max, x_min:x_max]
        roi = self._preprocess_roi(roi)
        
        return roi
    
    def _preprocess_roi(self, roi: np.ndarray) -> np.ndarray:
        target_size = self.config.get('roi_target_size', (100, 50))
        if roi.size > 0:
            roi = cv2.resize(roi, target_size)
        
        if self.config.get('convert_to_grayscale', True):
            if len(roi.shape) == 3:
                roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        
        if self.config.get('normalize_roi', True):
            roi = roi.astype(np.float32) / 255.0
        
        return roi
    
    def _calculate_confidence(self, landmarks: np.ndarray) -> float:
        x_coords = landmarks[:, 0]
        y_coords = landmarks[:, 1]
        area = (np.max(x_coords) - np.min(x_coords)) * (np.max(y_coords) - np.min(y_coords))
        
        if area > 0:
            return min(1.0, area / 1000.0)
        return 0.0
