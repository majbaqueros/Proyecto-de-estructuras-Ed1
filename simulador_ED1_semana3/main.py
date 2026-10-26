"""Punto de entrada soportado por Vercel y por uvicorn local.
Vercel detecta la variable de nivel superior `app` (FastAPI).
"""
from app import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=False)
