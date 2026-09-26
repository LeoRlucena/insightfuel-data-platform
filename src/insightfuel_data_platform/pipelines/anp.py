from pathlib import Path

import polars as pl

from insightfuel_data_platform.ingestion.anp import (
    carregar_particao,
    extrair_metadados_particao,
)
from insightfuel_data_platform.transformation.anp import (
    transformar_anp_silver,
    enriquecer_com_codigo_ibge,
)

from insightfuel_data_platform.storage.parquet import (
    construir_caminho_silver,
    salvar_parquet,
    construir_caminho_gold_precos_mensais,
)

from insightfuel_data_platform.validation.anp import validar_silver

from insightfuel_data_platform.validation.gold import validar_gold_precos_mensais


from insightfuel_data_platform.aggregation.anp import agregar_precos_mensais_municipio

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

def publicar_gold_precos_mensais(
    df_gold: pl.DataFrame,
    pasta_gold: Path,
) -> list[Path]:
    """
    Publica a Gold de preços mensais particionada por ano.

    Args:
        df_gold (pl.DataFrame): DataFrame da Gold de preços mensais.
        pasta_gold (Path): Pasta base da camada Gold.
    
    Raises:
        ValueError: Se alguma validação falhar.

    Returns:
        list[Path]: Lista de caminhos dos arquivos Parquet publicados.
    """
    caminhos_publicados = []

    anos = (
        df_gold["ano_mes"]
        .dt.year()
        .unique()
        .sort()
        .to_list()
    )

    for ano in anos:
        df_ano = df_gold.filter(
            pl.col("ano_mes").dt.year() == ano
        )

        caminho = construir_caminho_gold_precos_mensais(
            pasta_gold,
            ano,
        )

        salvar_parquet(
            df_ano,
            caminho,
        )

        caminhos_publicados.append(caminho)

    return caminhos_publicados

def construir_gold_precos_mensais(
    pasta_silver: Path,
    pasta_gold: Path,
    df_municipios: pl.DataFrame,
) -> list[Path]:
    """
    Constrói e publica a Gold de preços mensais por município e produto.

    Args:
        pasta_silver (Path): Diretório das partições Silver da ANP.
        pasta_gold (Path): Diretório de destino da Gold.
        df_municipios (pl.DataFrame): Dimensão oficial de municípios do IBGE.

    Returns:
        list[Path]: Caminhos das partições Gold publicadas.
    """
    arquivos_silver = sorted(
        pasta_silver.rglob("*.parquet")
    )

    if not arquivos_silver:
        raise FileNotFoundError(
            f"Nenhuma partição Silver encontrada em: {pasta_silver}"
        )

    df_silver = pl.concat([
        pl.read_parquet(arquivo)
        for arquivo in arquivos_silver
    ])

    df_enriquecido = enriquecer_com_codigo_ibge(
        df_silver,
        df_municipios,
    )

    df_gold = agregar_precos_mensais_municipio(
        df_enriquecido
    )

    validar_gold_precos_mensais(
        df_gold
    )

    return publicar_gold_precos_mensais(
        df_gold,
        pasta_gold,
    )