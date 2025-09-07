import asyncio
import logging
from enhanced_lip_reading_system import EnhancedLipReadingSystem
from monitoring import MonitoringServer, SystemMonitor
from health_check import HealthCheckServer
import signal

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - trace_id=%(trace_id)s',
        handlers=[
            logging.FileHandler("system.log"),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("Avvio del Sistema Avanzato di Riconoscimento Labiale - Versione Enterprise")

    system = None
    try:
        system = EnhancedLipReadingSystem(config_path="config/config.yaml")
        
        monitoring_server = MonitoringServer(port=9090)
        monitoring_server.start()
        
        system_monitor = SystemMonitor(interval=5)
        system_monitor.start()
        
        health_check = HealthCheckServer(port=8080)
        health_check.start()
        
        await system.start_processing()

        logger.info("Sistema in esecuzione. Premi Ctrl+C per fermare.")
        
        # Gestione graceful shutdown
        def signal_handler(sig, frame):
            logger.info("Interruzione rilevata, arresto in corso...")
            asyncio.create_task(shutdown())
            
        async def shutdown():
            if system:
                await system.stop_processing()
            logger.info("Sistema arrestato.")
            exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Mantieni il processo attivo
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.critical(f"Errore fatale: {e}", exc_info=True)
    finally:
        if system:
            await system.stop_processing()
        logger.info("Sistema arrestato.")

if __name__ == "__main__":
    asyncio.run(main())
