import unicodedata
import re

def normalizar_texto(texto: str | None) -> str | None:
    """
    Normaliza o texto removendo acentos, convertendo para maiúsculas e removendo caracteres especiais.

    Args:
        texto (str | None): Texto a ser normalizado.

    Returns:
        str | None: Texto normalizado ou None se o texto de entrada for None.
    """
    if texto is None:
        return None

    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = texto.upper()

    texto = re.sub(r"[^A-Z0-9 ]", "", texto)

    return texto
