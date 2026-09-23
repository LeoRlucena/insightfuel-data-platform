from pathlib import Path
import polars as pl

def carregar_particao(caminho: Path) -> pl.DataFrame:
    return pl.read_csv(
        caminho,
        separator=";",
        schema_overrides={
            "CNPJ da Revenda": pl.String,
            "Cep": pl.String
        }
    )
    

def extrair_metadados_particao(arquivo: Path) -> dict:
    return {
        "semestre": int(arquivo.parent.name.split("=")[1]),
        "ano": int(arquivo.parent.parent.name.split("=")[1])
    }