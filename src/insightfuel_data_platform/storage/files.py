from pathlib import Path

def descobrir_csvs(pasta: Path) -> list[Path]:
    """
    Descobre todos os arquivos CSV em uma pasta específica.

    Args:
        pasta (Path): Caminho para a pasta onde os arquivos CSV estão localizados.

    Returns:
        list[Path]: Lista de caminhos para os arquivos CSV encontrados.
    """
    return sorted(pasta.rglob("*.csv"))