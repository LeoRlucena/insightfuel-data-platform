import httpx
import polars as pl


URL_MUNICIPIOS_IBGE = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
)


def baixar_municipios_ibge() -> pl.DataFrame:
    '''
    Baixa os dados de municípios do IBGE e retorna um DataFrame do Polars contendo as informações.

    Args: None

    Returns:
        pl.DataFrame: Um DataFrame do Polars com os dados dos municípios.
    '''
    response = httpx.get(
        URL_MUNICIPIOS_IBGE,
        timeout=30.0,
    )

    response.raise_for_status()

    dados = response.json()

    return pl.DataFrame(dados)