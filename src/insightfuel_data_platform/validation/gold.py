import polars as pl

SCHEMA_GOLD_PRECOS_MENSAIS = {
    "ano_mes": pl.Date,
    "codigo_ibge": pl.String,
    "municipio": pl.String,
    "uf": pl.String,
    "regiao": pl.String,
    "produto": pl.String,
    "preco_medio": pl.Float64,
    "preco_mediano": pl.Float64,
    "preco_minimo": pl.Float64,
    "preco_maximo": pl.Float64,
    "desvio_padrao": pl.Float64,
    "qtd_coletas": pl.UInt32,
}

CAMPOS_OBRIGATORIOS_GOLD = {
    "ano_mes",
    "codigo_ibge",
    "municipio",
    "uf",
    "regiao",
    "produto",
    "preco_medio",
    "preco_mediano",
    "preco_minimo",
    "preco_maximo",
    "qtd_coletas",
}

def validar_schema_gold(df: pl.DataFrame) -> None:
    """
    Valida as colunas e os tipos da Gold de preços mensais.

    Args:
        df (pl.DataFrame): DataFrame a ser validado.

    Raises:
        ValueError: Se o schema do DataFrame não corresponder ao esperado.
    
    Returns:
        None
    """
    if df.schema != SCHEMA_GOLD_PRECOS_MENSAIS:
        raise ValueError(
            "Schema inválido na Gold de preços mensais. "
            f"Esperado: {SCHEMA_GOLD_PRECOS_MENSAIS}. "
            f"Recebido: {df.schema}."
        )

def validar_granularidade_gold(df: pl.DataFrame) -> None:
    """
    Valida a unicidade da granularidade da Gold.

    Args:
        df (pl.DataFrame): DataFrame a ser validado.

    Raises:
        ValueError: Se houver combinações duplicadas na granularidade da Gold.

    Returns:
        None
    """
    duplicados = (
        df
        .group_by([
            "ano_mes",
            "codigo_ibge",
            "produto",
        ])
        .len()
        .filter(pl.col("len") > 1)
    )

    if duplicados.height > 0:
        raise ValueError(
            f"Foram encontradas {duplicados.height} "
            "combinações duplicadas na granularidade da Gold."
        )

def validar_campos_obrigatorios_gold(
    df: pl.DataFrame,
) -> None:
    """
    Valida se os campos obrigatórios da Gold possuem valores nulos.

    Args:
        df (pl.DataFrame): DataFrame a ser validado.

    Raises:
        ValueError: Se algum campo obrigatório possuir valores nulos.
    
    Returns:
        None
    """ 
    campos_com_nulos = {}

    for coluna in CAMPOS_OBRIGATORIOS_GOLD:
        quantidade_nulos = df[coluna].null_count()

        if quantidade_nulos > 0:
            campos_com_nulos[coluna] = quantidade_nulos

    if campos_com_nulos:
        raise ValueError(
            "Campos obrigatórios com valores nulos na Gold: "
            f"{campos_com_nulos}"
        )

def validar_metricas_gold(df: pl.DataFrame) -> None:
    """
    Valida as métricas da Gold de preços mensais.

    Args:
        df (pl.DataFrame): DataFrame a ser validado.    

    Raises:
        ValueError: Se alguma métrica possuir valores inválidos.
    
    Returns:
        None
    """
    invalidos = df.filter(
        (pl.col("preco_medio") <= 0)
        | (pl.col("preco_mediano") <= 0)
        | (pl.col("preco_minimo") <= 0)
        | (pl.col("preco_maximo") <= 0)
        | (pl.col("preco_minimo") > pl.col("preco_maximo"))
        | (pl.col("qtd_coletas") <= 0)
    )

    if invalidos.height > 0:
        raise ValueError(
            f"Foram encontrados {invalidos.height} "
            "registros com métricas inválidas na Gold."
        )

def validar_gold_precos_mensais(
    df: pl.DataFrame,
) -> None:
    """
    Executa as validações da Gold de preços mensais.

    Args:
        df (pl.DataFrame): DataFrame a ser validado.

    Raises:
        ValueError: Se alguma validação falhar.
    
    Returns:
        None
    """
    validar_schema_gold(df)
    validar_granularidade_gold(df)
    validar_campos_obrigatorios_gold(df)
    validar_metricas_gold(df)