from pathlib import Path
import polars as pl

def verificar_chave_candidata(df: pl.DataFrame) -> pl.DataFrame:
    duplicados = (
        df.select(
            "CNPJ da Revenda",
            "Produto",
            "Data da Coleta"
        )
        .filter(
            pl.col("CNPJ da Revenda").is_not_null() &
            pl.col("Produto").is_not_null() &
            pl.col("Data da Coleta").is_not_null()       
        )
        .group_by([
            "CNPJ da Revenda",
            "Produto",
            "Data da Coleta"
        ])
        .len()
        .filter(
            pl.col("len") > 1
        )
    )
    return duplicados

def analisar_particao(df: pl.DataFrame) -> dict:
    resultado = {        
        "total_linhas": df.height,
        "total_colunas": df.width,        
        "colunas": df.columns,
        "data_minima": df["Data da Coleta"].str.to_date(format="%d/%m/%Y").min(),
        "data_maxima": df["Data da Coleta"].str.to_date(format="%d/%m/%Y").max(),
        "produtos": df["Produto"].unique().sort().to_list(),
        "unidades_de_medida": df["Unidade de Medida"].unique().sort().to_list(),
        "colisoes_chave_candidata": verificar_chave_candidata(df).height,
        "duplicatas_exatas": quantidade_duplicatas_exatas(df),
        "linhas_vazias": quantidade_linhas_vazias(df),
        "nulos": quantidade_nulos(df),
    }
    return resultado

def maximo_casas_decimais(df: pl.DataFrame, coluna: str) -> int:
    return (
        df
        .select(
            pl.col(coluna)
            .str.split(".")
            .list.get(1, null_on_oob=True)
            .str.len_chars()
            .alias("casas_decimais")
            .fill_null(0)
            .max()
            .alias("maximo_casas_decimais")
        )
        .item()
    )   

def quantidade_nulos(df: pl.DataFrame) -> dict:
    nulos = df.null_count().to_dicts()[0]

    nulos_com_valores = {}

    for col, count in nulos.items():
        if count > 0:
            nulos_com_valores[col] = count
    return nulos_com_valores

def quantidade_duplicatas_exatas(df: pl.DataFrame) -> int:
    return df.height - df.unique().height

def quantidade_linhas_vazias(df: pl.DataFrame) -> int:
    return df.filter(
        pl.all_horizontal(
            pl.all().is_null()
        )
    ).height