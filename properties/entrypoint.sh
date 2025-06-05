#!/bin/bash
set -e

echo "🚀 Lancement du traitement CSV avec PySpark"
python3 csv_treatment.py
echo "✅ Traitement terminé avec succès"
