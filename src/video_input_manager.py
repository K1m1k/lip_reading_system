import cv2
import numpy as np
from typing import Dict, Any, List, Union
import logging
from datetime import datetime
import threading
from queue import Queue
import time

logger = logging.getLogger(__name__)

class VideoInputManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.streams = {}
        self.buffer_queues = {}
        self.is_running = False
        self.threads = []
        
    def add_stream(self, stream_id: str, source: Any, stream_type: str = "webcam") -> bool:
        try:
            if stream_type == "webcam":
                cap = cv2.VideoCapture(int(source) if isinstance(source, str) and source.isdigit() else source)
            elif stream_type == "rtsp":
                cap = cv2.VideoCapture(source)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
                cap.set(cv2.CAP_PROP_FPS, 30)
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
            elif stream_type == "file":
                cap = cv2.VideoCapture(source)
            else:
                logger.error(f"Tipo stream non supportato: {stream_type}")
                return False
            
            if not cap.isOpened():
                logger.error(f"Impossibile aprire stream: {source}")
                return False
            
            self.streams[stream_id] = {
                'capture': cap,
                'type': stream_type,
                'source': source,
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            }
            
            self.buffer_queues[stream_id] = Queue(maxsize=self.config.get('buffer_size', 30))
            logger.info(f"Stream {stream_id} aggiunto: {source}")
            return True
            
        except Exception as e:
            logger.error(f"Errore aggiunta stream {stream_id}: {e}")
            return False
    
    def start_all_streams(self):
        self.is_running = True
        for stream_id in self.streams.keys():
            thread = threading.Thread(
                target=self._stream_worker, 
                args=(stream_id,),
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
            logger.info(f"Avviato worker per stream {stream_id}")
    
    def stop_all_streams(self):
        self.is_running = False
        for thread in self.threads:
            thread.join(timeout=2.0)
        
        for stream_id, stream_info in self.streams.items():
            stream_info['capture'].release()
        
        logger.info("Tutti gli stream fermati")
    
    def _stream_worker(self, stream_id: str):
        stream_info = self.streams[stream_id]
        cap = stream_info['capture']
        frame_count = 0
        
        while self.is_running:
            try:
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Frame non valido dallo stream {stream_id}")
                    time.sleep(0.1)
                    continue
                
                processed_frame = self._preprocess_frame(frame, stream_info)
                
                frame_data = {
                    'frame': processed_frame,
                    'timestamp': datetime.now(),
                    'stream_id': stream_id,
                    'frame_count': frame_count,
                    'source_info': stream_info
                }
                
                if self.buffer_queues[stream_id].full():
                    try:
                        self.buffer_queues[stream_id].get_nowait()
                    except:
                        pass
                
                self.buffer_queues[stream_id].put(frame_data)
                frame_count += 1
                
                if stream_info['fps'] > 0:
                    time.sleep(1.0 / stream_info['fps'])
                else:
                    time.sleep(0.033)
                    
            except Exception as e:
                logger.error(f"Errore acquisizione frame da {stream_id}: {e}")
                time.sleep(1.0)
    
    def get_frame(self, stream_id: str, timeout: float = 1.0) -> Dict[str, Any]:
        try:
            return self.buffer_queues[stream_id].get(timeout=timeout)
        except:
            return None
    
    def get_all_frames(self, timeout: float = 0.1) -> Dict[str, Any]:
        frames = {}
        for stream_id in self.streams.keys():
            frame_data = self.get_frame(stream_id, timeout)
            if frame_data:
                frames[stream_id] = frame_data
        return frames
    
    def _preprocess_frame(self, frame: np.ndarray, stream_info: Dict[str, Any]) -> np.ndarray:
        if self.config.get('resize', True):
            target_size = self.config.get('target_size', (640, 480))
            frame = cv2.resize(frame, target_size)
        
        if self.config.get('normalize', True):
            frame = frame.astype(np.float32) / 255.0
            
        if self.config.get('convert_to_rgb', True):
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
        return frame
    
    def get_stream_info(self, stream_id: str) -> Dict[str, Any]:
        return self.streams.get(stream_id, {})
    
    def list_streams(self) -> List[str]:
        return list(self.streams.keys())
