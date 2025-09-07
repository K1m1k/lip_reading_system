import numpy as np
import tensorflow as tf
from typing import List, Dict, Any, Optional
import cv2
import logging
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

class FeatureExtractor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scaler = StandardScaler()
        self.feature_model = None
        self._initialize_feature_models()
    
    def _initialize_feature_models(self):
        feature_type = self.config.get('feature_type', 'geometric')
        
        if feature_type == 'deep' and self.config.get('use_pretrained', False):
            try:
                input_shape = self.config.get('input_shape', (100, 50, 3))
                
                self.feature_model = tf.keras.Sequential([
                    tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
                    tf.keras.layers.MaxPooling2D((2, 2)),
                    tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
                    tf.keras.layers.MaxPooling2D((2, 2)),
                    tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
                    tf.keras.layers.Flatten(),
                    tf.keras.layers.Dense(128, activation='relu'),
                    tf.keras.layers.Dropout(0.5)
                ])
                
                logger.info("Modello feature extraction CNN inizializzato")
                
            except Exception as e:
                logger.error(f"Errore inizializzazione modello feature extraction: {e}")
                self.feature_model = None
    
    def extract_features(self, lip_roi: np.ndarray, sequence_data: Optional[List[np.ndarray]] = None) -> np.ndarray:
        feature_type = self.config.get('feature_type', 'geometric')
        
        if feature_type == 'geometric':
            return self._extract_geometric_features(lip_roi)
        elif feature_type == 'deep':
            return self._extract_deep_features(lip_roi)
        elif feature_type == 'temporal' and sequence_data:
            return self._extract_temporal_features(sequence_data)
        else:
            return lip_roi.flatten()
    
    def _extract_geometric_features(self, lip_roi: np.ndarray) -> np.ndarray:
        features = []
        
        if len(lip_roi.shape) == 3:
            gray = cv2.cvtColor(lip_roi, cv2.COLOR_RGB2GRAY)
        else:
            gray = lip_roi
        
        if self.config.get('hog_features', True):
            hog_features = self._extract_hog_features(gray)
            features.extend(hog_features)
        
        if self.config.get('lbp_features', False):
            lbp_features = self._extract_lbp_features(gray)
            features.extend(lbp_features)
        
        if self.config.get('shape_features', True):
            shape_features = self._extract_shape_features(gray)
            features.extend(shape_features)
        
        return np.array(features)
    
    def _extract_hog_features(self, image: np.ndarray) -> List[float]:
        try:
            from skimage.feature import hog
            
            hog_features = hog(
                image, 
                orientations=8, 
                pixels_per_cell=(16, 16),
                cells_per_block=(1, 1), 
                visualize=False,
                feature_vector=True
            )
            
            return hog_features.tolist()
        except ImportError:
            logger.warning("scikit-image non installato, saltando HOG features")
            return []
        except Exception as e:
            logger.error(f"Errore estrazione HOG: {e}")
            return []
    
    def _extract_lbp_features(self, image: np.ndarray) -> List[float]:
        try:
            from skimage.feature import local_binary_pattern
            
            lbp = local_binary_pattern(image, P=8, R=1, method='uniform')
            hist, _ = np.histogram(lbp.ravel(), bins=np.arange(0, 10), range=(0, 9))
            hist = hist.astype("float")
            hist /= (hist.sum() + 1e-6)
            
            return hist.tolist()
        except ImportError:
            logger.warning("scikit-image non installato, saltando LBP features")
            return []
        except Exception as e:
            logger.error(f"Errore estrazione LBP: {e}")
            return []
    
    def _extract_shape_features(self, image: np.ndarray) -> List[float]:
        try:
            _, binary = cv2.threshold(image, 0.5, 1, cv2.THRESH_BINARY)
            binary = binary.astype(np.uint8)
            
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return [0.0] * 7
            
            largest_contour = max(contours, key=cv2.contourArea)
            moments = cv2.moments(largest_contour)
            hu_moments = cv2.HuMoments(moments)
            hu_moments = -np.sign(hu_moments) * np.log10(np.abs(hu_moments) + 1e-10)
            
            return hu_moments.flatten().tolist()
        except Exception as e:
            logger.error(f"Errore estrazione shape features: {e}")
            return [0.0] * 7
    
    def _extract_deep_features(self, lip_roi: np.ndarray) -> np.ndarray:
        if self.feature_model is None:
            logger.warning("Modello deep learning non disponibile, usando geometric features")
            return self._extract_geometric_features(lip_roi)
        
        try:
            if len(lip_roi.shape) == 2:
                processed = np.stack([lip_roi] * 3, axis=-1)
            else:
                processed = lip_roi
            
            input_shape = self.config.get('input_shape', (100, 50, 3))
            if processed.shape[:2] != input_shape[:2]:
                processed = cv2.resize(processed, (input_shape[1], input_shape[0]))
            
            processed = processed.astype(np.float32) / 255.0
            features = self.feature_model.predict(np.expand_dims(processed, axis=0), verbose=0)
            
            return features.flatten()
        except Exception as e:
            logger.error(f"Errore estrazione deep features: {e}")
            return self._extract_geometric_features(lip_roi)
    
    def _extract_temporal_features(self, sequence_data: List[np.ndarray]) -> np.ndarray:
        try:
            temporal_features = []
            
            for i in range(1, len(sequence_data)):
                diff = cv2.absdiff(sequence_data[i-1], sequence_data[i])
                temporal_features.append(diff.flatten())
            
            if temporal_features:
                return np.concatenate(temporal_features)
            else:
                return np.array([])
        except Exception as e:
            logger.error(f"Errore estrazione temporal features: {e}")
            return np.array([])
    
    def normalize_features(self, features: np.ndarray, fit: bool = False) -> np.ndarray:
        if fit:
            return self.scaler.fit_transform(features.reshape(1, -1)).flatten()
        else:
            return self.scaler.transform(features.reshape(1, -1)).flatten()
