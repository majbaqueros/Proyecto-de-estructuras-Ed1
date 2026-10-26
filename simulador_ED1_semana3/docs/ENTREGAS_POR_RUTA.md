# Entregas al llegar a destino y validación de zonas

Esta versión une **Logística** con **Rutas**: ahora la llegada a la zona dispara una entrega real desde la cola enlazada de prioridad. Se conserva la arquitectura MVC, las animaciones y el modo automático de la Semana 3.

## Cómo ejecutarlo en VS Code (sin Docker)

En VS Code, **abre directamente la carpeta `simulador_ED1_semana3` que contiene `main.py`**. Después, en PowerShell:

```powershell
python -m pip install -r requirements.txt
flet run --web --port 8001 main.py
```

Abre `http://127.0.0.1:8001/`. El entorno que ya tenías configurado con Flet 1.0.4 y FastAPI 0.144.0 también sirve. Para detener el servidor usa `Ctrl + C`.

## Demostración 1: impedir un destino inexistente

1. En **Rutas**, agrega las paradas `La Paz` y `SantaCruz` si todavía no figuran. Las 4 paradas originales se cargan al arrancar el programa.
2. En **Logística**, intenta registrar un paquete para `Tarija` (ejemplo: 2 kg, prioridad Alta).
3. Verás un mensaje de error: ese destino no está registrado en las rutas, así que el paquete no se agrega a la cola.
4. Escribe `la paz` o `SantaCruz`; ahora se acepta porque sí existe una parada. Ignora diferencias de mayúsculas, tildes y espacios sobrantes.

**Importante:** las rutas agregadas manualmente se conservan en la memoria de esa sesión. Si reinicias Flet, debes volver a agregarlas. Se rechazan rutas duplicadas (incluso con distinta capitalización). No se puede quitar una ruta con paquetes pendientes.

## Demostración 2: entrega durante una vuelta completa

1. Registra en **Logística** un paquete para `La Paz`, otro para `Zona Norte` y otro para `SantaCruz`.
2. Ve a **Rutas**. Presiona **▶ Recorrer una vuelta**.
3. El vehículo avanza nodo por nodo. Cuando llega a `Zona Norte`, solo entrega el paquete de `Zona Norte`. Los paquetes de `La Paz` y `SantaCruz` continúan pendientes.
4. Al llegar a `La Paz`, entrega ese paquete; al llegar a `SantaCruz`, entrega el último.
5. Verifica el mensaje de entrega, el contador **Entregados** y que la **Cola de Prioridad** quede vacía.

Los botones **Siguiente** y **Anterior** también pueden entregar al llegar. El botón de **Logística → Entregar en parada actual** solamente entrega cuando hay un paquete para la zona donde está el vehículo.

## Demostración 3: modo automático

En **Logística → Modo de simulación automática**, pulsa **▶ Iniciar simulación**. Cuando no hay paquetes pendientes, el sistema genera dos paquetes con destinos tomados de las paradas reales. En cada ciclo el vehículo avanza una parada; **los paquetes solo se entregan al coincidir con esa parada**. Los otros esperan. El contador de entregas y las métricas se actualizan. Puedes pausar el modo automático antes de realizar un recorrido manual en Rutas.

El mecanismo utiliza `SimuladorAutomatico.paso()` dentro de `logica/simulacion_automatica.py`. El método llama a `AppController.avanzar_y_entregar()`, que a su vez llama a `LogisticEngine.despachar_en_destino()`. La búsqueda por destino se realiza en la **PriorityQueue enlazada**, respetando el orden de prioridad entre paquetes para una misma parada.

## ¿Cómo probarlo desde la terminal?

```powershell
python demo_entregas_por_ruta.py
python demo_simulacion_automatica.py --ciclos 12 --intervalo 0
python -m pytest -q
```

El primer script registra paradas y paquetes, rechaza un destino inexistente y realiza una vuelta mostrando las entregas realizadas. Las pruebas no requieren Flet ni navegador. El script de demostración trabaja en otro proceso: no modifica directamente la sesión de Flet que tengas abierta.

## Archivos modificados

| Archivo | Responsabilidad |
|---|---|
| `controlador/app_controller.py` | Valida el destino contra las rutas; coordina cada llegada y su entrega. |
| `controlador/rutas_controller.py` | Busca rutas reales, mantiene la lista circular y evita eliminar paradas con paquetes pendientes. |
| `estructuras/colas.py` | Añade `desencolar_si()`: extrae el primer paquete compatible respetando el orden de prioridad. |
| `logica/logistic_engine.py` | Hace el despacho por zona, no por simple prioridad global. |
| `logica/simulacion_automatica.py` | Genera lotes de prueba válidos, avanza el vehículo y registra entregas reales. |
| `vistas/vista_rutas.py` | Ejecuta entrega en el recorrido animado, siguiente y anterior; informa entregados. |
| `vistas/vista_logistica.py` | Informa de rutas válidas, rechaza errores y refresca la cola. |
| `logica/destinos.py` | Compara nombres sin importar mayúsculas ni tildes. |
| `tests/test_entregas_por_ruta.py` | Comprueba validación, prioridades, integridad y entregas. |

**Nota:** Esta simulación es académica. Los datos de paquetes de Rutas/Logística son temporales; un futuro sistema real incorporaría persistencia y gestión de vehículos/carga más avanzada.
