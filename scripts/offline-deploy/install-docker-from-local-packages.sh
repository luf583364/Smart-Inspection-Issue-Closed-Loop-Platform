#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PKG_ROOT="${REPO_ROOT}/docker-install"

if command -v docker >/dev/null 2>&1; then
  echo "Docker already exists:"
  docker version
  exit 0
fi

if [ -d "${PKG_ROOT}/deb" ] && compgen -G "${PKG_ROOT}/deb/*.deb" >/dev/null; then
  echo "Installing Docker from local deb packages ..."
  sudo dpkg -i "${PKG_ROOT}"/deb/*.deb
elif [ -d "${PKG_ROOT}/rpm" ] && compgen -G "${PKG_ROOT}/rpm/*.rpm" >/dev/null; then
  echo "Installing Docker from local rpm packages ..."
  if command -v dnf >/dev/null 2>&1; then
    sudo dnf localinstall -y "${PKG_ROOT}"/rpm/*.rpm
  else
    sudo yum localinstall -y "${PKG_ROOT}"/rpm/*.rpm
  fi
else
  echo "No local Docker packages found."
  echo "Put deb packages in docker-install/deb or rpm packages in docker-install/rpm, then rerun."
  exit 1
fi

sudo systemctl enable --now docker

echo "Docker installed:"
docker version
docker compose version || docker-compose version
