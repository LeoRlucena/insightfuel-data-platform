from pathlib import Path

from insightfuel_data_platform.ingestion.ibge import baixar_municipios_ibge

from insightfuel_data_platform.storage.parquet import (
    construir_caminho_silver_municipios_ibge,
    salvar_parquet,
)
from insightfuel_data_platform.transformation.ibge import (
    transformar_municipios_ibge,
)
from insightfuel_data_platform.validation.ibge import (
    validar_municipios_ibge,
)

def processar_municipios_ibge(pasta_silver: Path) -> Path:
    '''
    Processa os dados de municípios IBGE, realizando as etapas de download, transformação, validação e salvamento em formato Parquet na camada Silver.

    Args:
        pasta_silver (Path): Caminho da pasta onde os dados processados serão salvos

    Returns:
        caminho_silver (Path): Caminho completo do arquivo Parquet salvo na camada Silver.
    '''
    df_bronze = baixar_municipios_ibge()

    df_silver = transformar_municipios_ibge(df_bronze)

    validar_municipios_ibge(df_silver)

    caminho_silver = construir_caminho_silver_municipios_ibge(
        pasta_silver
    )

    salvar_parquet(df_silver, caminho_silver)

    return caminho_silver