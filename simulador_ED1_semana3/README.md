# Simulador ED1 · Estructuras de Datos y Logística · Semanas 1–3

Aplicación **Python + Flet** con arquitectura de presentación MVC, estructuras enlazadas construidas a mano y demostraciones para Windows, Web y pantallas táctiles Android.

## Funcionalidades

| Apartado | Qué muestra |
|---|---|
| **Estructuras** | Lista doble, `next`/`prev`, insertar/eliminar, deshacer/rehacer, validador y cálculo postfijo. |
| **Logística** | Cola de prioridad enlazada, despacho de paquetes y pila de historial. `1` es la mayor prioridad. |
| **Rutas** | Lista doblemente enlazada **circular** con vehículo en recorrido, botones paso atrás/adelante y animación asíncrona. |
| **Métricas** | Operaciones/s en ventana de 5s, duración por acción, memoria aproximada por nodo y benchmark O(1) vs O(n). |
| **Extras** | Bitácora Call Stack y Torres de Hanói del proyecto original. |

En teléfono se usa **barra de navegación inferior** y controles que se reordenan; en escritorio aparecen accesos superiores.

## Instalar / ejecutar

Requiere **Python 3.10+**, recomendado **3.12**. Para Windows abre CMD/PowerShell en esta carpeta:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\activate
pip install "flet[all]==1.0.4" pytest
python main.py
```

Para ejecutar con navegador:

```powershell
flet run --web --port 8000 main.py
```

Para pruebas unitarias:

```powershell
python -m pytest -q
```

## Guías adicionales

- [`docs/GUIA_DE_ENTREGA.md`](docs/GUIA_DE_ENTREGA.md): instalación detallada, distribución Windows, APK Android, web pública, lista de comprobación.
- [`docs/ANALISIS_TECNICO.md`](docs/ANALISIS_TECNICO.md): **diagrama de clases Mermaid**, tabla de complejidades e invariantes de punteros.
- [`docs/PRESENTACION.md`](docs/PRESENTACION.md): guion de exposición de 8 diapositivas.
- `presentacion_semana3.pptx`: diapositivas listas para adaptar.

## Directorios

```text
controlador/   operaciones MVC y estado del recorrido
estructuras/   nodos y punteros explícitos
logica/        logística y medidor de rendimiento
modelos/       entidades del dominio
vistas/        Flet, animaciones y navegación responsiva
pipeline/      validador, postfija y Hanói
tests/         pruebas del modelo y controladores
docs/          documentación y presentación
scripts/       ejecución y empaquetado Windows
```

**Notas:** No se incluyen EXE, APK ni URL de hosting pública ya compilados; se proveen scripts y configuración para construirlos en los sistemas correspondientes. Se conservan módulos de semanas previas y el archivo SQLite original; en Docker la base se usa en memoria para que usuarios públicos no compartan bitácoras. El tiempo y memoria indicados son mediciones en la capa Python y no reflejan todo el costo de Flet/Flutter.
