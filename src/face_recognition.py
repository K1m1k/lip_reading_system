import cv2
import numpy as np
import face_recognition
import logging
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class FaceRecognitionSystem:
    def __init__(self, model_type: str = 'hog', known_faces_path: Optional[str] = None):
        self.model_type = model_type
        self.known_faces = {}
        self.known_names = []
        
        if known_faces_path:
            self.load_known_faces(known_faces_path)
    
    def load_known_faces(self, path: str):
        try:
            for filename in os.listdir(path):
                if filename.endswith(('.jpg', '.jpeg', '.png')):
                    image_path = os.path.join(path, filename)
                    image = face_recognition.load_image_file(image_path)
                    
                    encodings = face_recognition.face_encodings(image)
                    if encodings:
                        name = os.path.splitext(filename)[0]
                        self.known_faces[name] = encodings[0]
                        self.known_names.append(name)
            
            logger.info(f"Caricati {len(self.known_faces)} volti noti")
        except Exception as e:
            logger.error(f"Errore caricamento volti noti: {e}")
    
    def add_known_face(self, image: np.ndarray, name: str) -> bool:
        try:
            encodings = face_recognition.face_encodings(image)
            if encodings:
                self.known_faces[name] = encodings[0]
                self.known_names.append(name)
                return True
            return False
        except Exception as e:
            logger.error(f"Errore aggiunta volto noto: {e}")
            return False
    
    def recognize_face(self, face_image: np.ndarray) -> Dict[str, Any]:
        try:
            if len(face_image.shape) == 3:
                rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = face_image
            
            face_encodings = face_recognition.face_encodings(rgb_image)
            
            if not face_encodings:
                return {"match": False, "name": "Unknown", "confidence": 0}
            
            matches = face_recognition.compare_faces(
                list(self.known_faces.values()), 
                face_encodings[0]
            )
            
            face_distances = face_recognition.face_distance(
                list(self.known_faces.values()), 
                face_encodings[0]
            )
            
            best_match_index = np.argmin(face_distances)
            
            if matches[best_match_index]:
                confidence = 1 - face_distances[best_match_index]
                return {
                    "match": True, 
                    "name": self.known_names[best_match_index], 
                    "confidence": float(confidence)
                }
            else:
                return {"match": False, "name": "Unknown", "confidence": 0}
                
        except Exception as e:
            logger.error(f"Errore riconoscimento volto: {e}")
            return {"match": False, "name": "Error", "confidence": 0}
