import sys
import os
import logging
import yaml
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from video_input_manager import VideoInputManager
from lip_tracker import LipTracker
from feature_extractor import FeatureExtractor
from config_manager import ConfigManager

def test_pipeline():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("pipeline_test.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Avvio test pipeline di riconoscimento labiale")
    
    config_path = "config/config.yaml"
    if not os.path.exists(config_path):
        logger.error("File di configurazione non trovato")
        return False
    
    try:
        config_manager = ConfigManager(config_path)
        config = config_manager.config
        logger.info("Configurazione caricata con successo")
    except Exception as e:
        logger.error(f"Errore caricamento configurazione: {e}")
        return False
    
    try:
        video_manager = VideoInputManager(config['video_processing'])
        lip_tracker = LipTracker(config['lip_tracking'])
        feature_extractor = FeatureExtractor(config['feature_extraction'])
        
        logger.info("Moduli inizializzati con successo")
    except Exception as e:
        logger.error(f"Errore inizializzazione moduli: {e}")
        return False
    
    stream_id = "test_webcam"
    if not video_manager.add_stream(stream_id, 0, "webcam"):
        logger.error("Impossibile aggiungere stream webcam")
        return False
    
    video_manager.start_all_streams()
    logger.info("Acquisizione video avviata")
    
    test_duration = 30
    start_time = datetime.now()
    frames_processed = 0
    successful_detections = 0
    
    try:
        while (datetime.now() - start_time).total_seconds() < test_duration:
            frame_data = video_manager.get_frame(stream_id, timeout=1.0)
            if not frame_data:
                logger.warning("Nessun frame disponibile")
                continue
            
            frame = frame_data['frame']
            frames_processed += 1
            
            lip_landmarks = lip_tracker.detect_lips(frame, stream_id)
            
            if lip_landmarks:
                successful_detections += 1
                logger.info(f"Labbra rilevate (confidence: {lip_landmarks.confidence:.2f})")
                
                lip_roi = lip_tracker.extract_roi(frame, lip_landmarks)
                
                features = feature_extractor.extract_features(lip_roi)
                logger.info(f"Features estratte: {len(features)} dimensioni")
                
                if lip_landmarks.confidence > 0.5:
                    logger.info("Simulazione riconoscimento: 'test phrase'")
            
            if frames_processed % 5 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"Elapsed: {elapsed:.1}f, Frames: {frames_processed}, Detections: {successful_detections}")
    
    except KeyboardInterrupt:
        logger.info("Test interrotto dall'utente")
    except Exception as e:
        logger.error(f"Errore durante il test: {e}")
    finally:
        video_manager.stop_all_streams()
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        fps = frames_processed / elapsed_time if elapsed_time > 0 else 0
        success_rate = (successful_detections / frames_processed * 100) if frames_processed > 0 else 0
        
        logger.info("=" * 50)
        logger.info("RISULTATI TEST PIPELINE")
        logger.info("=" * 50)
        logger.info(f"Tempo totale: {elapsed_time:.2f} secondi")
        logger.info(f"Frame processati: {frames_processed}")
        logger.info(f"Rilevamenti riusciti: {successful_detections}")
        logger.info(f"FPS: {fps:.2f}")
        logger.info(f"Tasso di successo: {success_rate:.2f}%")
        logger.info("=" * 50)
        
        return successful_detections > 0

if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)
