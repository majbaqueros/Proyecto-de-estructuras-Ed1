# Modo automático — logística por zona

Esta versión conecta la cola de prioridad de **Logística** con la lista doble circular de **Rutas**. Un paquete **solo puede registrarse** si su destino existe como parada, y **solo se entrega cuando el vehículo llega a esa parada**. El sistema no despacha paquetes de otra zona por su prioridad global.

## Cómo verlo en Flet

En VS Code, abre la carpeta `simulador_ED1_semana3` que contiene `main.py` y ejecuta:

```powershell
python -m pip install -r requirements.txt
flet run --web --port 8001 main.py
```

Abre `http://127.0.0.1:8001/` y visita **Logística → Modo de simulación automática**. Elige el intervalo entre 1, 1,5 o 3 segundos y pulsa **▶ Iniciar simulación**. Puedes cambiar a **Rutas** y ver al vehículo avanzar de parada en parada, con el número total de entregas; en **Métricas** verás el monitor de rendimiento. La simulación automática se puede pausar sin borrar la cola.

## Qué hace `SimuladorAutomatico.paso()`

El método se encuentra en `logica/simulacion_automatica.py`. Cada llamada:

1. Consulta las paradas de `RutasController`.
2. Si la cola está vacía, genera dos paquetes de ejemplo con **destinos válidos**, seleccionados entre las próximas paradas.
3. Solicita `AppController.avanzar_y_entregar()`: avanza un nodo `next` de la lista circular.
4. En esa parada, el controlador busca en `PriorityQueue` únicamente los paquetes destinados a esa zona y los entrega (prioridad 1 antes de 2 antes de 3).
5. Actualiza contadores, historial visual y métricas. Los demás paquetes permanecen pendientes para futuras paradas.

La interfaz llama a este método desde una tarea asíncrona mediante `page.run_task()` y `asyncio.sleep()`. El método no manipula directamente los controles de Flet.

| Etapa | Código implicado |
|---|---|
| Preparar paquetes | `logica/simulacion_automatica.py` → `AppController.crear_paquete()` |
| Validar destino | `RutasController.destino_canonico()` en `controlador/rutas_controller.py` |
| Avanzar vehículo | `AppController.avanzar_y_entregar()` → `RutasController.siguiente()` |
| Buscar paquetes de esa parada | `LogisticEngine.despachar_en_destino()` → `PriorityQueue.desencolar_si()` |
| Actualizar vista | `vistas/vista_logistica.py` y `vistas/vista_rutas.py` |

Para evitar dos recorridos simultáneos, pausa la simulación automática antes de iniciar **Recorrer una vuelta** en Rutas, y viceversa.

## Demostración en la terminal

```powershell
python demo_entregas_por_ruta.py
python demo_simulacion_automatica.py --ciclos 12 --intervalo 0.5
python -m pytest -q
```

Los scripts de terminal usan el mismo código Python pero son procesos independientes: no modifican el estado de la sesión abierta en Chrome. Consulta [ENTREGAS_POR_RUTA.md](ENTREGAS_POR_RUTA.md) para probar destinos no válidos, múltiples entregas en una zona y eliminación de paradas.

**Nota:** los paquetes y rutas agregados por el usuario están en memoria. Si reinicias la aplicación se restauran las paradas predeterminadas y desaparecen los registros creados durante la sesión. No se necesita Docker.
