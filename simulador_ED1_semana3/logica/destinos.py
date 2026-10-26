"""Normalización de nombres de zonas, compartida por rutas y logística."""
import unicodedata


def clave_destino(nombre):
    """Ignora mayúsculas/minúsculas, tildes y espacios repetidos."""
    texto = unicodedata.normalize("NFKD", " ".join(str(nombre).split()))
    return "".join(letra for letra in texto if not unicodedata.combining(letra)).casefold()
