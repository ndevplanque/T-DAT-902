# Utiliser l'image Python officielle
FROM python:3.9

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'API
COPY . .

# Exposer le port utilisé par Flask
EXPOSE 5000

# Définir la commande de démarrage
CMD ["python", "api.py"]
