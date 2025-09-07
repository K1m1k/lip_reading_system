#!/bin/bash

echo "Rotazione delle chiavi di crittografia..."

# Esegui lo script di rotazione chiavi
python -c "
from src.secret_manager import SecretManager
from src.config_manager import ConfigManager

config = ConfigManager().config
secret_manager = SecretManager(config)
secret_manager.rotate_encryption_key()

print('Chiavi ruotate con successo')
"

echo "Rotazione completata!"
