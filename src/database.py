import psycopg2
from psycopg2.extras import RealDictCursor, Json
import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = self._create_connection()
        self._init_db()
    
    def _create_connection(self):
        try:
            conn = psycopg2.connect(
                host=self.config['host'],
                database=self.config['name'],
                user=self.config['user'],
                password=self.config['password'],
                port=self.config['port'],
                sslmode=self.config.get('ssl_mode', 'prefer')
            )
            return conn
        except Exception as e:
            logger.error(f"Errore connessione database: {e}")
            raise
    
    def _init_db(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS blacklist (
                        id SERIAL PRIMARY KEY,
                        phrase TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT DEFAULT 'system'
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS detections (
                        id SERIAL PRIMARY KEY,
                        phrase TEXT NOT NULL,
                        confidence FLOAT NOT NULL,
                        camera_id TEXT NOT NULL,
                        location TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        frame_path TEXT,
                        face_path TEXT,
                        encrypted BOOLEAN DEFAULT FALSE,
                        signature TEXT,
                        processed BOOLEAN DEFAULT FALSE,
                        face_match JSONB
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS known_faces (
                        id SERIAL PRIMARY KEY,
                        person_id TEXT NOT NULL,
                        person_name TEXT NOT NULL,
                        face_encoding JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                """)
                
                self.connection.commit()
                logger.info("Database inizializzato con successo")
                
        except Exception as e:
            logger.error(f"Errore inizializzazione database: {e}")
            self.connection.rollback()
    
    def add_to_blacklist(self, phrase: str, created_by: str = 'system') -> bool:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO blacklist (phrase, created_by) VALUES (%s, %s) ON CONFLICT (phrase) DO NOTHING",
                    (phrase, created_by)
                )
                self.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Errore aggiunta blacklist: {e}")
            return False
    
    def get_blacklist(self) -> List[str]:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT phrase FROM blacklist")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Errore recupero blacklist: {e}")
            return []
    
    def save_detection(self, detection_data: Dict[str, Any]) -> Optional[int]:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO detections 
                    (phrase, confidence, camera_id, location, timestamp, frame_path, face_path, encrypted, signature, face_match)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    detection_data['phrase'],
                    detection_data['confidence'],
                    detection_data.get('camera_id', 'unknown'),
                    detection_data.get('location', 'unknown'),
                    detection_data.get('timestamp', datetime.now()),
                    detection_data.get('frame_path'),
                    detection_data.get('face_path'),
                    detection_data.get('encrypted', False),
                    detection_data.get('signature'),
                    Json(detection_data.get('face_match', {}))
                ))
                
                detection_id = cursor.fetchone()[0]
                self.connection.commit()
                return detection_id
        except Exception as e:
            logger.error(f"Errore salvataggio rilevamento: {e}")
            self.connection.rollback()
            return None
    
    def get_detections(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM detections 
                    ORDER BY timestamp DESC 
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Errore recupero rilevamenti: {e}")
            return []

    def is_in_blacklist(self, phrase: str) -> bool:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT EXISTS(SELECT 1 FROM blacklist WHERE phrase = %s)",
                    (phrase,)
                )
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Errore verifica blacklist: {e}")
            return False
