# Utilise une image Python légère (slim) pour économiser de l'espace
FROM python:3.12-slim

# Définit le dossier de travail à l'intérieur du conteneur
WORKDIR /app

# Copie d'abord le fichier des dépendances pour profiter du cache Docker
COPY requirements.txt .

# Installe les bibliothèques Python nécessaires
RUN pip install --no-cache-dir -r requirements.txt

# Copie le code de l'API
COPY app.py .

# Commande pour démarrer l'API sur le port 8000
# --host 0.0.0.0 permet au conteneur d'être accessible depuis l'extérieur
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
