#!/usr/bin/env bash

set -e

echo "========================================"
echo " InsightFuel Data Platform - Setup"
echo "========================================"

echo
echo "[1/4] Sincronizando ambiente Python..."
#!/usr/bin/env bash

set -e

echo "========================================"
echo " InsightFuel Data Platform - Setup"
echo "========================================"

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

chmod +x scripts/setup.sh