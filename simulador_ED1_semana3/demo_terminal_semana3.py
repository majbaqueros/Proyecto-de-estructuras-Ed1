"""Demostraciones para la defensa de ED1, sin abrir la ventana Flet.

Ejecutar desde la carpeta que contiene main.py:
    python demo_terminal_semana3.py

Este archivo no modifica main.py ni las estructuras; usa sus clases reales.
Crea un archivo SQLite independiente: registro_demo_semana3.sqlite.
"""
from pathlib import Path

from controlador.app_controller import AppController
from controlador.estructuras_controller import EstructurasController
from controlador.rutas_controller import RutasController
from estructuras.lista_circular_doble import ListaDoblementeCircular
from database import DatabaseManager
from logica.metricas import ejecutar_benchmark, estimar_memoria_nodos


def titulo(numero, mensaje):
    print(f"\n--- EJEMPLO {numero}: {mensaje} ---")


def main():
    titulo(1, "Registro de paradas y punteros circulares")
    rutas = RutasController()
    for nombre in ("Centro", "Norte", "Este"):
        rutas.agregar_parada(nombre)
        print(f"Registrada parada: {nombre}")
    print("Cantidad:", rutas.cantidad)
    print("Ruta:", " -> ".join(p["nombre"] for p in rutas.estado()))
    print("Punteros correctos:", rutas.verificar_integridad())
    print("Cola.next es cabeza:", rutas._ruta.cola.next is rutas._ruta.cabeza)
    print("Cabeza.prev es cola:", rutas._ruta.cabeza.prev is rutas._ruta.cola)
    assert rutas.verificar_integridad()
    prueba = ListaDoblementeCircular()
    prueba.insertar_final("A")
    prueba.insertar_final("B")
    prueba.cabeza.next.prev = None  # Se rompe deliberadamente SOLO la lista de prueba.
    print("Lista de prueba con puntero roto:", prueba.validar_enlaces())
    assert not prueba.validar_enlaces()

    titulo(2, "Recorrido de un vehiculo, adelante y atras")
    print("Posicion inicial:", rutas.actual)
    for _ in range(3):
        print("Siguiente:", rutas.siguiente())
    print("Anterior:", rutas.anterior())
    print("Eliminar Norte:", rutas.quitar_parada("Norte"))
    print("Ruta restante:", [p["nombre"] for p in rutas.estado()])
    print("Punteros correctos tras eliminar:", rutas.verificar_integridad())
    assert rutas.cantidad == 2 and rutas.verificar_integridad()

    titulo(3, "Validaciones de entrada")
    try:
        rutas.agregar_parada("   ")
    except ValueError as error:
        print("Parada vacia rechazada:", error)
    app = AppController()
    app.crear_paquete("Zona Norte", 3, 3)
    app.crear_paquete("Zona Sur", 2, 1)
    print("Orden de paquetes (prioridad 1 antes que 3):",
          [f"{p.destino} / prioridad {p.prioridad}" for p in app.listar_paquetes()])
    for destino, peso, prioridad in (("", 3, 1), ("Zona Sur", -2, 1), ("Zona Sur", 2, 4), ("Tarija", 2, 1)):
        try:
            app.crear_paquete(destino, peso, prioridad)
        except ValueError as error:
            print(f"Paquete rechazado {destino!r}, {peso}, {prioridad}:", error)
    print("Entregar en Centro (no hay coincidencia):", app.despachar())
    parada, entregados = app.avanzar_y_entregar()
    print("Al llegar a", parada, "se entrega:", [p.destino for p in entregados])
    print("Aun pendiente:", [p.destino for p in app.listar_paquetes()])

    titulo(4, "Registro REAL en SQLite")
    db_path = Path(__file__).with_name("registro_demo_semana3.sqlite")
    db = DatabaseManager(str(db_path))
    estructuras = EstructurasController(db=db)
    estructuras.insertar("Nodo A", "inicio")
    estructuras.insertar("Nodo B", "final")
    estructuras.eliminar("Nodo A")
    print("Lista actual:", estructuras.estado()["elementos"])
    print("Integridad de lista:", estructuras.estado()["integridad"])
    rows = db.conn.execute(
        "SELECT accion, valor FROM historial_lista ORDER BY id DESC LIMIT 3"
    ).fetchall()
    for accion, valor in reversed(rows):
        print(f"Guardado en SQLite: accion={accion}, valor={valor}")
    db.cerrar()
    print("Archivo de base de datos:", db_path.name)
    print("NOTA: las rutas circulares y sus metricas son datos en memoria;"
          " esta bitacora corresponde a la pestaña Estructuras.")

    titulo(5, "Metricas y benchmark")
    r = rutas.monitor.resumen()
    print("Operaciones de rutas registradas:", r["operaciones"])
    print(f"Tasa actual: {r['ops_segundo']:.2f} operaciones/segundo (ventana de 5 segundos)")
    print(f"Ultima duracion: {r['ultima_ms']:.6f} ms")
    memoria = estimar_memoria_nodos(10)["Circular doble"]
    print("Memoria circular doble (estimada, 10 nodos):", memoria)
    benchmark = ejecutar_benchmark(200)
    print(f"Benchmark 200 nodos: insercion total={benchmark.append_ms:.3f} ms; "
          f"200 busquedas de valor ausente={benchmark.buscar_ms:.3f} ms")
    print("Complejidad: insertar al final O(1) por nodo; buscar O(n) por busqueda")
    print("Los tiempos pueden variar segun computadora y ejecucion.")

    print("\nRESULTADO: ejemplos ejecutados sin errores.")


if __name__ == "__main__":
    main()
