import http.server
import socketserver
import threading
import logging

logger = logging.getLogger(__name__)

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')
        else:
            self.send_response(404)
            self.end_headers()

class HealthCheckServer:
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Avvia il server di health check"""
        try:
            self.server = socketserver.TCPServer(("", self.port), HealthCheckHandler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            logger.info(f"Server di health check avviato sulla porta {self.port}")
            return True
        except Exception as e:
            logger.error(f"Errore nell'avvio del server di health check: {e}")
            return False
    
    def stop(self):
        """Ferma il server di health check"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Server di health check arrestato")
