#!/usr/bin/env bash
set -euo pipefail

# Start Docker Desktop if needed, then pull and start containers from docker-compose.yaml

if ! command -v docker >/dev/null 2>&1; then
  echo "Erreur : la commande 'docker' est introuvable. Installez Docker Desktop d'abord."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Démarrage de Docker Desktop..."
  open -a Docker

  echo -n "Attente que Docker soit prêt"
  while ! docker info >/dev/null 2>&1; do
    printf '.'
    sleep 2
  done
  echo
fi

compose_cmd="docker compose"
if ! $compose_cmd version >/dev/null 2>&1; then
  compose_cmd="docker-compose"
fi

echo "Pull des images Docker définies dans docker-compose.yaml..."
$compose_cmd -f docker-compose.yaml pull

echo "Démarrage des conteneurs en arrière-plan..."
$compose_cmd -f docker-compose.yaml up --scale spark-worker=3 -d

echo "Conteneurs démarrés. Interfaces principales :"
echo "- Spark Master UI : http://localhost:8080"
echo "- Spark Application UI : http://localhost:4040 (lorsqu'un job tourne)"

