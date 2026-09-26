# InsightFuel Data Platform

Plataforma de dados desenvolvida para análise dos preços de combustíveis
no Brasil a partir dos dados públicos disponibilizados pela ANP.

O projeto foi desenvolvido como parte da disciplina de Tecnologia de
Armazenamento de Dados e implementa um pipeline utilizando Apache Airflow,
Python, Polars e Parquet.

## Objetivo

Construir um pipeline de dados capaz de realizar a ingestão, transformação,
validação e agregação dos dados históricos de preços de combustíveis,
preparando-os para análises posteriores.

## Arquitetura

O projeto utiliza uma arquitetura dividida em três camadas:

- **Bronze:** dados obtidos da fonte original.
- **Silver:** dados tratados, padronizados e validados.
- **Gold:** dados agregados para consumo analítico.

## Pipeline

O pipeline principal é orquestrado pelo Apache Airflow:

baixar_anp → processar_anp ─┐
                            ├→ construir_gold
             processar_ibge ┘

## Tecnologias

- Python
- Polars
- Apache Airflow
- Parquet
- HTTPX
- Docker
- uv