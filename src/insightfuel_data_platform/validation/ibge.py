import polars as pl


SCHEMA_MUNICIPIOS_IBGE = {
    "codigo_ibge": pl.String,
    "municipio": pl.String,
    "uf": pl.String,
    "regiao": pl.String,
    "municipio_match": pl.String,
}


def validar_municipios_ibge(df: pl.DataFrame) -> None:
    '''
    Valida o DataFrame de municípios IBGE, verificando se o schema está correto, se não há valores nulos nos campos obrigatórios e se não há códigos IBGE duplicados.

    Args:
        df (pl.DataFrame): DataFrame contendo os dados de municípios IBGE.

    Raises:
        ValueError: Se o schema estiver incorreto, se houver valores nulos nos campos obrigatórios ou se houver códigos IBGE duplicados.

    Returns:
        None
    '''
    if df.schema != SCHEMA_MUNICIPIOS_IBGE:
        raise ValueError(
            f"Schema inválido para municípios IBGE.\n"
            f"Esperado: {SCHEMA_MUNICIPIOS_IBGE}\n"
            f"Recebido: {df.schema}"
        )

    if df.height == 0:
        raise ValueError("Dimensão de municípios IBGE está vazia.")

    campos_obrigatorios = [
        "codigo_ibge",
        "municipio",
        "uf",
        "regiao",
        "municipio_match",
    ]

    for coluna in campos_obrigatorios:
        if df[coluna].null_count() > 0:
            raise ValueError(
                f"Campo obrigatório '{coluna}' possui valores nulos."
            )

    codigos_duplicados = (
        df
        .group_by("codigo_ibge")
        .len()
        .filter(pl.col("len") > 1)
    )

    if codigos_duplicados.height > 0:
        raise ValueError(
            "Foram encontrados códigos IBGE duplicados."
        )