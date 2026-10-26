# Corrección del servidor Flet Web (18-10-2026)

En FastAPI 0.145.0 se eliminó el parámetro `openapi_prefix`, pero Flet Web 1.0.4 sigue usándolo. Por ello, el servidor web falla con `TypeError: FastAPI.__init__() got an unexpected keyword argument 'openapi_prefix'`.

Se fijó `fastapi==0.144.0` tanto en `requirements.txt` como en `pyproject.toml` para evitar que se instale una versión incompatible.

Para corregir una instalación existente (PowerShell, dentro de la carpeta que contiene main.py):

```powershell
python -m pip install "fastapi==0.144.0"
python -m pip show fastapi
python -m pip check
flet run --web --port 8000 main.py
```

Si `flet` no se reconoce, utilizar el entorno `.venv` especificando `./.venv/Scripts/flet.exe` (ruta equivalente en Windows con barras invertidas).

No es necesario Docker para una prueba web local.

Este ajuste corrige la incompatibilidad conocida de dependencias; todavía es necesario validar la interfaz en el equipo de destino.
