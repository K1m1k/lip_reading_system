# Sistema Avanzato di Riconoscimento Labiale - Versione Enterprise

Un sistema completo per il riconoscimento del parlato labiale con integrazione di blacklist, riconoscimento facciale e dashboard di monitoraggio.

## Funzionalità

- Riconoscimento labiale in tempo reale con supporto GPU
- Sistema di blacklist per frasi pericolose
- Riconoscimento facciale integrato con supporto CNN
- Crittografia AES-256 con gestione sicura delle chiavi (Vault/KMS)
- Dashboard web per monitoraggio con autenticazione JWT
- Notifiche in tempo reale tramite multiple sorgenti
- Supporto per multiple sorgenti video con elaborazione distribuita
- Monitoraggio avanzato con Prometheus e tracing distribuito
- Health check e metriche di performance

## Architettura

Il sistema è progettato con un'architettura modulare e scalabile:

+---------------------+ +---------------------+ +---------------------+
| Sorgenti Video | | Elaborazione | | Database & |
| (Webcam, RTSP, ecc)| ----> | Distribuita | ----> | Message Broker |
+---------------------+ | - Multiprocessing | | - RabbitMQ |
| - GPU Acceleration | | - Encryption |
+---------------------+ +---------------------+
| |
v v
+---------------------+ +---------------------+
| Monitoraggio | | Dashboard & |
| - Prometheus | | Alerting |
| - Grafana | | - Webhook |
+---------------------+ +---------------------+

## Installazione

1. Clona il repository
2. Installa le dipendenze: `pip install -r requirements.txt`
3. Configura il database: `./scripts/setup_database.sh`
4. Configura RabbitMQ: `./scripts/setup_rabbitmq.sh`
5. Scarica il modello: `./scripts/download_lipnet_model.sh`
6. Configura le variabili d'ambiente: `cp config/.env.example config/.env`
7. Avvia il sistema: `python src/main.py`

## Utilizzo

Accedi alla dashboard all'indirizzo http://localhost:5000 per monitorare i rilevamenti e gestire la blacklist.

## Deployment Cloud

### AWS ECS
```bash
./scripts/deploy_cloud.sh aws
