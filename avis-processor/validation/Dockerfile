FROM python:3.9-slim

WORKDIR /app

# Installer les dépendances
RUN pip install --no-cache-dir \
    pymongo \
    pandas \
    matplotlib \
    seaborn \
    tabulate

# Copier le script de validation
COPY ./verify_processing.py /app/verify_processing.py

# Définir l'entrée
ENTRYPOINT ["python", "/app/verify_processing.py"]