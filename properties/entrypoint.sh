#!/bin/bash
# Script d'entrée pour l'import des données immobilières DVF
set -e

echo "Démarrage de l'import des données DVF..."
python3 csv_treatment.py
echo "Import des données DVF terminé"
