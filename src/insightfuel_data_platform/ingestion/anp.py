from pathlib import Path
import polars as pl

import shutil
from zipfile import ZipFile
from pathlib import Path
from zipfile import ZipFile

import httpx

URL_BASE_ANP_AUTOMOTIVOS = (
    "https://www.gov.br/anp/pt-br/centrais-de-conteudo/"
    "dados-abertos/arquivos/shpc/dsas/ca"
)

def construir_url_particao(ano: int, semestre: int) -> str:
    '''
    Constrói a URL para download do arquivo de preços mensais da ANP para um dado ano e semestre.

    Args:
        ano (int): Ano do arquivo a ser baixado.
        semestre (int): Semestre do arquivo a ser baixado (1 ou 2).

    Returns:
        str: URL completa para download do arquivo.
    '''
    if semestre not in (1, 2):
        raise ValueError(
            f"Semestre inválido: {semestre}. Esperado 1 ou 2."
        )

    return (
        f"{URL_BASE_ANP_AUTOMOTIVOS}/"
        f"ca-{ano}-{semestre:02d}.zip"
    )

def baixar_particao_anp(
    ano: int,
    semestre: int,
    pasta_bronze: Path,
) -> Path:
    pasta_particao = (
        pasta_bronze
        / f"ano={ano}"
        / f"semestre={semestre}"
    )

    arquivos_existentes = list(
        pasta_particao.glob("*.csv")
    )

    if arquivos_existentes:
        return arquivos_existentes[0]

    url = construir_url_particao(
        ano,
        semestre,
    )

    pasta_particao.mkdir(
        parents=True,
        exist_ok=True,
    )

    caminho_zip = pasta_particao / "download.tmp.zip"

    timeout = httpx.Timeout(
        connect=10.0,
        read=120.0,
        write=30.0,
        pool=10.0,
    )

    try:
        with httpx.stream(
            "GET",
            url,
            timeout=timeout,
            follow_redirects=True,
        ) as response:
            response.raise_for_status()

            with caminho_zip.open("wb") as arquivo:
                for bloco in response.iter_bytes():
                    arquivo.write(bloco)

        with ZipFile(caminho_zip) as arquivo_zip:
            arquivos_csv = [
                nome
                for nome in arquivo_zip.namelist()
                if nome.lower().endswith(".csv")
            ]

            if len(arquivos_csv) != 1:
                raise ValueError(
                    f"Esperado exatamente 1 CSV em {url}, "
                    f"encontrados: {arquivos_csv}"
                )

            nome_no_zip = arquivos_csv[0]
            nome_csv = Path(nome_no_zip).name
            caminho_csv = pasta_particao / nome_csv

            with arquivo_zip.open(nome_no_zip) as origem:
                with caminho_csv.open("wb") as destino:
                    shutil.copyfileobj(origem, destino)

        return caminho_csv

    finally:
        caminho_zip.unlink(missing_ok=True)
        
def baixar_particoes_anp(
    pasta_bronze: Path,
    anos: range = range(2023, 2026),
) -> list[Path]:
    '''
    Baixa todas as partições de dados da ANP para os anos e semestres especificados.

    Args:
        pasta_bronze (Path): Caminho da pasta onde os dados serão armazenados.
        anos (range, optional): Intervalo de anos para os quais os dados devem ser baixados. Padrão é range(2023, 2026).

    Returns:
        list[Path]: Lista de caminhos dos arquivos CSV baixados.
    '''
    arquivos = []

    for ano in anos:
        for semestre in (1, 2):
            arquivo = baixar_particao_anp(
                ano,
                semestre,
                pasta_bronze,
            )
            arquivos.append(arquivo)

    return arquivos

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