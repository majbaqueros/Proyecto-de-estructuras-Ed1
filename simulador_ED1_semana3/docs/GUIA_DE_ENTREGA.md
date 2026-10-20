# Guía de entrega, instalación y publicación del simulador ED1

## Preparación Windows 10/11 x64

1. Instala **Python 3.12 (64 bits)**. En VS Code abre la carpeta `ed1_semana3`.
2. En PowerShell, desde el directorio del proyecto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install "flet[all]==1.0.4" pytest
python -m pytest -q
python main.py
```

Si PowerShell restringe scripts, usa `cmd.exe` y `.venv\Scripts\activate.bat`, o `scripts\iniciar_escritorio_windows.bat`. Los scripts Windows crean el entorno en su primer uso.

## Web local (también para probar móvil)

```powershell
flet run --web --port 8000 main.py
```

Abre `http://localhost:8000`. Para acceder desde un teléfono **en la misma red**, inicia `flet run --web --host '*' --port 8000 main.py`, consulta la IP privada del equipo y abre `http://IP-DEL-PC:8000` desde el móvil. El firewall debe permitir el puerto; **no abras este puerto a Internet sin protección**.

## Publicación del simulador Web (servicio dinámico)

Se incluye `Dockerfile` para despliegue de un proceso Python + Flet con WebSockets. En un equipo con Docker:

```bash
docker build -t ed1-simulador .
docker run --rm -p 8000:8000 ed1-simulador
```

Comprueba `http://localhost:8000`. Para una URL pública, sube el repositorio o la imagen a un proveedor que soporte contenedores y WebSockets (por ejemplo un VPS con proxy inverso y HTTPS), configura el puerto del contenedor **8000** y un dominio/certificado SSL. No se ha publicado este ZIP en ningún servidor ni se suministra una URL pública ficticia.

La versión Docker establece `ED1_DB_PATH=:memory:` para **no guardar aportes de usuarios en una base SQLite compartida**; cada conexión a `DatabaseManager` es privada y temporal. Por defecto el programa local lee y escribe `proyecto_ed1.db` y la bitácora puede conservar datos del proyecto anterior. Un despliegue con persistencia requiere diseñar autenticación, separación de usuarios y almacenamiento permanente.

## Construcción de ejecutables

**Windows EXE** (sólo construible *en Windows*, 64 bits):

```powershell
flet build windows
```

Necesita Visual Studio con **Desarrollo de escritorio con C++**, Flutter/Flet CLI y espacio para las dependencias. Alternativa PyInstaller `flet pack main.py` (consultar ayuda instalada para opciones exactas). Ejecutar `scripts\construir_windows.bat` después de instalar dependencias.

**Android APK** (Windows/Linux/macOS):

```powershell
flet build apk
```

Necesita SDK Android y Java 17 (la CLI puede instalarlos); usa `scripts\construir_android.bat` en Windows. Para instalación usa el `.apk` generado en `build/apk/` según la CLI; instala en un dispositivo o emulador. No afirma que ya exista APK compilado.

**Web estática**: existe `flet build web` / `flet publish`, pero para este proyecto se recomienda **web dinámica** porque las bitácoras emplean SQLite y el benchmark/memoria está definido para el servidor CPython, no el runtime Pyodide del navegador.

## Secuencia demostrativa para exposición

1. En **Estructuras** inserta al inicio y final, observa flechas `prev/next`, elimina un valor y prueba deshacer/rehacer.
2. En **Logística** registra tres paquetes con prioridades 3, 1 y 2; despacha y deshaz.
3. En **Rutas** observa la ruta de cuatro paradas, pulsa «Siguiente» y «Anterior», inicia la animación de una vuelta y verifica la vuelta desde la cola a la cabeza.
4. En **Métricas** muestra ops/s tras unas acciones y compara 2000 inserciones vs 2000 búsquedas.
5. En **Extras** prueba Call Stack y Torres de Hanói. Reduce el ancho del navegador a menos de 720 px para comprobar la **barra inferior móvil**.

## Lista final de comprobación

- [ ] `pytest` pasa sin errores.
- [ ] Escritorio: abrir y probar los 5 apartados.
- [ ] Web: abrir en un navegador, redimensionar y comprobar barra inferior.
- [ ] Simulación: ruta circular recorre un ciclo y permite pausar.
- [ ] Rendimiento: el indicador de operaciones/s decae cuando no hay acciones.
- [ ] Android: compilar APK e instalarlo en emulador/dispositivo.
- [ ] Windows: compilar EXE y probarlo en un equipo de Windows x64.
- [ ] Pública: publicar en hosting WebSocket + HTTPS y verificar la URL real.
