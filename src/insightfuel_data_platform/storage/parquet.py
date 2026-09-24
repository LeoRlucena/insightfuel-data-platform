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