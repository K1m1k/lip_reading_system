#!/bin/bash

MODEL_DIR="./models"
mkdir -p $MODEL_DIR

echo "Scaricamento del modello LipNet (placeholder)..."

echo -e "hello\nworld\nsecurity\nalert\ndanger\nhelp\nstop\nrun\nfire\npolice" > $MODEL_DIR/vocabulary.txt
touch $MODEL_DIR/lipnet_model.h5

echo "Download completato. Modello e vocabolario salvati in $MODEL_DIR"
