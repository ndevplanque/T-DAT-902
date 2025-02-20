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

# Définir les variables d'environnement pour Flask
ENV FLASK_APP=api.py
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

# Définir la commande de démarrage
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
