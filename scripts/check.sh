#!/usr/bin/env bash

set -e

echo "========================================"
echo " InsightFuel Data Platform - Checks"
echo "========================================"

echo
echo "[1/2] Executando testes..."
uv run pytest -v

echo
echo "[2/2] Verificando qualidade do código..."
uv run ruff check .

echo
echo "========================================"
echo " Todos os checks foram concluídos."
echo "========================================"

