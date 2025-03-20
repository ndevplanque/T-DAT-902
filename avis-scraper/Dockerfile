FROM python:3.9-slim

WORKDIR /app

# Installation des outils de compilation nécessaires
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installation explicite de NumPy d'abord, puis des autres dépendances
RUN pip install --no-cache-dir numpy==1.24.3 && \
    pip install --no-cache-dir cython==0.29.34

# Copier les requirements.txt sans pandas
COPY requirements.txt .

# Installer les autres dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Installer pandas séparément après numpy
RUN pip install --no-cache-dir pandas==2.0.3

# Installer les nouvelles dépendances
RUN pip install --no-cache-dir tqdm

# Copier le script de scraping
COPY scraper.py .

# Créer un répertoire pour les logs
RUN mkdir -p /app/logs

# Exécuter le script de scraping au démarrage du conteneur
CMD ["python", "scraper.py"]