FROM python:3.9-slim

WORKDIR /app

COPY validate_data.py .
# Installation explicite de NumPy d'abord, puis des autres dépendances
RUN pip install --no-cache-dir numpy==1.24.3 && \
    pip install --no-cache-dir cython==0.29.34
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "validate_data.py"]