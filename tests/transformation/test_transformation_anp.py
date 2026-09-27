import polars as pl
import pytest

from insightfuel_data_platform.transformation.anp import transformar_anp_silver


def criar_registro_anp(**alteracoes) -> dict:
    registro = {
        "Regiao - Sigla": "S",
        "Estado - Sigla": "RS",
        "Municipio": "NOVO HAMBURGO",
        "Revenda": "POSTO TESTE",
        "CNPJ da Revenda": "01.234.567/0001-89",
        "Cep": "93.000-000",
        "Produto": "GASOLINA",
        "Data da Coleta": "15/01/2025",
        "Valor de Venda": "6,29",
        "Unidade de Medida": "R$ / litro",
        "Bandeira": "BRANCA",
    }

    registro.update(alteracoes)
    return registro

def test_transformar_anp_silver_normaliza_campos():
    df = pl.DataFrame([
        criar_registro_anp()
    ])

    resultado = transformar_anp_silver(df)

    assert resultado.height == 1
    assert resultado["cnpj_revenda"][0] == "01234567000189"
    assert resultado["cep"][0] == "93000000"
    assert resultado["data_coleta"].dtype == pl.Date
    assert resultado["valor_venda"].dtype == pl.Decimal(
        precision=10,
        scale=2,
    )

def test_transformar_anp_silver_normaliza_unidade_m3():
    df = pl.DataFrame([
        criar_registro_anp(
            Produto="GNV",
            **{"Unidade de Medida": "R$ / m3"},
        )
    ])

    resultado = transformar_anp_silver(df)

    assert resultado["unidade_medida"][0] == "R$ / m³"

def test_transformar_anp_silver_falha_sem_coluna_critica():
    registro = criar_registro_anp()
    del registro["Valor de Venda"]

    df = pl.DataFrame([registro])

    with pytest.raises(
        ValueError,
        match="Colunas críticas ausentes",
    ):
        transformar_anp_silver(df)

def test_transformar_anp_silver_aceita_coluna_opcional_ausente():
    registro = criar_registro_anp()
    del registro["Bandeira"]

    df = pl.DataFrame([registro])

    resultado = transformar_anp_silver(df)

    assert "bandeira" in resultado.columns
    assert resultado["bandeira"][0] is None

def test_transformar_anp_silver_remove_duplicata_exata():
    registro = criar_registro_anp()

    df = pl.DataFrame([
        registro,
        registro.copy(),
    ])

    resultado = transformar_anp_silver(df)

    assert resultado.height == 1

def test_transformar_anp_silver_preserva_observacoes_com_precos_diferentes():
    registro_1 = criar_registro_anp(
        **{"Valor de Venda": "6,29"}
    )

    registro_2 = criar_registro_anp(
        **{"Valor de Venda": "6,39"}
    )

    df = pl.DataFrame([
        registro_1,
        registro_2,
    ])

    resultado = transformar_anp_silver(df)

    assert resultado.height == 2
    assert resultado["valor_venda"].n_unique() == 2