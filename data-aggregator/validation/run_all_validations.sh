#!/bin/bash

# Créer les sous-répertoires nécessaires
mkdir -p /app/results/avis
mkdir -p /app/results/properties

echo "=== Validation des avis (MongoDB) ==="
export OUTPUT_DIR=/app/results/avis
python /app/aggregation_validator.py

echo ""
echo "=== Validation des propriétés (PostgreSQL) ==="
export OUTPUT_DIR=/app/results/properties
python /app/properties_aggregation_validator.py

echo ""
echo "=== Validation terminée ==="