import logging
import multiprocessing
import queue
import threading
import time
import cv2
import numpy as np
import tensorflow as tf
from typing import List, Dict, Any, Optional, Callable
from collections import deque

logger = logging.getLogger(__name__)

class FrameBuffer:
    """Buffer circolare per i frame video"""
    
    def __init__(self, max_size=30):
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.Lock()
    
    def add_frame(self, frame):
        """Aggiunge un frame al buffer"""
        with self.lock:
            self.buffer.append(frame)
    
    def get_frames(self, num_frames=1):
        """Ottiene un numero specifico di frame dal buffer"""
        with self.lock:
            if len(self.buffer) < num_frames:
                return None
            return list(self.buffer)[-num_frames:]
    
    def clear(self):
        """Pulisce il buffer"""
        with self.lock:
            self.buffer.clear()

class GPUAccelerator:
    """Gestisce l'accelerazione GPU per il modello"""
    
    def __init__(self, model_path, config):
        self.model_path = model_path
        self.config = config
        self.model = None
        self._init_gpu()
        self._load_model()
    
    def _init_gpu(self):
        """Configura l'use della GPU"""
        try:
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                # Imposta la crescita dinamica della memoria GPU
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                
                # Imposta il numero massimo di GPU da utilizzare
                max_gpus = self.config.get('max_gpus', len(gpus))
                tf.config.set_visible_devices(gpus[:max_gpus], 'GPU')
                
                logger.info(f"Configurata GPU con {max_gpus} dispositivi")
            else:
                logger.info("Nessuna GPU disponibile, esecuzione su CPU")
        except Exception as e:
            logger.warning(f"Errore nella configurazione GPU: {e}")
    
    def _load_model(self):
        """Carica il modello LipNet con supporto GPU"""
        try:
            # Configura il parallelismo per il modello
            num_cores = multiprocessing.cpu_count()
            tf.config.threading.set_intra_op_parallelism_threads(num_cores)
            tf.config.threading.set_inter_op_parallelism_threads(num_cores)
            
            # Carica il modello
            self.model = tf.keras.models.load_model(self.model_path, compile=False)
            logger.info(f"Modello LipNet caricato con successo da {self.model_path}")
            
            # Ottimizza per GPU
            if tf.config.experimental.list_physical_devices('GPU'):
                self.model = tf.keras.models.clone_model(self.model)
                self.model.compile()
                
        except Exception as e:
            logger.critical(f"Errore nel caricamento del modello: {e}", exc_info=True)
            raise
    
    def predict(self, sequence):
        """Esegue la predizione con ottimizzazione GPU"""
        try:
            # Processa la sequenza in batch se possibile
            if len(sequence) > 1:
                # Processa in batch
                batch_size = self.config.get('frame_batch_size', 8)
                results = []
                
                for i in range(0, len(sequence), batch_size):
                    batch = sequence[i:i+batch_size]
                    batch = self._preprocess_batch(batch)
                    batch_results = self.model.predict(batch)
                    results.extend(batch_results)
                
                return results
            else:
                # Processa singolo frame
                processed = self._preprocess_batch(sequence)
                return self.model.predict(processed)
                
        except Exception as e:
            logger.error(f"Errore durante la predizione GPU: {e}")
            return None
    
    def _preprocess_batch(self, frames):
        """Preprocessa un batch deiframe per il modello"""
        processed = []
        for frame in frames:
            # Preprocessa il frame come nel codice originale
            if len(frame.shape) == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            frame = cv2.resize(frame, (100, 50))
            processed.append(frame)
        
        # Converti in array numpy e normalizza
        processed = np.array(processed) / 255.0
        processed = np.expand_dims(processed, axis=-1)  # Aggiungi canale
        return processed

class ProcessingWorker(multiprocessing.Process):
    """Worker per l'elaborazione parallela"""
    
    def __init__(self, worker_id, input_queue, output_queue, config, model_path):
        super().__init__()
        self.worker_id = worker_id
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.config = config
        self.model_path = model_path
        self.running = True
    
    def run(self):
        """Esegue il worker"""
        logger.info(f"Worker {self.worker_id} avviato")
        
        # Inizializza il modello GPU per questo worker
        gpu_accelerator = GPUAccelerator(self.model_path, self.config)
        
        while self.running:
            try:
                # Prendi un lavoro dalla coda
                job = self.input_queue.get(timeout=1)
                
                if job is None:  # Segnale di arresto
                    break
                
                source_id, location, frames = job
                
                # Esegui l'elaborazione
                start_time = time.time()
                result = self._process_frames(gpu_accelerator, frames)
                duration = time.time() - start_time
                
                # Invia il risultato
                self.output_queue.put((source_id, location, result, duration))
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Errore nel worker {self.worker_id}: {e}", exc_info=True)
        
        logger.info(f"Worker {self.worker_id} terminato")
    
    def _process_frames(self, gpu_accelerator, frames):
        """Elabora i frame con il modello"""
        try:
            # Estrai le feature labiali
            lip_features = self._extract_lip_features(frames)
            
            # Esegui la predizione
            prediction = gpu_accelerator.predict(lip_features)
            
            return prediction
            
        except Exception as e:
            logger.error(f"Errore nell'elaborazione dei frame: {e}")
            return None
    
    def _extract_lip_features(self, frames):
        """Estrae le feature labiali dai frame"""
        # Implementazione semplificata - in produzione usare il modulo lip_tracker
        return frames

class DistributedProcessingSystem:
    """Sistema di elaborazione distribuita per il riconoscimento labiale"""
    
    def __init__(self, config, model_path):
        self.config = config
        self.model_path = model_path
        self.workers = []
        self.input_queues = {}
        self.output_queue = multiprocessing.Queue()
        self._init_workers()
        self._start_monitoring()
    
    def _init_workers(self):
        """Inizializza i worker di elaborazione"""
        num_workers = self.config.get('max_threads', 4)
        logger.info(f"Inizializzazione di {num_workers} worker di elaborazione")
        
        for i in range(num_workers):
            input_queue = multiprocessing.Queue()
            self.input_queues[f"worker_{i}"] = input_queue
            
            worker = ProcessingWorker(
                worker_id=i,
                input_queue=input_queue,
                output_queue=self.output_queue,
                config=self.config,
                model_path=self.model_path
            )
            self.workers.append(worker)
            worker.start()
    
    def _start_monitoring(self):
        """Avvia il monitoraggio delle prestazioni"""
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
    
    def _monitoring_loop(self):
        """Loop di monitoraggio delle prestazioni"""
        while True:
            try:
                # Controlla lo stato delle code
                for worker_id, queue in self.input_queues.items():
                    logger.debug(f"Worker {worker_id} - Dimensione coda: {queue.qsize()}")
                
                # Controlla lo stato dell'output
                logger.debug(f"Dimensione coda output: {self.output_queue.qsize()}")
                
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Errore nel monitoraggio: {e}")
                time.sleep(5)
    
    def process_video_source(self, source_id, location, frame_buffer):
        """Avvia l'elaborazione per una sorgente video"""
        logger.info(f"Avvio elaborazione per sorgente {source_id} - {location}")
        
        # Determina quale worker usare (round-robin semplice)
        worker_id = hash(source_id) % len(self.workers)
        worker_name = f"worker_{worker_id}"
        input_queue = self.input_queues[worker_name]
        
        # Avvia un thread per monitorare il buffer e inviare i lavori
        processing_thread = threading.Thread(
            target=self._processing_loop,
            args=(source_id, location, frame_buffer, input_queue),
            daemon=True
        )
        processing_thread.start()
    
    def _processing_loop(self, source_id, location, frame_buffer, input_queue):
        """Loop di elaborazione per una sorgente video"""
        buffer_size = self.config.get('buffer_size', 30)
        
        while True:
            try:
                # Ottieni i frame dal buffer
                frames = frame_buffer.get_frames(buffer_size)
                
                if frames is not None:
                    # Invia il lavoro al worker
                    input_queue.put((source_id, location, frames))
                
                time.sleep(0.01)  # Riduce il carico CPU
                
            except Exception as e:
                logger.error(f"Errore nel loop di elaborazione per {source_id}: {e}")
                time.sleep(1)
    
    def get_results(self, timeout=1):
        """Ottiene i risultati dall'elaborazione"""
        try:
            return self.output_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def shutdown(self):
        """Arresta tutti i worker"""
        logger.info("Arresto del sistema di elaborazione distribuita")
        
        # Invia segnale deiarresto a tutti i worker
        for queue in self.input_queues.values():
            queue.put(None)
        
        # Attende la terminazione dei worker
        for worker in self.workers:
            worker.join(timeout=5.0)
        
        logger.info("Sistema di elaborazione distribuita arrestato")
