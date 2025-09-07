#!/bin/bash

echo "Configurazione di RabbitMQ..."

sudo rabbitmqctl add_user lip_reader reader_password
sudo rabbitmqctl set_user_tags lip_reader administrator
sudo rabbitmqctl set_permissions -p / lip_reader ".*" ".*" ".*"

echo "RabbitMQ configurato con successo!"
