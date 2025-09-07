import time
import logging
import prometheus_client as prom
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily
from flask import Response, request
import threading
import psutil
import GPUtil
import uuid
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# Context variable per il trace ID
trace_id_ctx = ContextVar('trace_id', default=None)

# Metriche Prometheus
PROCESSING_LATENCY = prom.Histogram(
    'lip_recognition_processing_latency_seconds', 
    'Tempo di elaborazione del riconoscimento labiale',
    ['source_id', 'location']
)

FRAME_PROCESSING_RATE = prom.Counter(
    'lip_recognition_frame_processing_total',
    'Totale frame elaborati',
    ['source_id', 'location']
)

DETECTION_SUCCESS_RATE = prom.Counter(
    'lip_recognition_detection_success_total',
    'Totale rilevamenti riusciti',
    ['source_id', 'location']
)

DETECTION_FAILURE_RATE = prom.Counter(
    'lip_recognition_detection_failure_total',
    'Totale rilevamenti falliti',
    ['source_id', 'location', 'reason']
)

SYSTEM_CPU_USAGE = prom.Gauge(
    'lip_recognition_system_cpu_usage_percent',
    'Utilizzo CPU del sistema'
)

SYSTEM_MEMORY_USAGE = prom.Gauge(
    'lip_recognition_system_memory_usage_percent',
    'Utilizzo memoria del sistema'
)

GPU_UTILIZATION = prom.Gauge(
    'lip_recognition_gpu_utilization_percent',
    'Utilizzo GPU', 
    ['gpu_id', 'gpu_name']
)

GPU_MEMORY_USAGE = prom.Gauge(
    'lip_recognition_gpu_memory_usage_percent',
    'Utilizzo memoria GPU',
    ['gpu_id', 'gpu_name']
)

ACTIVE_THREADS = prom.Gauge(
    'lip_recognition_active_threads',
    'Numero di thread attivi'
)

class MonitoringServer:
    """Server Prometheus per l'esposizione delle metriche"""
    
    def __init__(self, port=9090):
        self.port = port
        self._server = None
    
    def start(self):
        """Avvia il server Prometheus"""
        try:
            prom.start_http_server(self.port)
            logger.info(f"Server Prometheus avviato sulla porta {self.port}")
            return True
        except Exception as e:
            logger.error(f"Errore nell'avvio del server Prometheus: {e}")
            return False
    
    def stop(self):
        """Ferma il server Prometheus"""
        # Non c'è un modo pulito per fermare il server Prometheus
        # In produzione, si potrebbe usare un processo separato
        pass

class SystemMonitor:
    """Monitoraggio delle risorse di sistema"""
    
    def __init__(self, interval=5):
        self.interval = interval
        self._running = False
        self._thread = None
    
    def start(self):
        """Avvia il monitoraggio delle risorse"""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Monitoraggio delle risorse di sistema avviato")
    
    def stop(self):
        """Ferma il monitoraggio delle risorse"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
    
    def _monitor_loop(self):
        """Loop di monitoraggio delle risorse"""
        while self._running:
            try:
                # CPU e memoria del sistema
                SYSTEM_CPU_USAGE.set(psutil.cpu_percent())
                SYSTEM_MEMORY_USAGE.set(psutil.virtual_memory().percent)
                
                # Thread attivi
                ACTIVE_THREADS.set(threading.active_count())
                
                # GPU
                try:
                    gpus = GPUtil.getGPUs()
                    for gpu in gpus:
                        GPU_UTILIZATION.labels(
                            gpu_id=str(gpu.id),
                            gpu_name=gpu.name
                        ).set(gpu.load * 100)
                        
                        GPU_MEMORY_USAGE.labels(
                            gpu_id=str(gpu.id),
                            gpu_name=gpu.name
                        ).set(gpu.memoryUtil * 100)
                except Exception as e:
                    logger.debug(f"Errore nel monitoraggio GPU: {e}")
                
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Errore nel monitoraggio delle risorse: {e}")
                time.sleep(self.interval)

class TracingMiddleware:
    """Middleware per le richieste HTTP"""
    
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        # Genera un trace ID unico
        trace_id = str(uuid.uuid4())
        trace_id_ctx.set(trace_id)
        
        # Aggiungi il trace ID ai log
        environ['trace_id'] = trace_id
        
        # Continua con la richiesta
        return self.app(environ, start_response)

def track_processing_latency(source_id, location, duration):
    """Traccia la latenza di elaborazione"""
    PROCESSING_LATENCY.labels(
        source_id=source_id,
        location=location
    ).observe(duration)

def increment_frame_processing(source_id, location):
    """Incrementa il contatore dei frame elaborati"""
    FRAME_PROCESSING_RATE.labels(
        source_id=source_id,
        location=location
    ).inc()

def increment_detection_success(source_id, location):
    """Incrementa il contatore dei rilevamenti riusciti"""
    DETECTION_SUCCESS_RATE.labels(
        source_id=source_id,
        location=location
    ).inc()

def increment_detection_failure(source_id, location, reason):
    """Incrementa il contatore dei rilevamenti falliti"""
    DETECTION_FAILURE_RATE.labels(
        source_id=source_id,
        location=location,
        reason=reason
    ).inc()
