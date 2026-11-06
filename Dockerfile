# Image Python légère
FROM python:3.12-slim

# Pas de fichiers .pyc, logs affichés immédiatement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# On installe d'abord les dépendances (étape mise en cache par Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Puis on copie le code
COPY . .

# Script de démarrage : migrations, seed, puis serveur
RUN chmod +x entrypoint.sh

EXPOSE 8000
CMD ["./entrypoint.sh"]