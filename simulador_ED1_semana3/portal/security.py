"""Hash seguro de contraseñas y normalización de entrada."""
import re
import unicodedata
from argon2 import PasswordHasher, exceptions

_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)


def normalize_email(email):
    email = str(email or "").strip().casefold()
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("Ingresa un correo electrónico válido")
    return email


def normalize_place(name):
    name = " ".join(str(name or "").split())
    if not (2 <= len(name) <= 120):
        raise ValueError("La ubicación debe tener entre 2 y 120 caracteres")
    key = unicodedata.normalize("NFKD", name).casefold()
    key = "".join(char for char in key if not unicodedata.combining(char))
    return name, key


def hash_password(password):
    if len(password or "") < 12:
        raise ValueError("La contraseña debe tener al menos 12 caracteres")
    return _hasher.hash(password)


def check_password(digest, password):
    try:
        return _hasher.verify(digest, password)
    except (exceptions.VerifyMismatchError, exceptions.VerificationError, exceptions.InvalidHashError):
        return False
