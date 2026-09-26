from datetime import datetime
from pathlib import Path

from airflow.sdk import dag, task

from insightfuel_data_platform.pipelines.anp import (
    construir_gold_precos_mensais,
    processar_particoes_anp,
)
from insightfuel_data_platform.pipelines.ibge import (
    processar_municipios_ibge,
)


PASTA_BRONZE_ANP = Path(
    "/opt/airflow/data/bronze/anp/automotivos"
)

PASTA_SILVER_ANP = Path(
    "/opt/airflow/data/silver/anp/automotivos"
)

PASTA_SILVER = Path(
    "/opt/airflow/data/silver"
)

PASTA_GOLD = Path(
    "/opt/airflow/data/gold/anp/precos_mensais_municipio"
)

@dag(
    dag_id="insightfuel_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["insightfuel", "anp", "ibge"],
)
def insightfuel_pipeline():

    @task
    def processar_anp():
        caminhos = processar_particoes_anp(
            PASTA_BRONZE_ANP,
            PASTA_SILVER_ANP,
        )

        return [str(caminho) for caminho in caminhos]

    @task
    def processar_ibge():
        caminho = processar_municipios_ibge(
            PASTA_SILVER
        )

        return str(caminho)

    @task
    def construir_gold():
        caminhos = construir_gold_precos_mensais(
            PASTA_SILVER,
            PASTA_GOLD,
        )

        return [str(caminho) for caminho in caminhos]

    anp = processar_anp()
    ibge = processar_ibge()

    gold = construir_gold()

    [anp, ibge] >> gold


insightfuel_pipeline()