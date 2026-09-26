from pathlib import Path

import polars as pl

def salvar_parquet(df: pl.DataFrame, caminho: Path) -> None:
    """
    Salva um DataFrame em formato Parquet.

    Args:
        df (pl.DataFrame): DataFrame a ser salvo.
        caminho (Path): Caminho do arquivo Parquet de destino.
    """
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(caminho)

def construir_caminho_silver(
        pasta_silver: Path,
        ano: int,
        semestre: int
) -> Path:
    """
    Constrói o caminho completo para o arquivo Parquet na camada Silver.

    Args:
        pasta_silver (Path): Pasta base da camada Silver.
        ano (int): Ano da partição.
        semestre (int): Semestre da partição.

    Returns:
        Path: Caminho completo para o arquivo Parquet na camada Silver.
    """
    return pasta_silver / f"ano={ano}" / f"semestre={semestre}" / "dados.parquet"

def construir_caminho_gold_precos_mensais(
    pasta_gold: Path,
    ano: int,
) -> Path:
    """
    Constrói o caminho completo para o arquivo Parquet na camada Gold de preços mensais.

    Args:
        pasta_gold (Path): Pasta base da camada Gold.
        ano (int): Ano da partição.

    Returns:
        Caminho completo para o arquivo Parquet na camada Gold de preços mensais.
    """
    return (
        pasta_gold
        / f"ano={ano}"
        / "dados.parquet"
    )