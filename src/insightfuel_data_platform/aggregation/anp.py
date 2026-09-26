import polars as pl

def agregar_precos_mensais_municipio(
    df: pl.DataFrame,
) -> pl.DataFrame:
    """
    Agrega os preços da ANP mensalmente por município e produto.

    Args:
        df (pl.DataFrame): Dados Silver da ANP enriquecidos com código IBGE.

    Returns:
        pl.DataFrame: Preços mensais agregados por município e produto.
    """
    return (
        df
        .with_columns(
            pl.col("data_coleta")
            .dt.truncate("1mo")
            .alias("ano_mes")
        )
        .group_by([
            "ano_mes",
            "codigo_ibge",
            "municipio",
            "uf",
            "regiao",
            "produto",
        ])
        .agg(
            pl.col("valor_venda")
            .mean()
            .cast(pl.Float64)
            .alias("preco_medio"),

            pl.col("valor_venda")
            .median()
            .cast(pl.Float64)
            .alias("preco_mediano"),

            pl.col("valor_venda")
            .min()
            .cast(pl.Float64)
            .alias("preco_minimo"),

            pl.col("valor_venda")
            .max()
            .cast(pl.Float64)
            .alias("preco_maximo"),

            pl.col("valor_venda")
            .std()
            .cast(pl.Float64)
            .alias("desvio_padrao"),

            pl.len()
            .alias("qtd_coletas"),
        )
        .sort([
            "ano_mes",
            "codigo_ibge",
            "produto",
        ])
    )