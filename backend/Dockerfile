# Utilisation d'une image Python légère
FROM python:3.11-slim-bookworm

# Évite la génération de fichiers .pyc et permet l'affichage direct des logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Installation des dépendances système nécessaires (ex: pour chromadb ou sqlite)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copie d'abord les dépendances pour profiter du cache Docker
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste du backend
COPY backend/ ./backend/

# Création du dossier data si nécessaire et génération de la DB
RUN mkdir -p backend/data && \
    python backend/scripts/build_db.py

# Port exposé par FastAPI (par défaut 8000)
EXPOSE 8000

# Commande de lancement (on utilise le host 0.0.0.0 pour Docker)
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
