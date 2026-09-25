from pathlib import Path

import polars as pl

from insightfuel_data_platform.ingestion.anp import (
    carregar_particao,
    extrair_metadados_particao,
)
from insightfuel_data_platform.transformation.anp import (
    transformar_anp_silver,
)
from insightfuel_data_platform.validation.anp import (
    validar_silver,
)
from insightfuel_data_platform.storage.parquet import (
    construir_caminho_silver,
    salvar_parquet,
)

from insightfuel_data_platform.storage.files import descobrir_csvs

def processar_particao_anp(arquivo_bronze: Path, pasta_silver: Path) -> Path:
    """
    Processa uma partição de dados da ANP, realizando a transformação e validação dos dados.

    Args:
        arquivo_bronze (Path): Caminho para o arquivo de dados bruto (bronze).
        pasta_silver (Path): Caminho para a pasta onde os dados processados (silver) serão salvos.

    Returns: 
        Artefato de saída (Path): Caminho para o arquivo de dados processado (silver).
    """
    metadados = extrair_metadados_particao(arquivo_bronze)
    ano = metadados["ano"] 
    semestre = metadados["semestre"]

    df_bronze = carregar_particao(arquivo_bronze)
    df_silver = transformar_anp_silver(df_bronze)
    validar_silver(df_silver)

    caminho_silver = construir_caminho_silver(pasta_silver, ano, semestre)
    salvar_parquet(df_silver, caminho_silver)

    return caminho_silver

def processar_particoes_anp(pasta_bronze: Path, pasta_silver: Path) -> list[Path]:
    """
    Processa todas as partições de dados da ANP em uma pasta específica, realizando a transformação e validação dos dados.

    Args:
        pasta_bronze (Path): Caminho para a pasta onde os arquivos de dados brutos (bronze) estão localizados.
        pasta_silver (Path): Caminho para a pasta onde os dados processados (silver) serão salvos.

    Returns:
        list[Path]: Lista de caminhos para os arquivos de dados processados (silver).
    """
    arquivos_bronze = descobrir_csvs(pasta_bronze)
    caminhos_silver = []

    for arquivo_bronze in arquivos_bronze:
        metadados = extrair_metadados_particao(arquivo_bronze)
        ano = metadados["ano"]
        semestre = metadados["semestre"]
        caminho_silver = construir_caminho_silver(pasta_silver, ano, semestre)

        if caminho_silver.exists():
            continue
        
        caminho_silver = processar_particao_anp(arquivo_bronze, pasta_silver)
        caminhos_silver.append(caminho_silver)

    return caminhos_silver