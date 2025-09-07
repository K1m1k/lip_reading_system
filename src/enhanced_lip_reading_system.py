python

import cv2
import numpy as np
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading
from queue import Queue

from config_manager import ConfigManager
from video_input_manager import VideoInputManager
from lip_tracker import LipTracker
from feature_extractor import FeatureExtractor
from face_capture import FaceCaptureModule
from lip_reading_model import LipReadingModel
from face_recognition import FaceRecognitionSystem
from database import DatabaseManager
from message_broker import MessageBroker
from encryption import DataEncryptor
from secret_manager import SecretManager

logger = logging.getLogger(__name__)

class EnhancedLipReadingSystem:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        
        # Gestione sicura delle credenziali
        self.secret_manager = SecretManager(self.config)
        
        # Componenti del sistema
        self.db = DatabaseManager(self.config['database'])
        self.message_broker = MessageBroker(self.config['message_broker'])
        
        # Crittografia con chiavi sicure
        encryption_key = self.secret_manager.get_encryption_key()
        signature_key = self.secret_manager.get_signature_key()
        self.encryptor = DataEncryptor(encryption_key, signature_key)
        
        self.face_recognition = FaceRecognitionSystem(
            self.config['face_recognition']['model_type'],
            self.config['face_recognition']['known_faces_path']
        )
        self.lip_reader = LipReadingModel(self.config['model'])
        
        self.video_manager = VideoInputManager(self.config['video_processing'])
        self.lip_tracker = LipTracker(self.config['lip_tracking'])
        self.feature_extractor = FeatureExtractor(self.config['feature_extraction'])
        self.face_capture = FaceCaptureModule({'face_margin': 20})
        
        self.result_queue = Queue()
        self.is_running = False
        self.processing_threads = []
        
        self.blacklist = self.db.get_blacklist()
        logger.info(f"Caricate {len(self.blacklist)} frasi in blacklist")
        
        self._setup_video_sources()
    
    def _setup_video_sources(self):
        video_sources = self.config.get('video_sources', [])
        
        for source_config in video_sources:
            if source_config.get('enabled', False):
                self.video_manager.add_stream(
                    source_config['id'],
                    source_config['source'],
                    source_config['type']
                )
                logger.info(f"Stream {source_config['id']} configurato: {source_config['source']}")
    
    def start_processing(self):
        self.is_running = True
        self.video_manager.start_all_streams()
        
        for stream_id in self.video_manager.list_streams():
            thread = threading.Thread(
                target=self._process_stream,
                args=(stream_id,),
                daemon=True
            )
            thread.start()
            self.processing_threads.append(thread)
            logger.info(f"Avviato processing per stream {stream_id}")
    
    def _process_stream(self, stream_id: str):
        sequence_buffer = []
        sequence_length = self.config['model'].get('sequence_length', 30)
        
        while self.is_running:
            try:
                frame_data = self.video_manager.get_frame(stream_id, timeout=1.0)
                if not frame_data:
                    continue
                
                frame = frame_data['frame']
                lip_landmarks = self.lip_tracker.detect_lips(frame, stream_id)
                
                if lip_landmarks and lip_landmarks.confidence > 0.5:
                    lip_roi = self.lip_tracker.extract_roi(frame, lip_landmarks)
                    
                    features = self.feature_extractor.extract_features(lip_roi)
                    sequence_buffer.append(features)
                    
                    if len(sequence_buffer) > sequence_length:
                        sequence_buffer.pop(0)
                    
                    if len(sequence_buffer) == sequence_length:
                        predicted_text, confidence = self.lip_reader.predict(sequence_buffer)
                        
                        if predicted_text and confidence > self.config['model'].get('confidence_threshold', 0.7):
                            self._process_detection(
                                predicted_text, 
                                confidence, 
                                frame, 
                                stream_id,
                                frame_data['timestamp']
                            )
                
            except Exception as e:
                logger.error(f"Errore processing stream {stream_id}: {e}")
    
    def _process_detection(self, phrase: str, confidence: float, frame: np.ndarray, 
                          camera_id: str, timestamp: datetime):
        try:
            if any(bl_phrase in phrase.lower() for bl_phrase in self.blacklist):
                logger.warning(f"Frase blacklist rilevata: {phrase} (confidence: {confidence})")
                
                face_image = self.face_capture.capture_face(frame)
                face_match = {"match": False, "name": "Unknown", "confidence": 0}
                
                if face_image is not None:
                    face_match = self.face_recognition.recognize_face(face_image)
                
                temp_dir = self.config['paths'].get('temp_faces', '/tmp')
                frame_path = self._save_temp_image(frame, temp_dir, camera_id, timestamp, 'frame')
                face_path = self._save_temp_image(face_image, temp_dir, camera_id, timestamp, 'face') if face_image else None
                
                encrypted_frame_path = None
                encrypted_face_path = None
                
                if self.config['encryption'].get('enabled', False):
                    if frame_path:
                        encrypted_frame_path = self.encryptor.encrypt_image(frame_path)
                    if face_path:
                        encrypted_face_path = self.encryptor.encrypt_image(face_path)
                
                signature_data = f"{phrase}{timestamp}{camera_id}"
                signature = self.encryptor.generate_signature(signature_data)
                
                detection_data = {
                    'phrase': phrase,
                    'confidence': float(confidence),
                    'camera_id': camera_id,
                    'location': self._get_stream_location(camera_id),
                    'timestamp': timestamp,
                    'frame_path': encrypted_frame_path or frame_path,
                    'face_path': encrypted_face_path or face_path,
                    'encrypted': self.config['encryption'].get('enabled', False),
                    'signature': signature,
                    'face_match': face_match
                }
                
                detection_id = self.db.save_detection(detection_data)
                
                if detection_id:
                    detection_data['id'] = detection_id
                    self.message_broker.publish_detection(detection_data)
                    self.result_queue.put(detection_data)
                    
                    if face_match.get('match', False):
                        logger.warning(
                            f"RILEVATO VOLTO CONOSCIUTO: {face_match['name']} "
                            f"ha pronunciato: {phrase}"
                        )
                
                self._cleanup_temp_files([frame_path, face_path])
                
        except Exception as e:
            logger.error(f"Errore processamento detection: {e}")
    
    def _save_temp_image(self, image: np.ndarray, base_path: str, camera_id: str, 
                        timestamp: datetime, image_type: str) -> Optional[str]:
        try:
            if not os.path.exists(base_path):
                os.makedirs(base_path)
                
            filename = f"{camera_id}_{image_type}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.jpg"
            filepath = os.path.join(base_path, filename)
            
            success = cv2.imwrite(filepath, image)
            return filepath if success else None
            
        except Exception as e:
            logger.error(f"Errore salvataggio immagine temporanea: {e}")
            return None
    
    def _get_stream_location(self, stream_id: str) -> str:
        for source in self.config.get('video_sources', []):
            if source['id'] == stream_id:
                return source.get('location', 'unknown')
        return 'unknown'
    
    def _cleanup_temp_files(self, file_paths: List[str]):
        for path in file_paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.warning(f"Impossibile eliminare file temporaneo {path}: {e}")
    
    def add_to_blacklist(self, phrase: str) -> bool:
        success = self.db.add_to_blacklist(phrase)
        if success:
            self.blacklist = self.db.get_blacklist()
        return success
    
    def stop_processing(self):
        self.is_running = False
        self.video_manager.stop_all_streams()
        
        for thread in self.processing_threads:
            thread.join(timeout=5)
            
        self.message_broker.close()
        logger.info("Sistema di riconoscimento fermato")
    
    def _process_results(self):
        """Elabora i risultati in arrivo dalla coda"""
        while self.is_running:
            try:
                result = self.result_queue.get(timeout=1.0)
                if result:
                    # Qui puoi implementare ulteriore elaborazione dei risultati
                    logger.info(f"Risultato elaborato: {result['phrase']}")
            except:
                continue

