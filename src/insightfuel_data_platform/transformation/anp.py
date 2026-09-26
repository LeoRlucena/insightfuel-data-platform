import polars as pl

from insightfuel_data_platform.validation.anp import (
    validar_colunas_desconhecidas,
    validar_colunas_criticas,
)

from insightfuel_data_platform.utils.text import normalizar_texto

MAPEAMENTO_COLUNAS_ANP = {
    "Regiao - Sigla": "regiao",
    "Estado - Sigla": "uf",
    "Municipio": "municipio",
    "Revenda": "revenda",
    "CNPJ da Revenda": "cnpj_revenda",
    "Cep": "cep",
    "Produto": "produto",
    "Data da Coleta": "data_coleta",
    "Valor de Venda": "valor_venda",
    "Unidade de Medida": "unidade_medida",
    "Bandeira": "bandeira",
}

def selecionar_e_renomear_colunas(df: pl.DataFrame) -> pl.DataFrame:
    """
    Seleciona e renomeia as colunas do DataFrame de acordo com o mapeamento definido.

    Args:
        df (pl.DataFrame): DataFrame de entrada.

    Returns:
        pl.DataFrame: DataFrame com as colunas selecionadas e renomeadas.
    """
    return (
        df
        .select(list(MAPEAMENTO_COLUNAS_ANP.keys()))
        .rename(MAPEAMENTO_COLUNAS_ANP)
    )

def remover_linhas_vazias(df: pl.DataFrame) -> pl.DataFrame:
    """
    Remove linhas do DataFrame que possuem valores nulos em todas as colunas.

    Args:
        df (pl.DataFrame): DataFrame de entrada.

    Returns:
        pl.DataFrame: DataFrame sem linhas vazias.
    """
    return df.filter(
        ~pl.all_horizontal(
            pl.all()
            .is_null()
        )
    )

def remover_duplicatas_exatas(df: pl.DataFrame) -> pl.DataFrame:
    """
    Remove duplicatas exatas do DataFrame.

    Args:
        df (pl.DataFrame): DataFrame de entrada.

    Returns:
        pl.DataFrame: DataFrame sem duplicatas exatas.
    """
    return df.unique()

def normalizar_separador_decimal(
        df: pl.DataFrame,
        coluna: str,
) -> pl.DataFrame:
    """
        Normaliza o separador decimal de um DataFrame e coluna indicados.
            
        Args:
            df (pl.DataFrame): DataFrame de entrada. 
            coluna (str): Coluna a ser normalizada           
            
        Returns:
            pl.DataFrame: DataFrame com o separador normalizado.
    """
    return df.with_columns(
        pl.col(coluna).str.replace(",", ".")
    )

def converter_valor_venda(df: pl.DataFrame) -> pl.DataFrame:
    """
        Converte o valor de venda para Decimal
        
        Args:
            df (pl.DataFrame): DataFrame de entrada.            
        
        Returns:
            pl.DataFrame: DataFrame com o valor de venda normalizado.
    """
    return df.with_columns(
        pl.col("valor_venda")
        .cast(pl.Decimal(precision=10, scale=2))
    )

def normalizar_unidade_medida(df: pl.DataFrame) -> pl.DataFrame:
    """
        Normaliza a unidade de medida para o mesmo padrão
        
        Args:
            df (pl.DataFrame): DataFrame de entrada.            
        
        Returns:
            pl.DataFrame: DataFrame com a unidade de medida normalizada.
    """
    return df.with_columns(
        pl.col("unidade_medida").replace("R$ / m3", "R$ / m³")
    )

def converter_data_coleta(df: pl.DataFrame) -> pl.DataFrame:
    """
        Converte a data de coleta para Date
        
        Args:
            df (pl.DataFrame): DataFrame de entrada.            
        
        Returns:
            pl.DataFrame: DataFrame com a data normalizada.
    """
    return df.with_columns(
        pl.col("data_coleta").str.to_date(format="%d/%m/%Y")
    )

def manter_apenas_digitos(
        df: pl.DataFrame,
        coluna: str,
) -> pl.DataFrame:
    """
        Remove caractéres que não sejam dígitos do DataFrame e coluna indicados
    
        Args:
            df (pl.DataFrame): DataFrame de entrada.
            coluna (str): Coluna do DataFrame.
    
        Returns:
            pl.DataFrame: DataFrame com os dados normalizados.
        """
    return df.with_columns(
            pl.col(coluna).str.replace_all(r"\D", "")
        )    

def normalizar_cnpj(df: pl.DataFrame) -> pl.DataFrame:
    """
    Remove formatação do CNPJ da Revenda.

    Args:
            df (pl.DataFrame): DataFrame de entrada.
    
        Returns:
            pl.DataFrame: DataFrame com o CNPJ normalizado.
    """
    return manter_apenas_digitos(df, "cnpj_revenda")

def normalizar_cep(df: pl.DataFrame) -> pl.DataFrame:
    """
    Remove formatação do CEP.

    Args:
            df (pl.DataFrame): DataFrame de entrada.
    
        Returns:
            pl.DataFrame: DataFrame com o CEP normalizado.
    """
    return manter_apenas_digitos(df, "cep")    

def enriquecer_com_codigo_ibge(
    df_anp: pl.DataFrame,
    df_municipios: pl.DataFrame,
) -> pl.DataFrame:
    """
    Enriquece os dados da ANP com o código oficial do município do IBGE.

    Args:
        df_anp (pl.DataFrame): DataFrame da ANP.
        df_municipios (pl.DataFrame): DataFrame de municípios do IBGE.

    Returns:
        pl.DataFrame: DataFrame da ANP enriquecido com o código do IBGE.
    """
    df_anp = df_anp.with_columns(
        pl.col("municipio")
        .map_elements(
            normalizar_texto,
            return_dtype=pl.String,
        )
        .alias("municipio_match")
    )

    return (
        df_anp
        .join(
            df_municipios,
            on=["uf", "municipio_match"],
            how="left",
            suffix="_ibge",
        )
        .rename({
            "municipio_ibge": "municipio_oficial",
            "regiao_ibge": "regiao_oficial",
        })
        .drop([
            "municipio",
            "regiao",
        ])
        .rename({
            "municipio_oficial": "municipio",
            "regiao_oficial": "regiao",
        })
        .drop("municipio_match")
    )

def transformar_anp_silver(df: pl.DataFrame) -> pl.DataFrame:
    """
    Transforma dados brutos da ANP para o padrão da camada Silver.

    Args:
        df (pl.DataFrame): DataFrame da camada Bronze.

    Returns:
        pl.DataFrame: DataFrame transformado para a camada Silver.
    """
    validar_colunas_criticas(df)
    validar_colunas_desconhecidas(df)
    
    resultado = remover_linhas_vazias(df)
    resultado = remover_duplicatas_exatas(resultado)
    resultado = selecionar_e_renomear_colunas(resultado)
    resultado = normalizar_cnpj(resultado)
    resultado = normalizar_cep(resultado)
    resultado = converter_data_coleta(resultado)
    resultado = normalizar_separador_decimal(resultado, "valor_venda")
    resultado = converter_valor_venda(resultado)
    resultado = normalizar_unidade_medida(resultado)

    return resultado