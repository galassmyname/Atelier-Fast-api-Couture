#!/bin/sh
# Arrête le script à la première erreur
set -e

echo "Application des migrations..."
alembic upgrade head

echo "Initialisation (admin + catalogue)..."
python -m app.seed

echo "Démarrage de l'API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000