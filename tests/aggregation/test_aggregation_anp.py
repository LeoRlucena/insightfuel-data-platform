from datetime import date
from decimal import Decimal

import polars as pl
import pytest

from insightfuel_data_platform.aggregation.anp import (
    agregar_precos_mensais_municipio,
)
from insightfuel_data_platform.validation.gold import (
    validar_gold_precos_mensais,
    validar_granularidade_gold,
)


def criar_dados_silver_enriquecidos() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "data_coleta": [
                date(2025, 1, 10),
                date(2025, 1, 20),
            ],
            "codigo_ibge": [
                "4313409",
                "4313409",
            ],
            "municipio": [
                "NOVO HAMBURGO",
                "NOVO HAMBURGO",
            ],
            "uf": ["RS", "RS"],
            "regiao": ["S", "S"],
            "produto": [
                "GASOLINA",
                "GASOLINA",
            ],
            "valor_venda": [
                Decimal("6.00"),
                Decimal("6.40"),
            ],
        },
        schema={
            "data_coleta": pl.Date,
            "codigo_ibge": pl.String,
            "municipio": pl.String,
            "uf": pl.String,
            "regiao": pl.String,
            "produto": pl.String,
            "valor_venda": pl.Decimal(
                precision=10,
                scale=2,
            ),
        },
    )


def test_agregacao_mensal_calcula_metricas_corretamente():
    df = criar_dados_silver_enriquecidos()

    resultado = agregar_precos_mensais_municipio(df)

    assert resultado.height == 1
    assert resultado["ano_mes"][0] == date(2025, 1, 1)
    assert resultado["preco_medio"][0] == pytest.approx(6.20)
    assert resultado["preco_mediano"][0] == pytest.approx(6.20)
    assert resultado["preco_minimo"][0] == pytest.approx(6.00)
    assert resultado["preco_maximo"][0] == pytest.approx(6.40)
    assert resultado["qtd_coletas"][0] == 2


def test_agregacao_mantem_produtos_separados():
    df = criar_dados_silver_enriquecidos()

    outra_observacao = df.head(1).with_columns(
        pl.lit("ETANOL").alias("produto"),
        pl.lit(Decimal("4.20"))
        .cast(pl.Decimal(precision=10, scale=2))
        .alias("valor_venda"),
    )

    resultado = agregar_precos_mensais_municipio(
        pl.concat([df, outra_observacao])
    )

    assert resultado.height == 2
    assert set(resultado["produto"].to_list()) == {
        "GASOLINA",
        "ETANOL",
    }


def test_gold_gerada_passa_nas_validacoes():
    df = criar_dados_silver_enriquecidos()

    resultado = agregar_precos_mensais_municipio(df)

    validar_gold_precos_mensais(resultado)


def test_validacao_detecta_granularidade_duplicada():
    df = criar_dados_silver_enriquecidos()

    gold = agregar_precos_mensais_municipio(df)
    gold_duplicada = pl.concat([gold, gold])

    with pytest.raises(
        ValueError,
        match="combinações duplicadas",
    ):
        validar_granularidade_gold(gold_duplicada)