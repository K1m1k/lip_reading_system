#!/bin/bash

# Script di backup del sistema
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Creazione backup del sistema..."

mkdir -p $BACKUP_DIR

# Backup del database
pg_dump -h localhost -U lip_user -d lip_reading_db > $BACKUP_DIR/db_backup_$TIMESTAMP.sql

# Backup dei modelli e configurazioni
tar -czf $BACKUP_DIR/system_backup_$TIMESTAMP.tar.gz models/ config/ known_faces/

echo "Backup completato in $BACKUP_DIR/"
