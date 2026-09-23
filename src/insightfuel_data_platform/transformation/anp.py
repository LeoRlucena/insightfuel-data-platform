import polars as pl

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

def normalizar_separador_decimal(
        df: pl.DataFrame,
        coluna: str,
) -> pl.DataFrame:
    """
        Converte separador decimal Brasileiro para padrão
            
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