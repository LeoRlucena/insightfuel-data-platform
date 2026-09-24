from pathlib import Path

import polars as pl

from insightfuel_data_platform.ingestion.anp import (
    carregar_particao,
    extrair_metadados_particao,
)
from insightfuel_data_platform.transformation.anp import (
    transformar_anp_silver,
)
from insightfuel_data_platform.validation.anp import (
    validar_silver,
)
from insightfuel_data_platform.storage.parquet import (
    construir_caminho_silver,
    salvar_parquet,
)

