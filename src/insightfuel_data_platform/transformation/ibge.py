import polars as pl

from insightfuel_data_platform.utils.text import normalizar_texto

def transformar_municipios_ibge(df: pl.DataFrame) -> pl.DataFrame:
    '''
    Transforma o DataFrame de municípios do IBGE, normalizando o nome dos municípios e selecionando colunas relevantes.

    Args:
        df (pl.DataFrame): DataFrame de entrada com os dados dos municípios.

    Returns:
        pl.DataFrame: DataFrame transformado com as colunas selecionadas e o nome dos municípios normalizado.
    '''
    return (
        df
        .select(
            pl.col("id")
            .cast(pl.String)
            .alias("codigo_ibge"),

            pl.col("nome")
            .alias("municipio"),

            pl.col("regiao-imediata")
            .struct.field("regiao-intermediaria")
            .struct.field("UF")
            .struct.field("sigla")
            .alias("uf"),

            pl.col("regiao-imediata")
            .struct.field("regiao-intermediaria")
            .struct.field("UF")
            .struct.field("regiao")
            .struct.field("nome")
            .alias("regiao"),
        )
        .with_columns(
            pl.col("municipio")
            .map_elements(
                normalizar_texto,
                return_dtype=pl.String,
            )
            .alias("municipio_match")
        )
    )