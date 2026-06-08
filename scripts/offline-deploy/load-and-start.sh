#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed. Install Docker first, then rerun this script."
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  echo "Docker Compose is not installed. Install the compose plugin or docker-compose first."
  exit 1
fi

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example."
  echo "Edit .env before production use: set PUBLIC_WEB_BASE_URL and JWT_SECRET."
fi

mkdir -p data/uploads data/reports

if [ -d "docker-images" ]; then
  shopt -s nullglob
  IMAGE_TARS=(docker-images/*.tar)
  if [ "${#IMAGE_TARS[@]}" -gt 0 ]; then
    for image_tar in "${IMAGE_TARS[@]}"; do
      echo "Loading ${image_tar} ..."
      docker load -i "${image_tar}"
    done
  else
    echo "docker-images exists, but no .tar image files were found."
  fi
else
  echo "No docker-images directory found. Images must already exist on this server."
fi

echo "Starting containers without building or pulling ..."
"${COMPOSE[@]}" up -d --no-build

echo
"${COMPOSE[@]}" ps
echo
echo "Open the system at the PUBLIC_WEB_BASE_URL configured in .env, usually http://SERVER_IP:8001"
