# Utiliser l'image Python officielle
FROM python:3.9

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application Streamlit
COPY . .

# Exposer le port utilisé par Streamlit
EXPOSE 8501

# Définir la commande de démarrage
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
