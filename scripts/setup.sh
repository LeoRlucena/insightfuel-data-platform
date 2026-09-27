#!/usr/bin/env bash

set -e

echo "========================================"
echo " InsightFuel Data Platform - Setup"
echo "========================================"

echo
echo "[0/4] Verificando configuração do ambiente..."

if [ ! -f .env ]; then
    echo "Arquivo .env não encontrado. Criando configuração local..."

    cat > .env <<EOF
AIRFLOW_UID=$(id -u)
FERNET_KEY=
EOF

    echo "Arquivo .env criado."
fi

echo
echo "[1/4] Sincronizando ambiente Python..."
uv sync

echo
echo "[2/4] Construindo as imagens Docker..."
docker compose build

echo
echo "[3/4] Inicializando o Apache Airflow..."
docker compose run --rm airflow-init

echo
echo "[4/4] Iniciando os serviços..."
docker compose up -d

echo
echo "========================================"
echo " Ambiente iniciado com sucesso!"
echo "========================================"
echo

docker compose ps