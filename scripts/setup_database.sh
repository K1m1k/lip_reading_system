#!/bin/bash

echo "Configurazione del database PostgreSQL..."

sudo -u postgres psql -c "CREATE DATABASE lip_reading_db;"
sudo -u postgres psql -c "CREATE USER lip_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE lip_reading_db TO lip_user;"

echo "Database configurato con successo!"
