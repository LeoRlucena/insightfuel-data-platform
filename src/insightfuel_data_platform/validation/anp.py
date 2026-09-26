import logging

import polars as pl

logger = logging.getLogger(__name__)

COLUNAS_CRITICAS_ANP = {
    "Estado - Sigla",
    "Municipio",
    "CNPJ da Revenda",
    "Produto",
    "Data da Coleta",
    "Valor de Venda",
    "Unidade de Medida",
}

COLUNAS_CONHECIDAS_ANP = {
    "Regiao - Sigla",
    "Estado - Sigla",
    "Municipio",
    "Revenda",
    "CNPJ da Revenda",
    "Nome da Rua",
    "Numero Rua",
    "Complemento",
    "Bairro",
    "Cep",
    "Produto",
    "Data da Coleta",
    "Valor de Venda",
    "Valor de Compra",
    "Unidade de Medida",
    "Bandeira",
}

COLUNAS_ANALITICAS_ANP = {
    "Regiao - Sigla",
    "Revenda",
    "Bandeira",
}

COLUNAS_COMPLEMENTARES_ANP = {
    "Nome da Rua",
    "Numero Rua",
    "Complemento",
    "Bairro",
    "Cep",
    "Valor de Compra",
}

UFS_VALIDAS_BRASIL = {
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
    "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"
}

SCHEMA_SILVER_ANP = {
    "regiao": pl.String,
    "uf": pl.String,
    "municipio": pl.String,
    "revenda": pl.String,
    "cnpj_revenda": pl.String,
    "cep": pl.String,
    "produto": pl.String,
    "data_coleta": pl.Date,
    "valor_venda": pl.Decimal(precision=10, scale=2),
    "unidade_medida": pl.String,
    "bandeira": pl.String,
}

CAMPOS_OBRIGATORIOS_SILVER = {
    "uf",
    "municipio",
    "cnpj_revenda",
    "produto",
    "data_coleta",
    "valor_venda",
    "unidade_medida",
}

PRODUTOS_VALIDOS_ANP = {
    "DIESEL",
    "DIESEL S10",
    "ETANOL",
    "GASOLINA",
    "GASOLINA ADITIVADA",
    "GNV",
}

UNIDADES_VALIDAS_ANP = {
    "R$ / litro",
    "R$ / m³",
}

def validar_colunas_criticas(df: pl.DataFrame) -> None:
    """
    Valida se as colunas críticas estão presentes no DataFrame.

    Args:
        df (pl.DataFrame): DataFrame de entrada.

    Returns:
        None

    Raises:
        ValueError: Se alguma coluna crítica estiver ausente.
    """
    colunas_recebidas = set(df.columns)

    colunas_ausentes = (
        COLUNAS_CRITICAS_ANP - colunas_recebidas
    )

    if colunas_ausentes:
        raise ValueError(
            f"Colunas críticas ausentes: {sorted(colunas_ausentes)}"
        )

def identificar_colunas_desconhecidas(df: pl.DataFrame) -> set[str]:
    """
    Identifica se existem colunas novas no DataFrame

    Args:
        df (pl.DataFrame): DataFrame de entrada.

    Returns:
        set[str]: Conjunto das colunas desconhecidas.
    """   
    colunas_recebidas = set(df.columns)

    colunas_novas = (
        colunas_recebidas - COLUNAS_CONHECIDAS_ANP
    )

    return colunas_novas

def validar_colunas_desconhecidas(df: pl.DataFrame) -> None:
    """
    Valida se existem colunas novas no DataFrame

    Args:
        df (pl.DataFrame): DataFrame de entrada.

    Returns:
        None.
    """       
    colunas_desconhecidas = identificar_colunas_desconhecidas(df)

    if colunas_desconhecidas:
        logger.warning(
            "Colunas desconhecidas encontradas na fonte ANP: %s",
            sorted(colunas_desconhecidas),
        )

def validar_valores_categoricos(df: pl.DataFrame) -> None:
    """
    Valida se os produtos e unidades de medida da camada Silver
    pertencem aos conjuntos de valores conhecidos.

    Args:
        df (pl.DataFrame): DataFrame da camada Silver.

    Raises:
        ValueError: Se houver produtos ou unidades de medida desconhecidos.
    """
    produtos_recebidos = set(
        df["produto"]
        .drop_nulls()
        .unique()
        .to_list()
    )

    unidades_recebidas = set(
        df["unidade_medida"]
        .drop_nulls()
        .unique()
        .to_list()
    )

    produtos_invalidos = (
        produtos_recebidos - PRODUTOS_VALIDOS_ANP
    )

    unidades_invalidas = (
        unidades_recebidas - UNIDADES_VALIDAS_ANP
    )

    if produtos_invalidos or unidades_invalidas:
        raise ValueError(
            "Valores categóricos inválidos na camada Silver. "
            f"Produtos: {sorted(produtos_invalidos)}. "
            f"Unidades: {sorted(unidades_invalidas)}. "
        )

def validar_colunas_silver(df: pl.DataFrame) -> None:
    """
    Valida se as colunas do DataFrame estão de acordo com o schema da camada Silver.

    Args:
        df (pl.DataFrame): DataFrame de entrada.

    Returns:
        None

    Raises:
        ValueError: Se alguma coluna estiver ausente.
    """
    colunas_recebidas = set(df.columns)
    colunas_esperadas = set(SCHEMA_SILVER_ANP.keys())

    colunas_ausentes =  colunas_esperadas - colunas_recebidas
    colunas_inesperadas = colunas_recebidas - colunas_esperadas
    

    if colunas_ausentes or colunas_inesperadas:
        raise ValueError(
            "Colunas inválidas na camada Silver. "
            f"Ausentes: {sorted(colunas_ausentes)}. "
            f"Inesperadas: {sorted(colunas_inesperadas)}."
        )
    
def validar_tipos_silver(df: pl.DataFrame) -> None:
    """
    Valida se os tipos das colunas do DataFrame estão de acordo com o schema da camada Silver.

    Args:
        df (pl.DataFrame): DataFrame de entrada.

    Returns:
        None

    Raises:
        ValueError: Se alguma coluna estiver com tipo incorreto.
    """
    for coluna, tipo_esperado in SCHEMA_SILVER_ANP.items():
        if coluna in df.columns:
            tipo_real = df[coluna].dtype
            if tipo_real != tipo_esperado:
                raise ValueError(
                    f"Coluna '{coluna}' tem tipo incorreto. "
                    f"Esperado: {tipo_esperado}, Recebido: {tipo_real}"
                )

def validar_valor_venda(df: pl.DataFrame) -> None:
    """
    Valida os valores de venda da camada Silver.

    Args:
        df (pl.DataFrame): DataFrame da camada Silver.

    Raises:
        ValueError: Se houver valores de venda nulos ou não positivos.
    """
    valores_invalidos = df.filter(
        pl.col("valor_venda").is_null()
        | (pl.col("valor_venda") <= 0)
    )

    if valores_invalidos.height > 0:
        raise ValueError(
            f"Foram encontrados {valores_invalidos.height} "
            "registros com valor_venda inválido"
        )

def validar_campos_obrigatorios(df: pl.DataFrame) -> None:
    """
    Valida se os campos obrigatórios da camada Silver possuem valores nulos.

    Args:
        df (pl.DataFrame): DataFrame da camada Silver.

    Raises:
        ValueError: Se algum campo obrigatório possuir valores nulos.
    """
    campos_com_nulos = {}

    for coluna in CAMPOS_OBRIGATORIOS_SILVER:
        quantidade_nulos = df[coluna].null_count()

        if quantidade_nulos > 0:
            campos_com_nulos[coluna] = quantidade_nulos

    if campos_com_nulos:
        raise ValueError(
            "Campos obrigatórios com valores nulos na camada Silver: "
            f"{campos_com_nulos}"
        )

def validar_cnpj_silver(df: pl.DataFrame) -> None:
    """
    Valida o formato dos CNPJs da camada Silver.

    Args:
        df (pl.DataFrame): DataFrame da camada Silver.

    Raises:
        ValueError: Se houver CNPJs com formatos inválidos.
    """
    cnpjs_invalidos = df.filter(
        ~pl.col("cnpj_revenda").str.contains(r"^\d{14}$")
    )

    if cnpjs_invalidos.height > 0:
        raise ValueError(
            f"Foram encontrados {cnpjs_invalidos.height} "
            "registros com CNPJ em formato inválido"
        )

def validar_ufs_silver(df: pl.DataFrame) -> None:
    """
    Valida os códigos de UF da camada Silver.

    Args:
        df (pl.DataFrame): DataFrame da camada Silver.

    Raises:
        ValueError: Se houver códigos de UF inválidos.
    """
    ufs_recebidas = set(
        df["uf"]
        .drop_nulls()
        .unique()
        .to_list()
    )

    ufs_invalidas = ufs_recebidas - UFS_VALIDAS_BRASIL

    if ufs_invalidas:
        raise ValueError(
            "Foram encontrados códigos de UF inválidos na camada Silver: "
            f"{ufs_invalidas}"
        )

def validar_silver(df: pl.DataFrame) -> None:
    """
    Valida se o DataFrame está de acordo com o schema da camada Silver.

    Args:
        df (pl.DataFrame): DataFrame de entrada.

    Returns:
        None

    Raises:
        ValueError: Se alguma coluna estiver ausente ou com tipo incorreto.
    """
    validar_colunas_silver(df)
    validar_tipos_silver(df)
    validar_valor_venda(df)
    validar_valores_categoricos(df)
    validar_campos_obrigatorios(df)
    validar_cnpj_silver(df)
    validar_ufs_silver(df)